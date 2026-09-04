"""
Full explainability combiner.

Stitches together, for one high-risk transaction/entity:
  1. what happened            (raw facts about the transaction/entity)
  2. why it was suspicious    (which signals were elevated, in plain terms)
  3. which models contributed (fraud/anomaly/AML model outputs, with SHAP
                                 top features for the fraud model when available)
  4. which graph relationships contributed (graph_risk_score risk_factors,
                                 suspicious_neighbors)
  5. how risk propagated      (propagation engine's blast radius / paths,
                                 explicitly labeled as a simulation)
  6. estimated financial exposure (cyber_var breakdown, or explicitly "not
                                 available" when no monetary field exists)
  7. recommended response     (response_engine recommendations)

This module does not compute anything new — it only assembles outputs from
the unified risk assessment, the SHAP explainer, and the response engine
into one readable structure, and is careful to keep these four kinds of
statement visually/textually distinct: AI PREDICTION vs RISK CALCULATION vs
GRAPH SIMULATION vs FINANCIAL EXPOSURE ESTIMATE vs RECOMMENDED RESPONSE.
"""
from typing import Optional

from src.risk_engine.response_engine import recommend_response


def build_full_explanation(
    unified_result: dict,
    shap_explanation: Optional[dict] = None,
    graph_evidence: Optional[dict] = None,
    raw_transaction_summary: Optional[dict] = None,
) -> dict:
    """
    unified_result: output of src.risk_engine.unified_risk.assess_unified_risk
    shap_explanation: output of src.explainability.shap_explainer.FraudExplainer.explain(...).to_dict(),
        or None if no fraud model applies to this entity (e.g. an AMLSim account)
    graph_evidence: output of src.risk_engine.graph_risk_scoring.score_entity(...),
        or None if this entity isn't part of any transaction graph
    raw_transaction_summary: caller-supplied plain dict of raw facts (e.g.
        {"transaction_amount": ..., "channel": ..., "transaction_datetime": ...})
        for section 1 ("what happened") — never fabricated, only what the
        caller actually knows about this record.
    """
    what_happened = raw_transaction_summary or {
        "note": "No raw transaction/account summary was supplied by the caller."
    }

    why_suspicious = list(unified_result.get("top_risk_factors", []))

    model_contributions = {
        "AI_PREDICTION": {
            "fraud_probability": unified_result.get("fraud_probability"),
            "aml_probability": unified_result.get("aml_probability"),
            "anomaly_score_raw": unified_result.get("anomaly_score"),
            "shap_top_features": (shap_explanation or {}).get("top_contributing_features"),
            "shap_human_readable": (shap_explanation or {}).get("human_readable_explanation"),
            "note_on_ulb_features": (
                "If any SHAP feature above is one of ULB's V1-V28, no semantic "
                "meaning is assigned to it — it is reported by name only, per "
                "the feature dictionary."
            ),
        }
        if shap_explanation is not None
        else {"note": "No supervised fraud model applies to this entity."}
    }

    graph_contribution = {
        "GRAPH_SIMULATION": {
            "graph_risk_score": unified_result.get("graph_risk_score"),
            "risk_factors": (graph_evidence or {}).get("risk_factors"),
            "suspicious_neighbors": (graph_evidence or {}).get("suspicious_neighbors"),
            "connected_component_size": (graph_evidence or {}).get("connected_component_size"),
        }
        if graph_evidence is not None
        else {"note": "This entity is not part of any transaction graph in the current system."}
    }

    propagation_contribution = {
        "GRAPH_SIMULATION": {
            "propagation_risk": unified_result.get("propagation_risk"),
            "affected_entities": unified_result.get("affected_entities"),
            "propagation_paths": unified_result.get("propagation_paths"),
            "disclaimer": (
                "This is a simulated estimate of which entities are structurally "
                "close enough to be worth extra scrutiny — it is NOT a prediction "
                "that fraud/AML activity will actually spread to them."
            ),
        }
    }

    exposure_breakdown = unified_result.get("cyber_exposure_breakdown", {})
    financial_exposure_section = {
        "FINANCIAL_EXPOSURE_ESTIMATE": {
            "estimated_exposure": exposure_breakdown.get("estimated_exposure"),
            "confidence": exposure_breakdown.get("confidence"),
            "explanation": exposure_breakdown.get("explanation"),
        }
    }

    recommendations = recommend_response(
        risk_level=unified_result.get("risk_level", "LOW"),
        fraud_probability=unified_result.get("fraud_probability"),
        aml_probability=unified_result.get("aml_probability"),
        graph_risk_score=unified_result.get("graph_risk_score"),
        propagation_risk=unified_result.get("propagation_risk"),
    )

    return {
        "1_what_happened": what_happened,
        "2_why_suspicious": why_suspicious,
        "3_model_contributions": model_contributions,
        "4_graph_relationships": graph_contribution,
        "5_risk_propagation": propagation_contribution,
        "6_financial_exposure": financial_exposure_section,
        "7_recommended_response": {"RECOMMENDED_RESPONSE": recommendations},
        "RISK_CALCULATION": {
            "risk_score": unified_result.get("risk_score"),
            "risk_level": unified_result.get("risk_level"),
            "risk_breakdown": unified_result.get("risk_breakdown"),
        },
    }
