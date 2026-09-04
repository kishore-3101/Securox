"""
Securox — AI Model Registry & Health Monitoring Subsystem
Manages lifecycle, automated health verification, latency tracking,
and event routing across all 18 specialized models.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from core.store import store
from services.ai_models.base import BaseAIModel, ModelInferenceResult
from services.ai_models.healthcare_models import (
    AbnormalPatientAccessModel, MassRecordAccessModel, HealthcareInsiderBehaviorModel,
    IoMTDeviceAnomalyModel, ClinicalInfrastructureRiskModel
)
from services.ai_models.traffic_models import (
    YOLOVehicleDetectionModel, SensorDisparityModel, CameraAnomalyModel,
    SignalTimingAnomalyModel, RoadsideInfrastructureModel
)
from services.ai_models.finance_models import (
    XGBoostFraudClassificationModel, IsolationForestTransactionAnomalyModel,
    AMLGraphContagionModel, CyberVaRExposureModel
)
from services.ai_models.network_models import (
    CICIDS2017Model, UNSWNB15Model, NSLKDDModel, ToNIoTModel
)

logger = logging.getLogger("securox.ai_registry")


class AIModelRegistry:
    """
    Central registry and health monitor for all 18 Securox AI models.
    """

    def __init__(self):
        self._models: Dict[str, BaseAIModel] = {}
        self._register_all_models()

    def _register_all_models(self):
        all_instances: List[BaseAIModel] = [
            # Healthcare (5)
            AbnormalPatientAccessModel(),
            MassRecordAccessModel(),
            HealthcareInsiderBehaviorModel(),
            IoMTDeviceAnomalyModel(),
            ClinicalInfrastructureRiskModel(),
            # Traffic (5)
            YOLOVehicleDetectionModel(),
            SensorDisparityModel(),
            CameraAnomalyModel(),
            SignalTimingAnomalyModel(),
            RoadsideInfrastructureModel(),
            # Finance (4)
            XGBoostFraudClassificationModel(),
            IsolationForestTransactionAnomalyModel(),
            AMLGraphContagionModel(),
            CyberVaRExposureModel(),
            # Network (4)
            CICIDS2017Model(),
            UNSWNB15Model(),
            NSLKDDModel(),
            ToNIoTModel(),
        ]
        for m in all_instances:
            self._models[m.model_id] = m
            # Also register by lowercase slug
            slug = m.model_name.lower().replace(" ", "_").replace("-", "_")
            self._models[slug] = m

        logger.info("AIModelRegistry initialized with %d models.", len(all_instances))

    def get_model(self, model_identifier: str) -> Optional[BaseAIModel]:
        return self._models.get(model_identifier) or self._models.get(model_identifier.upper())

    def list_models(self) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for m in self._models.values():
            if m.model_id in seen:
                continue
            seen.add(m.model_id)
            avg_lat = round(m.total_latency_ms / max(1, m.total_inferences), 2)
            out.append({
                "model_id": m.model_id,
                "model_name": m.model_name,
                "domain": m.domain,
                "version": m.version,
                "status": m.status,
                "total_inferences": m.total_inferences,
                "total_errors": m.total_errors,
                "avg_latency_ms": avg_lat
            })
        return out

    async def predict(self, model_identifier: str, inputs: Dict[str, Any], event_id: Optional[str] = None) -> ModelInferenceResult:
        model = self.get_model(model_identifier)
        if not model:
            return ModelInferenceResult(
                model=model_identifier,
                version="0.0.0",
                domain="UNKNOWN",
                prediction="MODEL_NOT_FOUND",
                score=0.0,
                confidence=0.0,
                features={"error": f"Model '{model_identifier}' is not registered in AIModelRegistry"},
                ground_truth_claim=False
            )

        res = await model.predict(inputs)

        # Update database storage
        try:
            await store.save_ai_model_inference({
                "model_name": res.model,
                "version": res.version,
                "domain": res.domain,
                "event_id": event_id,
                "prediction": res.prediction,
                "score": res.score,
                "confidence": res.confidence,
                "ground_truth_claim": False,
                "features": res.features,
                "important_factors": res.important_factors,
                "latency_ms": res.latency_ms,
                "disclaimer": res.disclaimer,
                "timestamp": res.timestamp
            })
            await store.update_ai_model_health(
                model_id=model.model_id,
                model_name=model.model_name,
                domain=model.domain,
                version=model.version,
                status=model.status,
                latency_ms=res.latency_ms,
                is_error=res.prediction == "ERROR_FALLBACK"
            )
        except Exception as e:
            logger.debug("Database AI inference tracking error: %s", e)

        return res

    async def get_health_summary(self) -> Dict[str, Any]:
        models = self.list_models()
        total_inf = sum(m["total_inferences"] for m in models)
        total_err = sum(m["total_errors"] for m in models)
        healthy_count = sum(1 for m in models if m["status"] == "HEALTHY")
        degraded_count = sum(1 for m in models if m["status"] == "DEGRADED")
        offline_count = sum(1 for m in models if m["status"] == "OFFLINE")

        all_latencies = [m["avg_latency_ms"] for m in models if m["avg_latency_ms"] > 0]
        mean_lat = round(sum(all_latencies) / max(1, len(all_latencies)), 2)

        return {
            "total_models": len(models),
            "healthy_models": healthy_count,
            "degraded_models": degraded_count,
            "offline_models": offline_count,
            "total_inferences_executed": total_inf,
            "total_errors_recorded": total_err,
            "overall_error_rate_pct": round((total_err / max(1, total_inf)) * 100.0, 2),
            "mean_inference_latency_ms": mean_lat,
            "models": models,
            "ground_truth_policy": "STRICT_PROBABILISTIC_INFERENCE_ONLY",
            "system_health": "OPTIMAL" if degraded_count == 0 and offline_count == 0 else "OPERATIONAL_WITH_WARNINGS"
        }

    async def get_overall_health(self) -> Dict[str, Any]:
        """Alias for get_health_summary."""
        return await self.get_health_summary()

    async def evaluate_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes an incoming canonical event from the Central Event Fabric
        to appropriate domain AI models and produces standardized inferences.
        """
        domain = str(event.get("domain", "SECURITY")).upper()
        action = str(event.get("action", "")).upper()
        meta = event.get("metadata", {}) or {}

        ai_detections = {}
        inferences = []

        if domain == "HEALTHCARE" or action in ("PATIENT_ACCESS", "MEDICAL_RECORD_UPDATE", "BREAK_GLASS", "AMBULANCE_ASSIGNMENT"):
            m1 = await self.predict("HC-MODEL-01", {**event, **meta}, event_id=event.get("event_id"))
            m2 = await self.predict("HC-MODEL-02", {**event, **meta}, event_id=event.get("event_id"))
            m3 = await self.predict("HC-MODEL-03", {**event, **meta}, event_id=event.get("event_id"))
            inferences.extend([m1, m2, m3])
            ai_detections["healthcare_access_score"] = m1.score
            ai_detections["mass_access_anomaly"] = m2.score >= 50.0
            ai_detections["insider_threat_score"] = m3.score

        elif domain == "TRAFFIC" or action in ("SIGNAL_OVERRIDE", "CAMERA_ACCESS", "CAMERA_FAILURE"):
            m_disparity = await self.predict("TR-MODEL-02", {**event, **meta}, event_id=event.get("event_id"))
            m_cam = await self.predict("TR-MODEL-03", {**event, **meta}, event_id=event.get("event_id"))
            m_sig = await self.predict("TR-MODEL-04", {**event, **meta}, event_id=event.get("event_id"))
            inferences.extend([m_disparity, m_cam, m_sig])
            ai_detections["sensor_disparity_score"] = m_disparity.score
            ai_detections["camera_tamper_flag"] = m_cam.prediction == "CAMERA_TAMPER"
            ai_detections["signal_conflict_score"] = m_sig.score

        elif domain == "FINANCE" or action in ("TRANSACTION", "FRAUD_ALERT", "AML_ALERT"):
            m_xgb = await self.predict("FIN-MODEL-01", {**event, **meta}, event_id=event.get("event_id"))
            m_if = await self.predict("FIN-MODEL-02", {**event, **meta}, event_id=event.get("event_id"))
            m_aml = await self.predict("FIN-MODEL-03", {**event, **meta}, event_id=event.get("event_id"))
            inferences.extend([m_xgb, m_if, m_aml])
            ai_detections["xgboost_fraud_score"] = m_xgb.score
            ai_detections["isolation_forest_anomaly"] = m_if.score / 100.0
            ai_detections["aml_mule_risk"] = m_aml.score / 100.0

        # Run benchmark network intrusion models for network and security events
        if domain in ("SECURITY", "PLATFORM") or action in ("LOGIN", "ACCESS_DENIED", "DEVICE_REGISTERED"):
            m_cic = await self.predict("NET-MODEL-01", {**event, **meta}, event_id=event.get("event_id"))
            m_ton = await self.predict("NET-MODEL-04", {**event, **meta}, event_id=event.get("event_id"))
            inferences.extend([m_cic, m_ton])
            ai_detections["cicids_attack_type"] = m_cic.prediction
            ai_detections["network_anomaly_score"] = m_cic.score
            ai_detections["ton_iot_attack_type"] = m_ton.prediction

        return {
            "ai_detections": ai_detections,
            "inferences": [inf.model_dump() for inf in inferences]
        }


ai_model_registry = AIModelRegistry()
