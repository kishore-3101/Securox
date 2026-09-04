import pytest
from backend.services.risk_engine import risk_engine, categorise

def test_risk_calculation_bounds():
    res = risk_engine.compute(
        asset="POWER_GRID",
        anomaly_score=0.90,
        attack_type="DDOS",
        attack_confidence=0.95,
        active_threat_flags=["MALICIOUS_IP"]
    )
    assert 0.0 <= res["risk_score"] <= 100.0
    assert res["severity"] in ["CRITICAL", "HIGH", "CATASTROPHIC"]
    assert len(res["reasons"]) > 0
    assert "POWER_GRID" in res["asset"]

def test_risk_categorise_function():
    assert categorise(95.0) == "CATASTROPHIC"
    assert categorise(80.0) == "CRITICAL"
    assert categorise(65.0) == "HIGH"
    assert categorise(45.0) == "MODERATE"
    assert categorise(15.0) == "NORMAL"
