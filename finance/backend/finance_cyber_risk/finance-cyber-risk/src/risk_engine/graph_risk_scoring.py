"""
Graph-risk scoring: converts TransactionGraph structure into a 0-100
"graph_risk_score" plus a list of the specific structural reasons behind it.

This is explicitly NOT the final cyber-risk score for the whole system —
it's one evidence source (graph structure) that a later risk-fusion stage
can combine with the fraud/AML model outputs. Nothing here uses is_sar or
any other label; every signal is purely structural.

Scoring is a configurable weighted combination of normalized structural
signals, capped at 100, so it stays interpretable rather than a black box.
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.models.graph.transaction_graph import TransactionGraph

DEFAULT_WEIGHTS = {
    "degree": 25.0,             # how connected the account is overall
    "fan_in_fan_out": 25.0,     # simultaneous high fan-in AND fan-out (layering shape)
    "suspicious_neighbors": 30.0,  # share of neighbors that are themselves structurally flagged
    "centrality": 20.0,         # pagerank / betweenness, when available
}


@dataclass
class GraphRiskConfig:
    weights: dict = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    fan_in_percentile: float = 95.0
    fan_out_percentile: float = 95.0
    degree_percentile_cap: float = 99.0  # score saturates at this percentile of degree


def _normalize(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return float(np.clip(value / cap, 0.0, 1.0))


def score_entity(
    graph: TransactionGraph,
    entity_id,
    config: Optional[GraphRiskConfig] = None,
    suspicious_node_ids: Optional[set] = None,
    all_node_features=None,
) -> dict:
    """
    Compute graph-risk evidence for a single account/entity.

    Returns exactly the shape requested:
      {
        "entity_id": ...,
        "graph_risk_score": 0-100,
        "risk_factors": [...],
        "centrality": {...},
        "suspicious_neighbors": [...],
        "connected_component_size": int,
      }
    """
    config = config or GraphRiskConfig()

    if all_node_features is None:
        all_node_features = graph.calculate_node_features(compute_expensive=False)

    if suspicious_node_ids is None:
        suspicious_node_ids = set(
            graph.find_suspicious_nodes(
                fan_in_percentile=config.fan_in_percentile,
                fan_out_percentile=config.fan_out_percentile,
            )["ACCOUNT_ID"]
        )

    node_row = all_node_features[all_node_features["ACCOUNT_ID"] == entity_id]
    if node_row.empty:
        return {
            "entity_id": entity_id,
            "graph_risk_score": 0.0,
            "risk_factors": ["entity not present in the transaction graph"],
            "centrality": {},
            "suspicious_neighbors": [],
            "connected_component_size": 0,
        }
    node_row = node_row.iloc[0]

    degree_cap = all_node_features["total_degree"].quantile(config.degree_percentile_cap / 100.0)
    in_threshold = all_node_features["in_degree"].quantile(config.fan_in_percentile / 100.0)
    out_threshold = all_node_features["out_degree"].quantile(config.fan_out_percentile / 100.0)

    local_risk = graph.local_network_risk(entity_id, suspicious_node_ids=suspicious_node_ids)

    risk_factors = []
    component_scores = {}

    # 1. overall connectivity
    degree_component = _normalize(node_row["total_degree"], degree_cap)
    component_scores["degree"] = degree_component
    if degree_component > 0.7:
        risk_factors.append(
            f"unusually high total connectivity (total_degree={int(node_row['total_degree'])}, "
            f"top {100 - config.degree_percentile_cap:.0f}th+ percentile)"
        )

    # 2. simultaneous fan-in AND fan-out (classic layering/pass-through shape)
    high_fan_in = node_row["in_degree"] >= in_threshold
    high_fan_out = node_row["out_degree"] >= out_threshold
    fan_component = 1.0 if (high_fan_in and high_fan_out) else (0.5 if (high_fan_in or high_fan_out) else 0.0)
    component_scores["fan_in_fan_out"] = fan_component
    if high_fan_in and high_fan_out:
        risk_factors.append(
            f"simultaneous high fan-in (in_degree={int(node_row['in_degree'])}) and "
            f"high fan-out (out_degree={int(node_row['out_degree'])}) — pass-through/layering shape"
        )
    elif high_fan_in:
        risk_factors.append(f"unusually high fan-in (in_degree={int(node_row['in_degree'])})")
    elif high_fan_out:
        risk_factors.append(f"unusually high fan-out (out_degree={int(node_row['out_degree'])})")

    # 3. suspicious neighbors
    susp_ratio = local_risk["suspicious_neighbor_ratio"]
    component_scores["suspicious_neighbors"] = susp_ratio
    if local_risk["suspicious_neighbor_count"] > 0:
        risk_factors.append(
            f"{local_risk['suspicious_neighbor_count']} of {local_risk['neighbor_count']} "
            f"direct neighbors are themselves structurally flagged as high fan-in/fan-out"
        )

    # 4. centrality, if it was actually computed for this graph
    centrality = {}
    centrality_component = 0.0
    if "pagerank" in node_row.index and node_row.get("pagerank") is not None and not pd_isna(node_row.get("pagerank")):
        pagerank_cap = all_node_features["pagerank"].quantile(0.99) if all_node_features["pagerank"].notna().any() else 0
        betweenness_cap = all_node_features["betweenness_centrality"].quantile(0.99) if all_node_features["betweenness_centrality"].notna().any() else 0
        centrality = {
            "pagerank": float(node_row["pagerank"]),
            "betweenness_centrality": float(node_row["betweenness_centrality"]),
            "closeness_centrality": float(node_row["closeness_centrality"]),
        }
        pr_component = _normalize(node_row["pagerank"], pagerank_cap)
        bw_component = _normalize(node_row["betweenness_centrality"], betweenness_cap)
        centrality_component = (pr_component + bw_component) / 2
        component_scores["centrality"] = centrality_component
        if pr_component > 0.7:
            risk_factors.append(f"high PageRank ({node_row['pagerank']:.5f}) relative to the rest of the graph")
        if bw_component > 0.7:
            risk_factors.append(
                f"high betweenness centrality ({node_row['betweenness_centrality']:.5f}) — "
                "sits on many shortest paths between other accounts"
            )
    else:
        component_scores["centrality"] = 0.0

    weights = config.weights
    total_weight = sum(weights.values())
    weighted_sum = sum(component_scores.get(k, 0.0) * w for k, w in weights.items())
    graph_risk_score = float(np.clip((weighted_sum / total_weight) * 100.0, 0.0, 100.0))

    if not risk_factors:
        risk_factors.append("no elevated structural risk signals detected")

    return {
        "entity_id": entity_id,
        "graph_risk_score": round(graph_risk_score, 2),
        "risk_factors": risk_factors,
        "centrality": centrality,
        "suspicious_neighbors": local_risk["suspicious_neighbors"],
        "connected_component_size": local_risk["connected_component_size"],
    }


def pd_isna(value) -> bool:
    import pandas as pd

    return pd.isna(value)


def score_all_entities(graph: TransactionGraph, config: Optional[GraphRiskConfig] = None) -> list:
    """Score every node currently in the graph. Reuses one shared node-feature
    table and one shared suspicious-node set instead of recomputing them per
    entity (each of those calls is itself O(nodes+edges))."""
    config = config or GraphRiskConfig()
    all_node_features = graph.calculate_node_features(compute_expensive=False)
    suspicious_node_ids = set(
        graph.find_suspicious_nodes(
            fan_in_percentile=config.fan_in_percentile,
            fan_out_percentile=config.fan_out_percentile,
        )["ACCOUNT_ID"]
    )
    return [
        score_entity(
            graph,
            node_id,
            config=config,
            suspicious_node_ids=suspicious_node_ids,
            all_node_features=all_node_features,
        )
        for node_id in all_node_features["ACCOUNT_ID"]
    ]
