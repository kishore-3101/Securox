"""
Securox — Network Domain AI Models
4 Benchmark Intrusion Detection Models:
  15. CICIDS2017Model
  16. UNSWNB15Model
  17. NSLKDDModel
  18. ToNIoTModel
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import joblib

from services.ai_models.base import BaseAIModel, ModelInferenceResult, _utcnow

MODELS_DIR = Path("c:/Users/praja/Downloads/Securox-main (1)/Securox-main/securox/models")
FEATURE_NAMES = ["duration", "bytes_in", "bytes_out", "total_bytes", "packets", "request_rate", "byte_rate", "packet_rate", "error_rate", "dst_port_norm", "is_tcp", "is_udp"]


class _BaseBenchmarkIntrusionModel(BaseAIModel):
    """Shared loader and inference executor for serialized joblib benchmark models."""

    def __init__(self, model_id: str, model_name: str, dataset_key: str):
        super().__init__(model_id, model_name, "NETWORK", "2.0.0")
        self.dataset_key = dataset_key
        self.scaler = None
        self.classifier = None
        self.clf_meta = None
        self.iso_forest = None
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            scaler_p = MODELS_DIR / "feature_scaler.joblib"
            if scaler_p.exists():
                self.scaler = joblib.load(scaler_p)

            clf_p = MODELS_DIR / "classifier" / f"{self.dataset_key}_classifier.joblib"
            meta_p = MODELS_DIR / "classifier" / f"{self.dataset_key}_metadata.joblib"
            if clf_p.exists():
                self.classifier = joblib.load(clf_p)
            if meta_p.exists():
                self.clf_meta = joblib.load(meta_p)

            iso_p = MODELS_DIR / "isolation_forest" / f"{self.dataset_key}_iso_forest.joblib"
            if iso_p.exists():
                self.iso_forest = joblib.load(iso_p)

            self.status = "HEALTHY" if self.classifier is not None else "DEGRADED"
        except Exception as e:
            self.status = "DEGRADED"

    def _extract_vector(self, inputs: Dict[str, Any]) -> np.ndarray:
        dur = max(0.0001, float(inputs.get("duration", 0.05)))
        b_in = float(inputs.get("bytes_in", 200.0))
        b_out = float(inputs.get("bytes_out", 100.0))
        tot_b = b_in + b_out
        pkts = max(1.0, float(inputs.get("packets", 10.0)))
        req_rate = float(inputs.get("request_rate", pkts / dur))
        byte_rate = tot_b / dur
        pkt_rate = pkts / dur
        err_rate = float(inputs.get("error_rate", 0.0))
        dst_port = int(inputs.get("dst_port", inputs.get("destination_port", 80)))
        dst_port_norm = float(dst_port % 1024) / 1024.0
        proto = str(inputs.get("protocol", "TCP")).upper()

        vec = np.array([[
            dur, b_in, b_out, tot_b, pkts,
            min(50000.0, req_rate), min(1e8, byte_rate), min(1e6, pkt_rate),
            err_rate, dst_port_norm,
            1.0 if "TCP" in proto else 0.0,
            1.0 if "UDP" in proto else 0.0
        ]], dtype=np.float32)

        if self.scaler is not None:
            try:
                return self.scaler.transform(vec)
            except Exception:
                return vec
        return vec

    async def _predict_internal(self, inputs: Dict[str, Any]) -> ModelInferenceResult:
        vec = self._extract_vector(inputs)
        attack_type = "BENIGN"
        confidence = 0.95
        anomaly_score = 15.0

        if self.classifier is not None and self.clf_meta is not None:
            probs = self.classifier.predict_proba(vec)[0]
            top_idx = int(np.argmax(probs))
            classes = self.clf_meta.get("classes", [])
            if top_idx < len(classes):
                attack_type = str(classes[top_idx])
            confidence = float(probs[top_idx])

        if self.iso_forest is not None:
            raw_iso = self.iso_forest.decision_function(vec)[0]
            anomaly_score = float(np.clip((0.5 - raw_iso) * 100.0, 0.0, 100.0))

        is_attack = attack_type != "BENIGN"
        composite_score = round(max(anomaly_score, confidence * 100.0 if is_attack else 5.0), 1)

        factors = []
        if is_attack:
            factors.append({
                "factor": f"{self.dataset_key.upper()}_SIGNATURE_MATCH",
                "attack_type": attack_type,
                "confidence": round(confidence, 2),
                "points": composite_score,
                "description": f"Classified as {attack_type} with P={confidence:.2f} using {self.dataset_key.upper()} trained ensemble"
            })

        return ModelInferenceResult(
            model=self.model_name,
            version=self.version,
            domain=self.domain,
            prediction=attack_type,
            score=composite_score,
            confidence=round(confidence, 2),
            features={k: float(vec[0][i]) for i, k in enumerate(FEATURE_NAMES)},
            important_factors=factors or [{"factor": "NOMINAL_NETWORK_FLOW", "points": 0.0, "description": "Flow characteristics match normal baseline"}],
            model_attribution="LIVE INFERENCE"
        )

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "model_id": self.model_id,
            "dataset": self.dataset_key,
            "classifier_loaded": self.classifier is not None,
            "isolation_forest_loaded": self.iso_forest is not None,
            "scaler_loaded": self.scaler is not None
        }


class CICIDS2017Model(_BaseBenchmarkIntrusionModel):
    def __init__(self):
        super().__init__("NET-MODEL-01", "CIC-IDS2017 Network Intrusion Classifier", "cicids2017")


class UNSWNB15Model(_BaseBenchmarkIntrusionModel):
    def __init__(self):
        super().__init__("NET-MODEL-02", "UNSW-NB15 Network Intrusion Classifier", "unsw_nb15")


class NSLKDDModel(_BaseBenchmarkIntrusionModel):
    def __init__(self):
        super().__init__("NET-MODEL-03", "NSL-KDD Network Intrusion Classifier", "nsl_kdd")


class ToNIoTModel(_BaseBenchmarkIntrusionModel):
    def __init__(self):
        super().__init__("NET-MODEL-04", "ToN-IoT SCADA & IoT Intrusion Classifier", "ton_iot")
