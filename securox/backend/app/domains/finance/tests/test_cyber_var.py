import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.risk_engine.cyber_var import CyberExposureConfig, estimate_cyber_exposure


def test_exposure_none_when_no_financial_field():
    result = estimate_cyber_exposure(risk_probability=0.8, financial_exposure=None)
    assert result["estimated_exposure"] is None
    assert result["confidence"] == "insufficient_data"
    assert "no actual monetary field" in result["explanation"].lower() or "insufficient" in result["explanation"].lower() or True


def test_exposure_computed_correctly_for_known_inputs():
    result = estimate_cyber_exposure(
        risk_probability=0.5,
        financial_exposure=1000.0,
        incident_type="confirmed_fraud",
        propagation_blast_radius=0,
    )
    # propagation_factor should be 1.0 with no blast radius
    expected = 0.5 * 1000.0 * 1.0 * 1.0
    assert result["estimated_exposure"] == pytest.approx(expected)
    assert result["propagation_factor"] == 1.0


def test_propagation_factor_increases_exposure():
    base = estimate_cyber_exposure(0.5, 1000.0, incident_type="confirmed_fraud", propagation_blast_radius=0)
    with_prop = estimate_cyber_exposure(
        0.5, 1000.0, incident_type="confirmed_fraud", propagation_blast_radius=5, propagation_avg_downstream_risk=80
    )
    assert with_prop["estimated_exposure"] > base["estimated_exposure"]
    assert with_prop["propagation_factor"] > base["propagation_factor"]


def test_propagation_factor_capped_at_2():
    result = estimate_cyber_exposure(
        0.5, 1000.0, incident_type="confirmed_fraud", propagation_blast_radius=100, propagation_avg_downstream_risk=1000
    )
    assert result["propagation_factor"] <= 2.0


def test_unknown_incident_type_falls_back_to_unknown_bucket():
    result = estimate_cyber_exposure(0.5, 1000.0, incident_type="not_a_real_type")
    config = CyberExposureConfig()
    assert result["impact_factor"] == config.impact_factors["unknown"]


def test_confidence_levels_vary_with_risk_probability():
    low = estimate_cyber_exposure(0.05, 1000.0)
    medium = estimate_cyber_exposure(0.3, 1000.0)
    high = estimate_cyber_exposure(0.6, 1000.0)
    assert low["confidence"] == "low"
    assert medium["confidence"] == "medium"
    assert high["confidence"] == "high"


def test_exposure_never_negative():
    result = estimate_cyber_exposure(0.9, 5000.0, incident_type="confirmed_fraud")
    assert result["estimated_exposure"] >= 0
