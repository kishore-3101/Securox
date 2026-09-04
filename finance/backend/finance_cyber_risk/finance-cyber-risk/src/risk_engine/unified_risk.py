"""
Unified Risk Assessment.

A single entry point that combines whichever of the following are actually
available for a given transaction/entity into one structured result:
  Fraud AI (XGBoost) + Anomaly Detection (Isolation Forest) + AML Detection
  + Graph Intelligence + Propagation + Dynamic Risk + Cyber Exposure.

Nothing is fabricated: any signal not supplied by the caller is reported as
null in the output rather than defaulted to a value that would silently
change the score. See src/risk_engine/dynamic_risk.py for how missing
signals affect weighting (weights are renormalized over what's present).
"""
from dataclasses import dataclass
from typing import Optional

from src.risk_engine.cyber_var import CyberExposureConfig, estimate_cyber_exposure
from src.risk_engine.dynamic_risk import RiskEngineConfig, compute_dynamic_risk, normalize_signal


def assess_unified_risk(
    entity_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    fraud_probability: Optional[float] = None,
    anomaly_score_raw: Optional[float] = None,
    aml_probability: Optional[float] = None,
    graph_risk_score: Optional[float] = None,
    propagation_result: Optional[dict] = None,
    criticality: Optional[float] = None,
    financial_exposure: Optional[float] = None,
    incident_type: str = "unknown",
    risk_engine_config: Optional[RiskEngineConfig] = None,
    cyber_exposure_config: Optional[CyberExposureConfig] = None,
) -> dict:
    """
    All *_probability / *_score arguments accept their NATIVE scale:
      - fraud_probability, aml_probability: model probability in [0, 1]
      - anomaly_score_raw: raw Isolation Forest anomaly_score (see
        src.models.anomaly.isolation_forest_model.anomaly_scores)
      - graph_risk_score: already 0-100 (from src.risk_engine.graph_risk_scoring)
      - propagation_result: the dict returned by
        src.risk_engine.propagation.propagate_risk (or None if propagation
        wasn't computed for this entity, e.g. it isn't in any graph)
      - criticality: caller-supplied 0-1 business/structural criticality, or
        None if not assessed
    """
    propagation_risk_0_100 = None
    affected_entities = []
    propagation_paths = []
    if propagation_result is not None and propagation_result.get("blast_radius", 0) > 0:
        downstream = propagation_result.get("highest_risk_downstream_entities", [])
        propagation_risk_0_100 = (
            sum(d["propagated_risk"] for d in downstream) / len(downstream) if downstream else 0.0
        )
        affected_entities = [a["entity_id"] for a in propagation_result.get("affected_entities", [])]
        propagation_paths = propagation_result.get("propagation_paths", [])

    signals = {
        "anomaly": normalize_signal(anomaly_score_raw, "isolation_forest_raw") if anomaly_score_raw is not None else None,
        "fraud": normalize_signal(fraud_probability, "probability_0_1") if fraud_probability is not None else None,
        "aml": normalize_signal(aml_probability, "probability_0_1") if aml_probability is not None else None,
        "graph": normalize_signal(graph_risk_score, "score_0_100") if graph_risk_score is not None else None,
        "propagation": normalize_signal(propagation_risk_0_100, "score_0_100") if propagation_risk_0_100 is not None else None,
        "criticality": normalize_signal(criticality, "probability_0_1") if criticality is not None else None,
    }

    dynamic_risk = compute_dynamic_risk(signals, config=risk_engine_config)

    exposure = estimate_cyber_exposure(
        risk_probability=dynamic_risk["risk_score"] / 100.0,
        financial_exposure=financial_exposure,
        incident_type=incident_type,
        propagation_blast_radius=(propagation_result or {}).get("blast_radius", 0),
        propagation_avg_downstream_risk=propagation_risk_0_100 or 0.0,
        config=cyber_exposure_config,
    )

    return {
        "entity_id": entity_id,
        "transaction_id": transaction_id,
        "fraud_probability": fraud_probability,
        "anomaly_score": anomaly_score_raw,
        "aml_probability": aml_probability,
        "graph_risk_score": graph_risk_score,
        "propagation_risk": round(propagation_risk_0_100, 2) if propagation_risk_0_100 is not None else None,
        "risk_score": dynamic_risk["risk_score"],
        "risk_level": dynamic_risk["risk_level"],
        "cyber_exposure": exposure["estimated_exposure"],
        "affected_entities": affected_entities,
        "propagation_paths": propagation_paths,
        "risk_breakdown": dynamic_risk,
        "cyber_exposure_breakdown": exposure,
        "top_risk_factors": dynamic_risk["top_risk_factors"],
    }
