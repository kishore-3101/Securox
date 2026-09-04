import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from src.risk_engine.unified_risk import assess_unified_risk
from src.risk_engine.response_engine import recommend_response
from src.explainability.full_explanation import build_full_explanation


# ------------------------------------------------------------ edge cases


def test_completely_normal_transaction():
    result = assess_unified_risk(
        transaction_id="T1", fraud_probability=0.01, anomaly_score_raw=-0.15, financial_exposure=100.0
    )
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["risk_level"] == "LOW"


def test_highly_anomalous_transaction():
    result = assess_unified_risk(transaction_id="T2", anomaly_score_raw=0.45, financial_exposure=100.0)
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["anomaly_score"] == 0.45


def test_high_fraud_probability_transaction():
    result = assess_unified_risk(transaction_id="T3", fraud_probability=0.97, financial_exposure=1000.0)
    assert result["risk_level"] in ("HIGH", "CRITICAL")
    assert result["cyber_exposure"] is not None


def test_aml_positive_entity():
    result = assess_unified_risk(entity_id="A1", aml_probability=0.9)
    assert 0.0 <= result["risk_score"] <= 100.0
    assert result["cyber_exposure"] is None  # no financial_exposure supplied for AML-only entity


def test_high_graph_risk_entity():
    result = assess_unified_risk(entity_id="A2", graph_risk_score=95.0)
    assert result["risk_score"] > 0


def test_high_propagation_risk_entity():
    fake_propagation = {
        "blast_radius": 3,
        "affected_entities": [{"entity_id": "X", "propagated_risk": 90.0}],
        "highest_risk_downstream_entities": [{"entity_id": "X", "propagated_risk": 90.0}],
        "propagation_paths": [["A", "X"]],
    }
    result = assess_unified_risk(entity_id="A3", propagation_result=fake_propagation)
    assert result["propagation_risk"] == 90.0
    assert "X" in result["affected_entities"]


def test_critical_entity_all_signals_maxed():
    fake_propagation = {
        "blast_radius": 5,
        "affected_entities": [{"entity_id": "X", "propagated_risk": 100.0}],
        "highest_risk_downstream_entities": [{"entity_id": "X", "propagated_risk": 100.0}],
        "propagation_paths": [["A", "X"]],
    }
    result = assess_unified_risk(
        entity_id="A4",
        fraud_probability=1.0,
        aml_probability=1.0,
        graph_risk_score=100.0,
        propagation_result=fake_propagation,
        criticality=1.0,
        anomaly_score_raw=0.5,
        financial_exposure=10000.0,
        incident_type="confirmed_fraud",
    )
    assert result["risk_score"] == 100.0
    assert result["risk_level"] == "CRITICAL"


def test_missing_optional_signals_are_null_not_fabricated():
    result = assess_unified_risk(transaction_id="T5", fraud_probability=0.3)
    assert result["aml_probability"] is None
    assert result["graph_risk_score"] is None
    assert result["propagation_risk"] is None
    assert result["cyber_exposure"] is None


def test_risk_score_always_bounded_across_many_random_combinations():
    import random

    rng = random.Random(0)
    for _ in range(50):
        kwargs = {}
        for key in ["fraud_probability", "aml_probability", "criticality"]:
            if rng.random() > 0.5:
                kwargs[key] = rng.random()
        if rng.random() > 0.5:
            kwargs["anomaly_score_raw"] = rng.uniform(-0.5, 0.5)
        if rng.random() > 0.5:
            kwargs["graph_risk_score"] = rng.uniform(0, 100)
        result = assess_unified_risk(entity_id="R", **kwargs)
        assert 0.0 <= result["risk_score"] <= 100.0
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


# --------------------------------------------------------- response engine


@pytest.mark.parametrize("level", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
def test_response_engine_returns_recommendations_for_every_level(level):
    recs = recommend_response(risk_level=level)
    assert len(recs) >= 1
    for r in recs:
        assert set(r.keys()) == {"action", "priority", "reason", "human_approval_required"}
        assert r["human_approval_required"] is True  # never autonomous


def test_response_engine_low_risk_only_monitors():
    recs = recommend_response(risk_level="LOW")
    actions = {r["action"] for r in recs}
    assert actions == {"monitor"}


def test_response_engine_critical_includes_containment_and_escalation():
    recs = recommend_response(risk_level="CRITICAL")
    actions = {r["action"] for r in recs}
    assert "recommend_containment" in actions
    assert "escalate_to_soc" in actions
    assert "preserve_evidence" in actions


def test_response_engine_adds_targeted_recommendation_for_high_aml_probability():
    recs = recommend_response(risk_level="MEDIUM", aml_probability=0.9)
    actions = {r["action"] for r in recs}
    assert "file_sar_review" in actions


def test_response_engine_unknown_level_defaults_safely():
    recs = recommend_response(risk_level="NOT_A_REAL_LEVEL")
    assert recs[0]["action"] == "monitor"


def test_response_engine_never_returns_autonomous_execution_actions():
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        recs = recommend_response(risk_level=level, fraud_probability=0.99, aml_probability=0.99, propagation_risk=99)
        forbidden_terms = ["execute", "auto_block", "auto_freeze", "auto_reverse"]
        for r in recs:
            assert not any(term in r["action"].lower() for term in forbidden_terms)


# ------------------------------------------------------------- explanation


def test_full_explanation_structure_has_all_seven_sections():
    unified = assess_unified_risk(transaction_id="T9", fraud_probability=0.9, financial_exposure=500.0)
    explanation = build_full_explanation(unified_result=unified)
    for key in [
        "1_what_happened", "2_why_suspicious", "3_model_contributions",
        "4_graph_relationships", "5_risk_propagation", "6_financial_exposure",
        "7_recommended_response",
    ]:
        assert key in explanation


def test_full_explanation_distinguishes_prediction_from_simulation_from_response():
    unified = assess_unified_risk(transaction_id="T10", fraud_probability=0.9, financial_exposure=500.0)
    explanation = build_full_explanation(unified_result=unified)
    assert "AI_PREDICTION" in explanation["3_model_contributions"]
    assert "GRAPH_SIMULATION" in explanation["5_risk_propagation"]
    assert "FINANCIAL_EXPOSURE_ESTIMATE" in explanation["6_financial_exposure"]
    assert "RECOMMENDED_RESPONSE" in explanation["7_recommended_response"]


def test_full_explanation_handles_missing_graph_and_shap_gracefully():
    unified = assess_unified_risk(transaction_id="T11", fraud_probability=0.2)
    explanation = build_full_explanation(unified_result=unified, shap_explanation=None, graph_evidence=None)
    assert "note" in explanation["3_model_contributions"]["AI_PREDICTION"]
    assert "note" in explanation["4_graph_relationships"]["GRAPH_SIMULATION"]


def test_full_explanation_response_recommendations_present():
    unified = assess_unified_risk(entity_id="A5", aml_probability=0.95, graph_risk_score=90.0)
    explanation = build_full_explanation(unified_result=unified)
    recs = explanation["7_recommended_response"]["RECOMMENDED_RESPONSE"]
    assert len(recs) >= 1
    assert all(r["human_approval_required"] for r in recs)
