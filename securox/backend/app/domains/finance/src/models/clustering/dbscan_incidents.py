"""
DBSCAN-based incident clustering.

Purpose: group related suspicious transactions/events into incidents to
reduce alert fatigue, rather than presenting every flagged transaction as
its own isolated alert. DBSCAN is used specifically because it does NOT
require a predefined number of clusters and naturally separates "noise"
(isolated suspicious events with no similar neighbors) from genuine
clusters of related activity.

No ground-truth "incident" labels exist anywhere in these datasets, so no
clustering accuracy/precision is claimed or computed here — only descriptive
cluster statistics (size, time range, aggregate risk, dominant behavior).
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import OneHotEncoder, StandardScaler


@dataclass
class DBSCANIncidentConfig:
    eps: float = 1.5
    min_samples: int = 3
    numeric_cols: tuple = ("time_numeric", "risk_score", "amount_log1p")
    categorical_cols: tuple = ("channel", "transaction_type")


def _build_feature_matrix(events: pd.DataFrame, config: DBSCANIncidentConfig) -> np.ndarray:
    numeric_cols = [c for c in config.numeric_cols if c in events.columns]
    categorical_cols = [c for c in config.categorical_cols if c in events.columns]

    parts = []
    if numeric_cols:
        scaler = StandardScaler()
        parts.append(scaler.fit_transform(events[numeric_cols].fillna(0.0)))
    if categorical_cols:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        parts.append(encoder.fit_transform(events[categorical_cols].astype(str)))

    if not parts:
        raise ValueError(
            "No usable numeric or categorical columns found for clustering — "
            f"expected some of {config.numeric_cols + config.categorical_cols}."
        )
    return np.hstack(parts)


def cluster_incidents(
    events: pd.DataFrame,
    event_id_col: str,
    entity_id_col: str,
    time_col: Optional[str],
    risk_score_col: str,
    config: Optional[DBSCANIncidentConfig] = None,
) -> dict:
    """
    events: one row per suspicious event/transaction already selected for
    clustering (e.g. everything above some risk threshold — this function
    does not itself decide what counts as "suspicious").

    Returns:
      {
        "incidents": [ {incident_id, cluster_id, events, affected_entities,
                         time_range, severity, dominant_behavior, aggregate_risk} ],
        "isolated_events": [ {event_id, entity_id, risk_score} ],  # DBSCAN noise (-1)
        "n_clusters": int,
        "n_noise": int,
        "config": {...},
      }
    """
    config = config or DBSCANIncidentConfig()
    events = events.reset_index(drop=True).copy()

    if len(events) == 0:
        return {"incidents": [], "isolated_events": [], "n_clusters": 0, "n_noise": 0, "config": config.__dict__}

    X = _build_feature_matrix(events, config)
    labels = DBSCAN(eps=config.eps, min_samples=config.min_samples).fit_predict(X)
    events["_cluster_id"] = labels

    incidents = []
    for cluster_id, group in events[events["_cluster_id"] != -1].groupby("_cluster_id"):
        time_range = None
        if time_col and time_col in group.columns:
            time_range = {"start": str(group[time_col].min()), "end": str(group[time_col].max())}

        aggregate_risk = float(group[risk_score_col].mean())
        severity = (
            "CRITICAL" if aggregate_risk >= 75 else
            "HIGH" if aggregate_risk >= 50 else
            "MEDIUM" if aggregate_risk >= 25 else
            "LOW"
        )
        dominant_behavior = {}
        for cat_col in config.categorical_cols:
            if cat_col in group.columns and not group[cat_col].empty:
                dominant_behavior[cat_col] = group[cat_col].mode().iat[0]

        incidents.append(
            {
                "incident_id": f"incident_{int(cluster_id)}",
                "cluster_id": int(cluster_id),
                "events": group[event_id_col].tolist(),
                "affected_entities": sorted(group[entity_id_col].astype(str).unique().tolist()),
                "time_range": time_range,
                "severity": severity,
                "dominant_behavior": dominant_behavior,
                "aggregate_risk": round(aggregate_risk, 2),
                "n_events": int(len(group)),
            }
        )

    incidents.sort(key=lambda i: -i["aggregate_risk"])

    noise = events[events["_cluster_id"] == -1]
    isolated_events = [
        {
            "event_id": row[event_id_col],
            "entity_id": row[entity_id_col],
            "risk_score": float(row[risk_score_col]),
        }
        for _, row in noise.iterrows()
    ]

    return {
        "incidents": incidents,
        "isolated_events": isolated_events,
        "n_clusters": len(incidents),
        "n_noise": len(isolated_events),
        "config": {
            "eps": config.eps,
            "min_samples": config.min_samples,
            "numeric_cols": list(config.numeric_cols),
            "categorical_cols": list(config.categorical_cols),
        },
    }
