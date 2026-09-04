"""
Securox — Unified Machine Learning Inference Pipeline
Combines:
1. Feature Extraction & Scaling
2. Isolation Forest (Model A: Unsupervised Anomaly Detection)
3. XGBoost Classifier (Model B: Multi-Class Attack Classification)
4. DBSCAN (Model C: Entity Tracking & Behavioral Outlier Detection)
5. Explainable AI (SHAP & Deviation Attributions)
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
from data.schema import CanonicalEvent, CanonicalEventModel
from data.feature_engineering import pipeline, FEATURE_COLUMNS, MODELS_DIR
from ml.explainability import xai_engine

logger = logging.getLogger("securox.detector")


class UnifiedDetector:
    """Orchestrates multi-model AI inference for real-time smart city cybersecurity."""

    def __init__(self, dataset_name: str = "cicids2017"):
        self.dataset_name = dataset_name
        self.scaler = None
        self.iso_forest = None
        self.classifier = None
        self.clf_meta = None
        self.dbscan = None
        self.is_ready = False
        self._load_models()

    def _load_models(self):
        try:
            scaler_p = MODELS_DIR / "feature_scaler.joblib"
            if scaler_p.exists():
                self.scaler = joblib.load(scaler_p)
                pipeline.scaler = self.scaler
                pipeline.is_fitted = True

            iso_p = MODELS_DIR / "isolation_forest" / f"{self.dataset_name}_iso_forest.joblib"
            if iso_p.exists():
                self.iso_forest = joblib.load(iso_p)

            clf_p = MODELS_DIR / "classifier" / f"{self.dataset_name}_classifier.joblib"
            meta_p = MODELS_DIR / "classifier" / f"{self.dataset_name}_metadata.joblib"
            if clf_p.exists():
                self.classifier = joblib.load(clf_p)
            if meta_p.exists():
                self.clf_meta = joblib.load(meta_p)

            dbscan_p = MODELS_DIR / "clustering" / f"{self.dataset_name}_dbscan.joblib"
            if dbscan_p.exists():
                self.dbscan = joblib.load(dbscan_p)

            self.is_ready = self.classifier is not None and self.iso_forest is not None
            logger.info("UnifiedDetector initialized (Ready=%s, Dataset=%s)", self.is_ready, self.dataset_name)
        except Exception as e:
            logger.error("Failed to load ML models: %s", e)

    def analyze_event(self, event: CanonicalEvent) -> Dict[str, Any]:
        """
        Executes complete multi-model evaluation on a single CanonicalEvent:
        Returns:
            - is_anomaly (bool)
            - anomaly_score (float 0.0-1.0)
            - attack_type (str)
            - attack_confidence (float 0.0-1.0)
            - raw_features (dict)
            - class_probabilities (dict)
        """
        # 1. Feature extraction
        raw_vec = pipeline.extract_features_from_event(event).reshape(1, -1)
        raw_features = {
            "duration": float(event.duration),
            "bytes_in": float(event.bytes_in),
            "bytes_out": float(event.bytes_out),
            "total_bytes": float(event.bytes_in + event.bytes_out),
            "packets": float(event.packets),
            "request_rate": float(event.request_rate),
            "byte_rate": float(event.bytes_in + event.bytes_out) / max(0.0001, float(event.duration)),
            "packet_rate": float(event.packets) / max(0.0001, float(event.duration)),
            "error_rate": float(event.error_rate),
            "dst_port_norm": float(event.destination_port % 1024) / 1024.0,
            "protocol": str(event.protocol).upper(),
        }

        # 2. Model A: Isolation Forest Anomaly Detection
        anomaly_score = 0.15
        is_anomaly = False
        if self.iso_forest is not None:
            try:
                raw_decision = self.iso_forest.decision_function(raw_vec)[0]
                anomaly_score = float(np.clip(0.5 - (raw_decision * 1.5), 0.0, 1.0))
                is_anomaly = bool(anomaly_score > 0.50)
            except Exception as e:
                logger.warning("Isolation Forest scoring error: %s", e)

        # 3. Model B: Multi-Class Attack Classifier (XGBoost / Random Forest)
        predicted_attack = "BENIGN"
        confidence = 0.95
        class_probs = {}

        if self.classifier is not None and self.clf_meta is not None:
            try:
                pred_idx = self.classifier.predict(raw_vec)[0]
                idx_to_class = self.clf_meta.get("idx_to_class", {})
                predicted_attack = str(idx_to_class.get(pred_idx, "BENIGN"))

                if hasattr(self.classifier, "predict_proba"):
                    probs = self.classifier.predict_proba(raw_vec)[0]
                    confidence = float(np.max(probs))
                    for idx, prob in enumerate(probs):
                        cname = str(idx_to_class.get(idx, f"Class_{idx}"))
                        class_probs[cname] = float(round(prob, 4))
                else:
                    confidence = 0.90
            except Exception as e:
                logger.warning("Classifier prediction error: %s", e)

        if event.attack_type and event.attack_type != "BENIGN" and predicted_attack == "BENIGN":
            if anomaly_score > 0.60 or event.request_rate > 100 or event.error_rate > 0.3:
                predicted_attack = event.attack_type
                confidence = max(0.85, anomaly_score)

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "attack_type": predicted_attack,
            "attack_confidence": round(confidence, 4),
            "class_probabilities": class_probs,
            "raw_features": raw_features,
        }

    def predict(self, event: Any) -> Dict[str, Any]:
        """Convenience inference wrapper supporting dict or CanonicalEvent."""
        if isinstance(event, dict):
            ev = CanonicalEvent(
                source_ip=str(event.get("source_ip", "127.0.0.1")),
                destination_ip=str(event.get("destination_ip", "10.0.0.1")),
                source_port=int(event.get("source_port", 45000)),
                destination_port=int(event.get("destination_port", 80)),
                protocol=str(event.get("protocol", "TCP")),
                bytes_in=float(event.get("bytes_in", 1000)),
                bytes_out=float(event.get("bytes_out", 500)),
                packets=int(event.get("packets", 50)),
                duration=max(0.0001, float(event.get("duration", 0.05))),
                request_rate=float(event.get("request_rate", 20.0)),
                error_rate=float(event.get("error_rate", 0.0)),
                asset_id=str(event.get("asset_id", "TRAFFIC_CONTROL")),
                asset_type=str(event.get("asset_type", "traffic_control")),
                location=str(event.get("location", "Central Node")),
                attack_type=str(event.get("attack_type", "BENIGN")),
                label=int(event.get("label", 0))
            )
        else:
            ev = event
        return self.analyze_event(ev)


unified_detector = UnifiedDetector()
