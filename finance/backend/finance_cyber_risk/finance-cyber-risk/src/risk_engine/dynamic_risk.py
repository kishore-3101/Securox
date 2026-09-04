"""
Dynamic Cyber Risk Engine.

Combines INDEPENDENT evidence already produced elsewhere in this system
into one 0-100 risk_score + LOW/MEDIUM/HIGH/CRITICAL risk_level, with a
component breakdown so the score is explainable rather than a black box.

Explicitly NOT just the XGBoost fraud probability: it's a weighted blend of
whichever of the following signals are actually available for the
entity/transaction being scored (missing signals are treated as "no
evidence", not silently defaulted to a value that changes the score):

  - anomaly      : Isolation Forest anomaly score (already 0-100-normalized here)
  - fraud        : supervised fraud-model probability (Indian Banking / ULB XGBoost)
  - aml          : AML model probability (AMLSim logistic regression / XGBoost)
  - graph        : graph_risk_score from src.risk_engine.graph_risk_scoring
  - propagation  : propagated_risk from src.risk_engine.propagation
  - criticality  : a documented structural/context proxy (e.g. account degree,
                    or a caller-supplied business criticality), NOT a learned score

Weights are ENGINEERING CONFIGURATION, not a scientifically validated
model — this is stated explicitly here and in
artifacts/metrics/risk_engine_documentation.md, and the config is saved to
artifacts/config/risk_engine_weights.json for transparency and reuse.
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

DEFAULT_WEIGHTS = {
    "anomaly": 0.15,
    "fraud": 0.30,
    "aml": 0.20,
    "graph": 0.15,
    "propagation": 0.10,
    "criticality": 0.10,
}

RISK_LEVEL_THRESHOLDS = {
    "LOW": (0, 25),
    "MEDIUM": (25, 50),
    "HIGH": (50, 75),
    "CRITICAL": (75, 100),
}


@dataclass
class RiskEngineConfig:
    weights: dict = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    level_thresholds: dict = field(default_factory=lambda: dict(RISK_LEVEL_THRESHOLDS))


def _clip01_to_100(x: float) -> float:
    return float(np.clip(x, 0.0, 100.0))


def normalize_signal(value: Optional[float], input_scale: str) -> Optional[float]:
    """
    Normalize a raw signal onto the common 0-100 risk scale used throughout
    this engine. `input_scale` documents what the caller is handing in:
      - "probability_0_1": a model probability in [0, 1] -> * 100
      - "score_0_100": already on a 0-100 scale (e.g. graph_risk_score) -> passthrough
      - "isolation_forest_raw": sklearn IsolationForest anomaly_score (roughly
        -0.5..0.5, higher = more anomalous) -> min-max squashed via a fixed,
        documented range rather than a per-call statistic (so the same raw
        score always maps to the same normalized value).
    Returns None if `value` is None (signal genuinely unavailable).
    """
    if value is None:
        return None
    if input_scale == "probability_0_1":
        return _clip01_to_100(value * 100.0)
    if input_scale == "score_0_100":
        return _clip01_to_100(value)
    if input_scale == "isolation_forest_raw":
        # Isolation Forest's decision_function-derived anomaly_score
        # (= -decision_function) typically falls roughly in [-0.5, 0.5] for
        # sklearn's default; we fix that as the assumed normalization range
        # rather than recomputing min/max per call (which would make the
        # same raw score map to different risk values depending on what
        # else was in the batch).
        lo, hi = -0.2, 0.4
        normalized = (value - lo) / (hi - lo)
        return _clip01_to_100(normalized * 100.0)
    raise ValueError(f"Unknown input_scale: {input_scale}")


def risk_level_from_score(score: float, thresholds: dict = RISK_LEVEL_THRESHOLDS) -> str:
    for level, (lo, hi) in thresholds.items():
        if lo <= score < hi:
            return level
    return "CRITICAL"  # score == 100 falls through the last half-open interval


def compute_dynamic_risk(
    signals: dict,
    config: Optional[RiskEngineConfig] = None,
    top_n_factors: int = 5,
) -> dict:
    """
    `signals`: dict of component_name -> value already normalized to 0-100
    (use `normalize_signal` first), or None if that signal is unavailable
    for this entity/transaction. Only keys in DEFAULT_WEIGHTS are read;
    unknown keys are ignored.

    Returns the documented breakdown structure:
      {
        "risk_score": ...,
        "risk_level": "...",
        "components": {...},   # normalized value used per component, or null
        "weights_used": {...}, # re-normalized weights actually applied (missing signals excluded)
        "top_risk_factors": [...],
      }
    """
    config = config or RiskEngineConfig()

    available = {k: v for k, v in signals.items() if k in config.weights and v is not None}
    if not available:
        return {
            "risk_score": 0.0,
            "risk_level": "LOW",
            "components": {k: signals.get(k) for k in config.weights},
            "weights_used": {},
            "top_risk_factors": ["no risk signals were available for this entity/transaction"],
        }

    # Re-normalize weights over only the signals actually present, so a
    # missing signal doesn't silently drag the score toward zero.
    total_weight = sum(config.weights[k] for k in available)
    weights_used = {k: config.weights[k] / total_weight for k in available}

    weighted_score = sum(available[k] * weights_used[k] for k in available)
    risk_score = round(_clip01_to_100(weighted_score), 2)
    risk_level = risk_level_from_score(risk_score, config.level_thresholds)

    contributions = sorted(
        (
            {
                "component": k,
                "value": round(available[k], 2),
                "weight": round(weights_used[k], 4),
                "contribution": round(available[k] * weights_used[k], 2),
            }
            for k in available
        ),
        key=lambda c: -c["contribution"],
    )
    top_risk_factors = [
        f"{c['component']} = {c['value']:.1f}/100 (weight {c['weight']:.2f}, "
        f"contributed {c['contribution']:.1f} points)"
        for c in contributions[:top_n_factors]
    ]

    components_full = {k: (round(signals[k], 2) if signals.get(k) is not None else None) for k in config.weights}

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "components": components_full,
        "weights_used": {k: round(v, 4) for k, v in weights_used.items()},
        "top_risk_factors": top_risk_factors,
    }
