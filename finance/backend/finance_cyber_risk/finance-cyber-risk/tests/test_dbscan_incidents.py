import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.models.clustering.dbscan_incidents import DBSCANIncidentConfig, cluster_incidents


def _synthetic_events():
    """Two tight clusters of events + a couple of clear outliers."""
    rng = np.random.default_rng(0)
    cluster_a_time = rng.normal(1000, 2, 10)
    cluster_b_time = rng.normal(5000, 2, 10)
    outlier_time = [20000, 40000]

    time_numeric = np.concatenate([cluster_a_time, cluster_b_time, outlier_time])
    risk_score = np.concatenate([rng.normal(80, 1, 10), rng.normal(60, 1, 10), [95, 10]])
    amount_log1p = np.concatenate([rng.normal(5, 0.1, 10), rng.normal(7, 0.1, 10), [10, 2]])
    n = len(time_numeric)

    return pd.DataFrame(
        {
            "event_id": [f"E{i}" for i in range(n)],
            "entity_id": [f"C{i % 5}" for i in range(n)],
            "time_numeric": time_numeric,
            "risk_score": risk_score,
            "amount_log1p": amount_log1p,
            "channel": ["Mobile_App"] * n,
            "transaction_type": ["UPI"] * n,
        }
    )


def test_dbscan_finds_at_least_one_cluster_and_some_noise():
    events = _synthetic_events()
    config = DBSCANIncidentConfig(eps=1.0, min_samples=3)
    result = cluster_incidents(
        events, event_id_col="event_id", entity_id_col="entity_id", time_col="time_numeric",
        risk_score_col="risk_score", config=config,
    )
    assert result["n_clusters"] >= 1
    assert result["n_noise"] >= 1


def test_dbscan_incident_structure_contains_required_fields():
    events = _synthetic_events()
    result = cluster_incidents(
        events, event_id_col="event_id", entity_id_col="entity_id", time_col="time_numeric",
        risk_score_col="risk_score",
    )
    for incident in result["incidents"]:
        for key in ["incident_id", "cluster_id", "events", "affected_entities", "time_range", "severity", "dominant_behavior", "aggregate_risk"]:
            assert key in incident


def test_dbscan_does_not_force_predefined_cluster_count():
    import inspect
    sig = inspect.signature(cluster_incidents)
    assert "n_clusters" not in sig.parameters


def test_dbscan_empty_input_returns_empty_result():
    empty = pd.DataFrame(columns=["event_id", "entity_id", "time_numeric", "risk_score"])
    result = cluster_incidents(
        empty, event_id_col="event_id", entity_id_col="entity_id", time_col="time_numeric",
        risk_score_col="risk_score",
    )
    assert result["n_clusters"] == 0
    assert result["incidents"] == []


def test_dbscan_severity_matches_aggregate_risk_bucket():
    events = _synthetic_events()
    result = cluster_incidents(
        events, event_id_col="event_id", entity_id_col="entity_id", time_col="time_numeric",
        risk_score_col="risk_score", config=DBSCANIncidentConfig(eps=1.0, min_samples=3),
    )
    for incident in result["incidents"]:
        risk = incident["aggregate_risk"]
        sev = incident["severity"]
        if risk >= 75:
            assert sev == "CRITICAL"
        elif risk >= 50:
            assert sev == "HIGH"
        elif risk >= 25:
            assert sev == "MEDIUM"
        else:
            assert sev == "LOW"


def test_dbscan_missing_columns_raises_clear_error():
    events = pd.DataFrame({"event_id": ["a"], "entity_id": ["c1"]})
    with pytest.raises(ValueError):
        cluster_incidents(
            events, event_id_col="event_id", entity_id_col="entity_id", time_col=None,
            risk_score_col="risk_score",
            config=DBSCANIncidentConfig(numeric_cols=(), categorical_cols=()),
        )
