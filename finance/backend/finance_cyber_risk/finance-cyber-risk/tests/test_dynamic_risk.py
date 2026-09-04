import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.risk_engine.dynamic_risk import (
    RiskEngineConfig,
    compute_dynamic_risk,
    normalize_signal,
    risk_level_from_score,
)


def test_normalize_probability_scale():
    assert normalize_signal(0.5, "probability_0_1") == 50.0
    assert normalize_signal(1.0, "probability_0_1") == 100.0
    assert normalize_signal(0.0, "probability_0_1") == 0.0


def test_normalize_score_0_100_passthrough_and_clip():
    assert normalize_signal(60, "score_0_100") == 60.0
    assert normalize_signal(150, "score_0_100") == 100.0  # clipped
    assert normalize_signal(-10, "score_0_100") == 0.0  # clipped


def test_normalize_none_returns_none():
    assert normalize_signal(None, "probability_0_1") is None


def test_normalize_unknown_scale_raises():
    with pytest.raises(ValueError):
        normalize_signal(0.5, "not_a_real_scale")


@pytest.mark.parametrize(
    "score,expected_level",
    [(0, "LOW"), (24.9, "LOW"), (25, "MEDIUM"), (49.9, "MEDIUM"), (50, "HIGH"), (74.9, "HIGH"), (75, "CRITICAL"), (100, "CRITICAL")],
)
def test_risk_level_mapping(score, expected_level):
    assert risk_level_from_score(score) == expected_level


def test_risk_score_always_between_0_and_100_normal_case():
    signals = {"anomaly": 10, "fraud": 5, "aml": None, "graph": 8, "propagation": None, "criticality": 20}
    result = compute_dynamic_risk(signals)
    assert 0.0 <= result["risk_score"] <= 100.0


def test_risk_score_bounded_when_all_signals_maxed():
    signals = {"anomaly": 100, "fraud": 100, "aml": 100, "graph": 100, "propagation": 100, "criticality": 100}
    result = compute_dynamic_risk(signals)
    assert result["risk_score"] == 100.0
    assert result["risk_level"] == "CRITICAL"


def test_risk_score_zero_when_all_signals_zero():
    signals = {"anomaly": 0, "fraud": 0, "aml": 0, "graph": 0, "propagation": 0, "criticality": 0}
    result = compute_dynamic_risk(signals)
    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "LOW"


def test_no_signals_available_returns_low_risk_not_an_error():
    signals = {"anomaly": None, "fraud": None, "aml": None, "graph": None, "propagation": None, "criticality": None}
    result = compute_dynamic_risk(signals)
    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "LOW"
    assert "no risk signals" in result["top_risk_factors"][0]


def test_missing_signal_weights_renormalized_over_available_only():
    """If only 'fraud' is available, it alone should determine the whole
    score (weight renormalized to 1.0), not be diluted by absent signals."""
    signals = {"anomaly": None, "fraud": 80, "aml": None, "graph": None, "propagation": None, "criticality": None}
    result = compute_dynamic_risk(signals)
    assert result["risk_score"] == pytest.approx(80.0)
    assert result["weights_used"]["fraud"] == pytest.approx(1.0)


def test_components_dict_reports_null_for_unavailable_signals():
    signals = {"anomaly": 30, "fraud": None, "aml": None, "graph": None, "propagation": None, "criticality": None}
    result = compute_dynamic_risk(signals)
    assert result["components"]["fraud"] is None
    assert result["components"]["anomaly"] == 30.0


def test_top_risk_factors_ordered_by_contribution_descending():
    signals = {"anomaly": 10, "fraud": 90, "aml": None, "graph": 20, "propagation": None, "criticality": None}
    result = compute_dynamic_risk(signals)
    assert result["top_risk_factors"][0].startswith("fraud")


def test_custom_weights_config_is_respected():
    config = RiskEngineConfig(weights={"anomaly": 1.0, "fraud": 0.0, "aml": 0.0, "graph": 0.0, "propagation": 0.0, "criticality": 0.0})
    signals = {"anomaly": 40, "fraud": 100, "aml": 0, "graph": 0, "propagation": 0, "criticality": 0}
    result = compute_dynamic_risk(signals, config=config)
    # only 'anomaly' has nonzero weight, so score should equal anomaly's value
    assert result["risk_score"] == pytest.approx(40.0)
