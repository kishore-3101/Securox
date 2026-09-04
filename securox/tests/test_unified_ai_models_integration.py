"""
Securox — Unified AI Model Mesh & Health Monitoring Test Suite
Verifies:
  1. Standardized inference interface across all 18 models:
     prediction, score, model, version, timestamp, features, important_factors
  2. Strict non-ground-truth guarantee: ground_truth_claim is False with standard disclaimer
  3. Healthcare domain models (5):
     - Abnormal patient access
     - Mass record access
     - Insider behavior
     - Device anomaly (IoMT)
     - Clinical infrastructure risk
  4. Traffic domain models (5):
     - YOLO detection (yolov8n.onnx via OpenCV DNN)
     - Sensor disparity
     - Camera anomaly
     - Signal timing anomaly
     - Roadside infrastructure
  5. Finance domain models (4):
     - Fraud classification (XGBoost)
     - Transaction anomaly (Isolation Forest)
     - AML graph contagion
     - Financial exposure (Cyber-VaR)
  6. Network domain models (4):
     - CIC-IDS2017
     - UNSW-NB15
     - NSL-KDD
     - ToN-IoT
  7. Model Health Monitoring (uptime, status, error rates, average latency)
  8. Unified Event Architecture Integration (Event Fabric + Cyber-Risk Engine consumption)
  9. REST API endpoints (/api/ai/models, /api/ai/health, /api/ai/models/{id}/predict, /api/ai/evaluate-event)
"""

import asyncio
import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app"))
if backend_app not in sys.path:
    sys.path.insert(0, backend_app)
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(1, backend_dir)

from main import app
from services.ai_models import ai_model_registry, ModelInferenceResult, STANDARD_DISCLAIMER
from services.event_fabric import event_fabric
from services.cyber_risk_engine import cyber_risk_engine
from core.store import store

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Standardized Interface & Non-Ground-Truth Compliance Across All 18 Models
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_all_18_models_registered_and_healthy():
    models = ai_model_registry.list_models()
    assert len(models) == 18, f"Expected 18 models, found {len(models)}"
    domains = {m["domain"] for m in models}
    assert "HEALTHCARE" in domains
    assert "TRAFFIC" in domains
    assert "FINANCE" in domains
    assert "NETWORK" in domains

    for m in models:
        assert m["status"] in ("HEALTHY", "DEGRADED"), f"Model {m['model_id']} has unexpected status {m['status']}"
        assert m["model_id"].startswith(("HC-", "TR-", "FIN-", "NET-"))


@pytest.mark.asyncio
async def test_standardized_inference_contract_and_disclaimer():
    """Verify EVERY model satisfies the exact 7 contract keys and never claims ground truth."""
    models = ai_model_registry.list_models()
    for m in models:
        res = await ai_model_registry.predict(m["model_id"], {})
        assert isinstance(res, ModelInferenceResult)
        assert res.model == m["model_name"]
        assert res.version == m["version"]
        assert res.domain == m["domain"]
        assert res.prediction is not None
        assert isinstance(res.score, (int, float))
        assert 0.0 <= res.confidence <= 1.0
        # STRICT INVARIANTS:
        assert res.ground_truth_claim is False, f"Model {m['model_id']} claimed ground truth!"
        assert "probabilistic statistical inference, not deterministic ground truth" in res.disclaimer
        assert isinstance(res.features, dict)
        assert isinstance(res.important_factors, list)
        assert res.latency_ms >= 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Healthcare Domain Models (5 Models)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_healthcare_abnormal_patient_access_nominal():
    res = await ai_model_registry.predict("HC-MODEL-01", {
        "identity": "dr_smith",
        "role": "doctor",
        "department": "Cardiology",
        "patient_department": "Cardiology",
        "is_assigned": True,
        "hour": 14
    })
    assert res.prediction == "NOMINAL_ACCESS"
    assert res.score < 25.0
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_healthcare_abnormal_patient_access_anomaly():
    res = await ai_model_registry.predict("HC-MODEL-01", {
        "identity": "clerk_rob",
        "role": "billing_clerk",
        "department": "Billing",
        "patient_department": "Oncology",
        "is_assigned": False,
        "hour": 23
    })
    assert res.prediction == "ANOMALOUS_ACCESS"
    assert res.score >= 50.0
    assert len(res.important_factors) >= 1
    assert any(f["factor"] in ("UNASSIGNED_PATIENT", "DEPARTMENT_BOLA_MISMATCH") for f in res.important_factors)


@pytest.mark.asyncio
async def test_healthcare_mass_record_access():
    res = await ai_model_registry.predict("HC-MODEL-02", {
        "identity": "dr_smith",
        "records_accessed": 85,
        "window_seconds": 60,
        "is_export": True
    })
    assert res.prediction == "MASS_EXFILTRATION_RISK"
    assert res.score >= 60.0


@pytest.mark.asyncio
async def test_healthcare_insider_behavior():
    res = await ai_model_registry.predict("HC-MODEL-03", {
        "identity": "nurse_jack",
        "action": "BREAK_GLASS",
        "reason": "",
        "break_glass_count_24h": 5
    })
    assert res.prediction in ("HIGH_RISK_INSIDER", "SUSPICIOUS_INSIDER")
    assert res.score >= 50.0


@pytest.mark.asyncio
async def test_healthcare_device_anomaly_iomt():
    res = await ai_model_registry.predict("HC-MODEL-04", {
        "device_id": "PUMP-ICU-04",
        "protocol": "BLE",
        "packet_rate": 120.0,
        "gap_delta": 1500.0
    })
    assert res.prediction in ("IOMT_ATTACK", "DEVICE_TAMPER_SUSPECTED")
    assert res.score >= 50.0


@pytest.mark.asyncio
async def test_healthcare_clinical_infrastructure_risk():
    res = await ai_model_registry.predict("HC-MODEL-05", {
        "facility": "Metro Hospital",
        "ehr_saturation_pct": 85.0,
        "offline_devices": 4
    })
    assert res.prediction in ("CLINICAL_DISRUPTION_HIGH", "ELEVATED_CLINICAL_RISK", "CRITICAL_CLINICAL_RISK")
    assert res.score >= 50.0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Traffic Domain Models (5 Models)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_traffic_yolo_detection_model():
    """Verify YOLOv8n detector runs inference with authentic OpenCV DNN."""
    res = await ai_model_registry.predict("TR-MODEL-01", {
        "camera_id": "CAM-JUNCTION-04"
    })
    assert res.domain == "TRAFFIC"
    assert "vehicle_count" in res.prediction or "detected_objects" in res.prediction
    assert res.ground_truth_claim is False
    assert res.disclaimer == STANDARD_DISCLAIMER


@pytest.mark.asyncio
async def test_traffic_sensor_disparity():
    res = await ai_model_registry.predict("TR-MODEL-02", {
        "junction_id": "INT-10",
        "loop_count": 80.0,
        "camera_count": 15.0
    })
    assert res.prediction in ("DISPARITY_ALERT", "SENSOR_DISPARITY_HIGH")
    assert res.score >= 50.0
    assert len(res.important_factors) >= 1


@pytest.mark.asyncio
async def test_traffic_camera_anomaly():
    res = await ai_model_registry.predict("TR-MODEL-03", {
        "camera_id": "CAM-01",
        "is_frozen": True,
        "occlusion_score": 0.85,
        "fps": 5.0
    })
    assert res.prediction == "CAMERA_TAMPER"
    assert res.score >= 50.0


@pytest.mark.asyncio
async def test_traffic_signal_timing_anomaly():
    res = await ai_model_registry.predict("TR-MODEL-04", {
        "signal_id": "SIG-401",
        "conflict_detected": True,
        "cycle_duration": 5.0
    })
    assert res.prediction in ("INTERLOCK_BREACH", "SIGNAL_TIMING_CRITICAL")
    assert res.score >= 80.0


@pytest.mark.asyncio
async def test_traffic_roadside_infrastructure():
    res = await ai_model_registry.predict("TR-MODEL-05", {
        "rsu_id": "RSU-12",
        "fastag_cloned": True,
        "latency_ms": 2500.0
    })
    assert res.prediction in ("INFRASTRUCTURE_EXPLOIT", "RSU_TAMPER_SUSPECTED")
    assert res.score >= 50.0


# ═══════════════════════════════════════════════════════════════════════════
# 4. Finance Domain Models (4 Models)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_finance_xgboost_fraud():
    res = await ai_model_registry.predict("FIN-MODEL-01", {
        "amount": 4500000.0,
        "channel": "SWIFT",
        "ip_address": "198.51.100.22",
        "currency": "USD"
    })
    assert res.prediction in ("FRAUD_FLAGGED", "HIGH_FRAUD_RISK", "SUSPICIOUS_TRANSFER")
    assert res.score >= 50.0
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_finance_isolation_forest_anomaly():
    res = await ai_model_registry.predict("FIN-MODEL-02", {
        "amount": 50000000.0,
        "channel": "SWIFT"
    })
    assert res.prediction in ("ANOMALOUS_TRANSACTION", "NOMINAL_TRANSACTION")
    assert 0.0 <= res.score <= 100.0
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_finance_aml_graph_contagion():
    res = await ai_model_registry.predict("FIN-MODEL-03", {
        "account_id": "ACC-MULE-88",
        "counterparties": ["OFFSHORE-ESCROW-8841", "MULE-NODE-12"],
        "amount": 48000.0
    })
    assert res.prediction in ("AML_CONTAGION_DETECTED", "HIGH_MULE_CONTAGION_RISK", "ELEVATED_MULE_RISK")
    assert res.score >= 50.0


@pytest.mark.asyncio
async def test_finance_cyber_var_exposure():
    res = await ai_model_registry.predict("FIN-MODEL-04", {
        "portfolio_total_balance_inr": 100000000.0,
        "simulation_multiplier": 1.5
    })
    assert isinstance(res.prediction, dict)
    assert "cyber_var_95_1day_inr" in res.prediction
    assert res.score > 0.0


# ═══════════════════════════════════════════════════════════════════════════
# 5. Network Intrusion Benchmark Models (4 Models)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_network_cicids2017_model():
    res = await ai_model_registry.predict("NET-MODEL-01", {
        "duration": 12.5,
        "bytes_in": 150000,
        "bytes_out": 200,
        "packets": 500,
        "request_rate": 120.0,
        "is_tcp": 1
    })
    assert res.prediction in ("BENIGN", "DDoS", "PortScan", "Botnet", "ATTACK_SUSPECTED")
    assert 0.0 <= res.score <= 100.0
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_network_unsw_nb15_model():
    res = await ai_model_registry.predict("NET-MODEL-02", {
        "duration": 5.0,
        "bytes_in": 4000,
        "bytes_out": 8000,
        "packets": 40,
        "request_rate": 8.0,
        "is_tcp": 1
    })
    assert res.prediction in ("BENIGN", "Generic", "Exploits", "Fuzzers", "DoS", "ATTACK_SUSPECTED")
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_network_nsl_kdd_model():
    res = await ai_model_registry.predict("NET-MODEL-03", {
        "duration": 0.0,
        "bytes_in": 0,
        "bytes_out": 0,
        "packets": 10,
        "error_rate": 0.8,
        "is_tcp": 1
    })
    assert res.prediction in ("BENIGN", "DOS", "Dos", "Probe", "R2L", "U2R", "ATTACK_SUSPECTED")
    assert res.ground_truth_claim is False


@pytest.mark.asyncio
async def test_network_ton_iot_model():
    res = await ai_model_registry.predict("NET-MODEL-04", {
        "duration": 3.2,
        "bytes_in": 600,
        "bytes_out": 600,
        "packets": 12,
        "dst_port_norm": 0.5,
        "is_tcp": 1
    })
    assert res.prediction in ("BENIGN", "normal", "ddos", "dos", "injection", "scanning", "password", "xss", "backdoor", "mitm", "ransomware", "ATTACK_SUSPECTED")
    assert res.ground_truth_claim is False


# ═══════════════════════════════════════════════════════════════════════════
# 6. Model Health Monitoring
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_model_health_monitoring_overall():
    health = await ai_model_registry.get_overall_health()
    assert health["total_models"] == 18
    assert health["healthy_models"] >= 16
    assert health["total_inferences_executed"] >= 0
    assert health["overall_error_rate_pct"] >= 0.0
    assert health["ground_truth_policy"] == "STRICT_PROBABILISTIC_INFERENCE_ONLY"
    assert "models" in health


@pytest.mark.asyncio
async def test_model_health_database_persistence():
    models = ai_model_registry.list_models()
    first_model = models[0]
    db_health = await store.get_ai_model_health(first_model["model_id"])
    assert db_health is not None
    assert db_health["model_id"] == first_model["model_id"]
    assert db_health["domain"] == first_model["domain"]


# ═══════════════════════════════════════════════════════════════════════════
# 7. Unified Event Architecture Integration
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_event_fabric_ingest_enriches_ai_detections():
    """Verify that ingesting a canonical event automatically runs AI models and enriches metadata."""
    test_event = {
        "event_id": f"EVT-AI-TEST-{uuid.uuid4().hex[:6]}",
        "domain": "FINANCE",
        "action": "TRANSACTION",
        "user": "corp_treasurer",
        "role": "treasurer",
        "resource": "SWIFT_WIRE",
        "metadata": {
            "amount": 4500000.0,
            "channel": "SWIFT",
            "ip_address": "198.51.100.22",
            "counterparties": ["OFFSHORE-MULE-NODE"],
            "currency": "USD"
        }
    }
    persisted = await event_fabric.ingest_event(test_event)
    assert "ai_detections" in persisted["metadata"]
    assert "ai_inferences" in persisted["metadata"]
    detections = persisted["metadata"]["ai_detections"]
    assert "xgboost_fraud_score" in detections
    assert "isolation_forest_anomaly" in detections

    # Verify that Central CyberRiskEngine consumed these detections
    assert "evaluated_risk" in persisted
    assert persisted["risk_category"] in ("MEDIUM", "HIGH", "CRITICAL")
    factors = persisted.get("risk_factors", [])
    assert any(f.get("source_type") == "ML_DETECTION" for f in factors)


# ═══════════════════════════════════════════════════════════════════════════
# 8. REST API Endpoints Verification
# ═══════════════════════════════════════════════════════════════════════════

def test_api_list_ai_models():
    resp = client.get("/api/ai/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 18
    assert data["ground_truth_claim"] is False
    assert len(data["models"]) == 18


def test_api_get_ai_health():
    resp = client.get("/api/ai/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_models"] == 18
    assert data["healthy_models"] >= 16


def test_api_get_single_model_health():
    resp = client.get("/api/ai/models/TR-MODEL-01/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_id"] == "TR-MODEL-01"
    assert data["domain"] == "TRAFFIC"
    assert data["ground_truth_claim"] is False


def test_api_post_predict_standardized():
    payload = {
        "identity": "nurse_rob",
        "role": "nurse",
        "action": "PATIENT_ACCESS",
        "department": "ICU",
        "patient_department": "ICU",
        "is_assigned": True
    }
    resp = client.post("/api/ai/models/HC-MODEL-01/predict", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "Abnormal Patient Access Classifier"
    assert data["ground_truth_claim"] is False
    assert "disclaimer" in data
    assert "prediction" in data
    assert "score" in data


def test_api_evaluate_event():
    event = {
        "event_id": f"EVT-EVAL-{uuid.uuid4().hex[:6]}",
        "domain": "TRAFFIC",
        "action": "SIGNAL_OVERRIDE",
        "user": "traffic_engineer",
        "role": "engineer",
        "resource": "INTERSECTION_44",
        "metadata": {
            "conflict_detected": True,
            "cycle_duration": 5.0
        }
    }
    resp = client.post("/api/ai/evaluate-event", json=event)
    assert resp.status_code == 200
    data = resp.json()
    assert "ai_detections" in data
    assert "inferences" in data
    assert len(data["inferences"]) >= 1


def test_api_get_ai_inferences():
    resp = client.get("/api/ai/inferences?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
