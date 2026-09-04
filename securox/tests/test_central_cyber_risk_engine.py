"""
Securox Central Cyber-Risk Engine — Comprehensive Verification Suite
Tests:
  1. Exact user example:
     Risk 91
     +20 new device
     +18 unusual location
     +15 unusual time
     +25 abnormal volume
     +13 sensitive resource
  2. Input contract validation across all 11 dimensions:
     identity, role, resource, action, device, location, time, behavior, domain, historical baseline, AI detections
  3. Strict 4-tier risk classification: LOW, MEDIUM, HIGH, CRITICAL
  4. Determinism: Zero random numbers, same input evaluated N times yields identical scores and factors
  5. Distinction between Policy Rules, Statistical Baselines, and ML Detections
  6. Uncertainty quantification: Never hide uncertainty, explicit diagnostic root causes
  7. Event Fabric integration: Consuming events automatically creates persisted RiskAssessment & RiskFactors
  8. REST API endpoints:
     - POST /api/risk/assess
     - GET /api/risk/assessments
     - GET /api/risk/assessments/{assessment_id}
     - GET /api/risk/baselines/{identity}
     - POST /api/risk/baselines/{identity}/reset
     - GET /api/risk/stats
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
from auth.jwt_auth import create_access_token
from services.cyber_risk_engine import (
    cyber_risk_engine, RiskEvent, RiskAssessment, RiskFactor, HistoricalBaseline
)
from services.event_fabric import event_fabric
from core.store import store

client = TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "username": "admin", "role": "admin"})


@pytest.fixture
def fraud_analyst_token():
    return create_access_token({"sub": "fraud_analyst", "username": "fraud_analyst", "role": "fraud_analyst"})


# ═══════════════════════════════════════════════════════════════════════════
# 1. EXACT USER EXAMPLE TEST
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_exact_user_example_91_critical():
    """
    Verifies the user's exact specification:
    Risk 91
    +20 new device
    +18 unusual location
    +15 unusual time
    +25 abnormal volume
    +13 sensitive resource
    Sum: 20 + 18 + 15 + 25 + 13 = 91.0 (CRITICAL, BLOCK_ACTION)
    """
    event = RiskEvent(
        identity="rogue_actor",
        role="teller",
        resource="SETTLEMENT_VAULT",
        action="TRANSACTION",
        device="DEV-UNKNOWN-99",
        location="OFFSHORE-ANONYMOUS",
        time="03:15:00Z",
        behavior={
            "is_new_device": True,
            "is_unusual_location": True,
            "is_unusual_time": True,
            "is_abnormal_volume": True,
            "volume_z_score": 3.8
        },
        domain="FINANCE",
        historical_baseline={
            "identity": "rogue_actor",
            "known_devices": ["DEV-TELLER-01"],
            "known_locations": ["State Apex Municipal Bank"],
            "typical_hours": [9, 17],
            "mean_volume": 10.0,
            "std_dev_volume": 2.0,
            "event_count": 25
        }
    )

    assessment = await cyber_risk_engine.evaluate(event)

    assert assessment.risk_score == 91.0
    assert assessment.risk_category == "CRITICAL"
    assert assessment.recommended_action == "BLOCK_ACTION"

    factor_dict = {f.name: f.points for f in assessment.factors}
    assert factor_dict.get("new device") == 20.0
    assert factor_dict.get("unusual location") == 18.0
    assert factor_dict.get("unusual time") == 15.0
    assert factor_dict.get("abnormal volume") == 25.0
    assert factor_dict.get("sensitive resource") == 13.0

    explanation = assessment.explanation
    assert "Risk 91 (CRITICAL)" in explanation
    assert "+20 new device" in explanation
    assert "+18 unusual location" in explanation
    assert "+15 unusual time" in explanation
    assert "+25 abnormal volume" in explanation
    assert "+13 sensitive resource" in explanation


# ═══════════════════════════════════════════════════════════════════════════
# 2. INPUT CONTRACT VALIDATION (11 DIMENSIONS)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_input_contract_11_dimensions():
    """
    Verifies that all 11 required input dimensions are accepted and evaluated.
    """
    event = RiskEvent(
        identity="dr_smith",
        role="doctor",
        resource="PATIENT:P-1004:EHR_MASTER",
        action="BREAK_GLASS",
        device="CLINICAL-TABLET-03",
        location="Emergency Trauma Bay 1",
        time="2026-09-05T14:30:00Z",
        behavior={"request_rate": 1.2, "failed_prior_attempts": 0},
        domain="HEALTHCARE",
        historical_baseline={
            "identity": "dr_smith",
            "domain": "HEALTHCARE",
            "role": "doctor",
            "known_devices": ["CLINICAL-TABLET-03"],
            "known_locations": ["Emergency Trauma Bay 1"],
            "typical_hours": [6, 22],
            "typical_actions": ["PATIENT_ACCESS", "BREAK_GLASS"],
            "mean_volume": 5.0,
            "std_dev_volume": 1.5,
            "event_count": 40
        },
        ai_detections={
            "xgboost_fraud_probability": 0.02,
            "isolation_forest_anomaly_score": 0.05
        }
    )

    assessment = await cyber_risk_engine.evaluate(event)
    assert assessment.identity == "dr_smith"
    assert assessment.domain == "HEALTHCARE"
    assert assessment.action == "BREAK_GLASS"
    assert assessment.resource == "PATIENT:P-1004:EHR_MASTER"
    assert assessment.risk_score >= 0.0
    assert assessment.confidence >= 0.80
    assert assessment.uncertainty <= 0.20


# ═══════════════════════════════════════════════════════════════════════════
# 3. 4-TIER RISK CLASSIFICATION (LOW, MEDIUM, HIGH, CRITICAL)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_all_four_risk_tiers():
    """Verifies that LOW, MEDIUM, HIGH, CRITICAL are produced based on deterministic thresholds."""
    # Tier 1: LOW (< 30.0) -> ALLOW
    low_event = RiskEvent(
        identity="operator_01",
        role="traffic_operator",
        resource="SCADA:ROAD_SEGMENT:RS-01",
        action="LOGIN",
        device="SCADA-WS-01",
        location="Traffic Control HQ",
        time="10:00:00Z",
        domain="TRAFFIC",
        historical_baseline={
            "identity": "operator_01",
            "known_devices": ["SCADA-WS-01"],
            "known_locations": ["Traffic Control HQ"],
            "typical_hours": [8, 18],
            "event_count": 50
        }
    )
    low_res = await cyber_risk_engine.evaluate(low_event)
    assert low_res.risk_category == "LOW"
    assert low_res.risk_score < 30.0
    assert low_res.recommended_action == "ALLOW"

    # Tier 2: MEDIUM (30.0 to 59.9) -> MONITOR / STEP_UP_AUTH
    med_event = RiskEvent(
        identity="operator_01",
        role="traffic_operator",
        resource="SCADA:SIGNAL:SIG-01",
        action="SIGNAL_OVERRIDE",
        device="DEV-NEW-LAPTOP",
        location="Traffic Control HQ",
        time="11:00:00Z",
        domain="TRAFFIC",
        behavior={"is_new_device": True},
        historical_baseline={
            "identity": "operator_01",
            "known_devices": ["SCADA-WS-01"],
            "known_locations": ["Traffic Control HQ"],
            "event_count": 50
        }
    )
    med_res = await cyber_risk_engine.evaluate(med_event)
    assert med_res.risk_category == "MEDIUM"
    assert 30.0 <= med_res.risk_score < 60.0
    assert med_res.recommended_action in ("STEP_UP_AUTH", "MONITOR")

    # Tier 3: HIGH (60.0 to 79.9) -> CHALLENGE_MFA / STEP_UP_AUTH
    high_event = RiskEvent(
        identity="operator_01",
        role="traffic_operator",
        resource="SCADA:GRID_MASTER",
        action="SIGNAL_OVERRIDE",
        device="DEV-NEW-LAPTOP",
        location="REMOTE-CAFE-WIFI",
        time="11:00:00Z",
        domain="TRAFFIC",
        behavior={"is_new_device": True, "is_unusual_location": True},
        historical_baseline={
            "identity": "operator_01",
            "known_devices": ["SCADA-WS-01"],
            "known_locations": ["Traffic Control HQ"],
            "event_count": 50
        }
    )
    high_res = await cyber_risk_engine.evaluate(high_event)
    assert high_res.risk_category == "HIGH"
    assert 60.0 <= high_res.risk_score < 80.0
    assert high_res.recommended_action in ("CHALLENGE_MFA", "STEP_UP_AUTH")

    # Tier 4: CRITICAL (>= 80.0) -> BLOCK_ACTION
    crit_event = RiskEvent(
        identity="operator_01",
        role="traffic_operator",
        resource="SCADA:GRID_MASTER",
        action="ACCESS_DENIED",
        device="DEV-NEW-LAPTOP",
        location="OFFSHORE-ANONYMOUS",
        time="03:00:00Z",
        behavior={"is_new_device": True, "is_unusual_location": True, "is_unusual_time": True},
        domain="TRAFFIC",
        ai_detections={"isolation_forest_anomaly_score": 0.85},
        historical_baseline={
            "identity": "operator_01",
            "known_devices": ["SCADA-WS-01"],
            "known_locations": ["Traffic Control HQ"],
            "event_count": 50
        }
    )
    crit_res = await cyber_risk_engine.evaluate(crit_event)
    assert crit_res.risk_category == "CRITICAL"
    assert crit_res.risk_score >= 80.0
    assert crit_res.recommended_action == "BLOCK_ACTION"


# ═══════════════════════════════════════════════════════════════════════════
# 4. DETERMINISM (ZERO RANDOM SCORES)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_strict_determinism_20_iterations():
    """
    Verifies that running the same input 20 times produces 100% identical outputs.
    """
    event = RiskEvent(
        identity="finance_teller_02",
        role="teller",
        resource="TREASURY:SETTLEMENT_VAULT",
        action="TRANSACTION",
        device="BRANCH-WS-99",
        location="Unknown VPN",
        time="23:30:00Z",
        behavior={"is_new_device": True, "is_unusual_time": True},
        domain="FINANCE",
        historical_baseline={
            "identity": "finance_teller_02",
            "known_devices": ["BRANCH-WS-01"],
            "known_locations": ["Branch Downtown"],
            "typical_hours": [9, 17],
            "event_count": 15
        }
    )

    baseline_run = await cyber_risk_engine.evaluate(event)

    for i in range(20):
        run = await cyber_risk_engine.evaluate(event)
        assert run.risk_score == baseline_run.risk_score, f"Iteration {i} score drifted"
        assert run.risk_category == baseline_run.risk_category
        assert run.confidence == baseline_run.confidence
        assert run.uncertainty == baseline_run.uncertainty
        assert run.recommended_action == baseline_run.recommended_action
        assert len(run.factors) == len(baseline_run.factors)
        for f1, f2 in zip(run.factors, baseline_run.factors):
            assert f1.factor_key == f2.factor_key
            assert f1.points == f2.points
            assert f1.source_type == f2.source_type


# ═══════════════════════════════════════════════════════════════════════════
# 5. DISTINCTION BETWEEN POLICY RULES VS BASELINES VS ML DETECTIONS
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_policy_vs_baseline_vs_ml_separation():
    """
    Verifies auditable separation between POLICY_RULE, STATISTICAL_BASELINE, ML_DETECTION.
    """
    event = RiskEvent(
        identity="auditor_user",
        role="auditor",
        resource="TREASURY:SWIFT_GATEWAY",
        action="TRANSACTION",
        device="DEV-NEW",
        location="Branch North",
        time="14:00:00Z",
        behavior={"is_new_device": True, "is_abnormal_volume": True},
        domain="FINANCE",
        ai_detections={
            "xgboost_fraud_probability": 0.88,
            "aml_mule_probability": 0.75
        },
        historical_baseline={
            "identity": "auditor_user",
            "known_devices": ["AUDIT-WS-01"],
            "known_locations": ["Branch North"],
            "event_count": 30
        }
    )

    assessment = await cyber_risk_engine.evaluate(event)

    assert assessment.rule_score > 0.0
    assert assessment.baseline_score > 0.0
    assert assessment.ml_score > 0.0

    for factor in assessment.factors:
        assert factor.source_type in ("POLICY_RULE", "STATISTICAL_BASELINE", "ML_DETECTION")
        if factor.source_type == "POLICY_RULE":
            assert factor.factor_key in ("NEW_DEVICE", "SENSITIVE_RESOURCE", "HIGH_CONSEQUENCE_ACTION", "ROLE_MISMATCH", "UNUSUAL_LOCATION", "UNUSUAL_TIME", "UNTRUSTED_DEVICE", "ACCESS_DENIED_EVENT")
        elif factor.source_type == "STATISTICAL_BASELINE":
            assert factor.factor_key in ("ABNORMAL_VOLUME", "OFF_PEAK_SPIKE")
        elif factor.source_type == "ML_DETECTION":
            assert factor.factor_key in ("ML_FRAUD_HIGH", "ML_FRAUD_MODERATE", "ML_ANOMALY_DETECTION", "ML_AML_CONTAGION")


# ═══════════════════════════════════════════════════════════════════════════
# 6. UNCERTAINTY QUANTIFICATION (NEVER HIDE UNCERTAINTY)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_uncertainty_quantification_sparse_vs_robust():
    """
    Verifies that sparse historical baselines result in higher uncertainty,
    and ambiguous model probabilities (P ~ 0.50) explicitly declare entropy.
    """
    sparse_event = RiskEvent(
        identity="brand_new_employee",
        role="teller",
        resource="BRANCH_CASH",
        action="LOGIN",
        device="DEV-01",
        location="Branch 1",
        historical_baseline={"event_count": 1, "known_devices": ["DEV-01"], "known_locations": ["Branch 1"]}
    )
    sparse_res = await cyber_risk_engine.evaluate(sparse_event)
    assert sparse_res.uncertainty >= 0.25
    assert "Sparse entity baseline" in sparse_res.uncertainty_reason

    boundary_event = RiskEvent(
        identity="established_teller",
        role="teller",
        resource="BRANCH_CASH",
        action="TRANSACTION",
        device="DEV-01",
        location="Branch 1",
        ai_detections={"xgboost_fraud_probability": 0.51},
        historical_baseline={"event_count": 100, "known_devices": ["DEV-01"], "known_locations": ["Branch 1"]}
    )
    boundary_res = await cyber_risk_engine.evaluate(boundary_event)
    assert "Elevated model entropy near classification threshold" in boundary_res.uncertainty_reason


# ═══════════════════════════════════════════════════════════════════════════
# 7. EVENT FABRIC INGESTION INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_event_fabric_consumption_creates_assessment():
    """
    Verifies that ingesting an event via EventFabric automatically evaluates risk,
    persists a RiskAssessment, and saves RiskFactors to SQLite.
    """
    evt_id = f"EVT-FABRIC-{uuid.uuid4().hex[:6].upper()}"
    event_payload = {
        "event_id": evt_id,
        "domain": "FINANCE",
        "user": "analyst_fabric_test",
        "role": "fraud_analyst",
        "resource": "SWIFT_GATEWAY:SETTLEMENT_VAULT",
        "action": "TRANSACTION",
        "device": "DEV-FABRIC-NEW",
        "location": "Offshore IP",
        "behavior": {"is_new_device": True, "is_unusual_location": True}
    }

    persisted = await event_fabric.ingest_event(event_payload)
    assert persisted["event_id"] == evt_id
    assert "assessment_id" in persisted
    assert "risk_category" in persisted
    assert persisted["risk_category"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    stored_assessment = await store.get_risk_assessment_detail(persisted["assessment_id"])
    assert stored_assessment is not None
    assert stored_assessment["id"] == persisted["assessment_id"]
    assert stored_assessment["identity"] == "analyst_fabric_test"
    assert len(stored_assessment["factors"]) > 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. REST API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

def test_api_assess_cyber_risk():
    """Tests POST /api/risk/assess endpoint."""
    payload = {
        "identity": "api_test_user",
        "role": "doctor",
        "resource": "ICU_CENTRAL_CONSOLE",
        "action": "BREAK_GLASS",
        "device": "CLINICAL-01",
        "location": "Emergency Room",
        "behavior": {"is_new_device": False},
        "domain": "HEALTHCARE"
    }
    resp = client.post("/api/risk/assess", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "assessment_id" in data
    assert "risk_score" in data
    assert "risk_category" in data
    assert "recommended_action" in data
    assert "explanation" in data
    assert isinstance(data["factors"], list)


def test_api_list_and_filter_assessments():
    """Tests GET /api/risk/assessments with filtering."""
    resp = client.get("/api/risk/assessments?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:
        first = data[0]
        assert "id" in first
        assert "risk_score" in first
        assert "risk_category" in first


def test_api_assessment_detail():
    """Tests GET /api/risk/assessments/{assessment_id}."""
    payload = {
        "identity": "detail_test_user",
        "role": "teller",
        "resource": "TREASURY_SWIFT",
        "action": "TRANSACTION",
        "device": "DEV-TEST-DETAIL",
        "location": "Downtown Branch",
        "domain": "FINANCE"
    }
    create_resp = client.post("/api/risk/assess", json=payload)
    assert create_resp.status_code == 200
    aid = create_resp.json()["assessment_id"]

    detail_resp = client.get(f"/api/risk/assessments/{aid}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == aid
    assert "factors" in detail
    assert "raw_event" in detail


def test_api_baseline_profile_and_reset(admin_token):
    """Tests GET & POST /api/risk/baselines/{identity}."""
    test_identity = f"test_persona_{uuid.uuid4().hex[:6]}"
    get_resp = client.get(f"/api/risk/baselines/{test_identity}")
    assert get_resp.status_code == 200
    base = get_resp.json()
    assert base["identity"] == test_identity

    reset_resp = client.post(
        f"/api/risk/baselines/{test_identity}/reset",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert reset_data["identity"] == test_identity
    assert reset_data["event_count"] == 0


def test_api_risk_stats():
    """Tests GET /api/risk/stats."""
    resp = client.get("/api/risk/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_assessments" in data
    assert "category_distribution" in data
    assert "average_risk_score" in data
    assert "average_confidence" in data
    assert "average_uncertainty" in data
    assert "recommended_actions" in data
