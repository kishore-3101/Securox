"""
Simulated risk-propagation over the transaction graph.

IMPORTANT FRAMING: this is a risk-ESTIMATION simulation, not a prediction
that an actual attack/fraud will spread. It answers "if this entity is
risky, which other entities are structurally close enough that the same
risk might plausibly implicate them too, and how much should that concern
us" — a weighted, distance-decayed traversal over real graph edges, using
only signals that already exist elsewhere in this system (graph-risk
scores, degree-based "criticality").

Method: weighted BFS from the source entity. At each hop, the risk carried
across an edge decays with (a) graph distance and (b) the strength of the
relationship (currently: presence of an edge = weight 1.0 per edge; the
raw AMLSim data has no transaction amount, so relationship "strength" here
means transaction count between the pair, not monetary weight — documented
explicitly, not invented).
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from src.models.graph.transaction_graph import TransactionGraph


@dataclass
class PropagationConfig:
    max_depth: int = 3
    decay_per_hop: float = 0.5       # risk carried multiplies by this each hop
    min_risk_to_propagate: float = 5.0   # stop traversing once carried risk falls below this (0-100 scale)
    criticality_boost_cap: float = 1.5   # a highly-critical (high-degree) node can amplify received risk up to this factor
    max_affected_entities: int = 200     # safety cap so this stays fast on larger graphs


def _relationship_strength(graph: TransactionGraph, u, v) -> float:
    """Number of distinct transactions directly between u and v, in either
    direction (a MultiDiGraph can have several parallel edges). Used as a
    proxy for relationship strength since no transaction amount exists in
    the raw AMLSim data available here."""
    count = 0
    if graph.graph.has_edge(u, v):
        count += graph.graph.number_of_edges(u, v)
    if graph.graph.has_edge(v, u):
        count += graph.graph.number_of_edges(v, u)
    return float(count)


def _node_criticality(graph: TransactionGraph, node, all_features, config: PropagationConfig) -> float:
    """A simple, documented proxy for "how structurally important is this
    node" — normalized total_degree, capped. Not a learned quantity."""
    row = all_features[all_features["ACCOUNT_ID"] == node]
    if row.empty:
        return 1.0
    max_degree = all_features["total_degree"].max()
    if max_degree <= 0:
        return 1.0
    normalized = row.iloc[0]["total_degree"] / max_degree
    return float(1.0 + normalized * (config.criticality_boost_cap - 1.0))


def propagate_risk(
    graph: TransactionGraph,
    source_entity,
    source_risk: float,
    config: Optional[PropagationConfig] = None,
) -> dict:
    """
    Weighted BFS risk-propagation simulation starting at `source_entity`
    with an initial `source_risk` (0-100 scale, typically the entity's
    graph_risk_score or unified risk_score from the dynamic risk engine).

    Returns:
      {
        "source_entity": ...,
        "source_risk": ...,
        "affected_entities": [{"entity_id", "propagated_risk", "depth", "path"}],
        "propagation_paths": [[...]],
        "propagation_depth": max depth actually reached,
        "blast_radius": number of affected entities,
        "highest_risk_downstream_entities": top-N by propagated_risk,
        "config": {...},
        "disclaimer": "..."
      }
    """
    config = config or PropagationConfig()

    if source_entity not in graph.graph:
        return {
            "source_entity": source_entity,
            "source_risk": source_risk,
            "affected_entities": [],
            "propagation_paths": [],
            "propagation_depth": 0,
            "blast_radius": 0,
            "highest_risk_downstream_entities": [],
            "config": config.__dict__,
            "disclaimer": "Source entity not present in the transaction graph.",
        }

    all_features = graph.calculate_node_features(compute_expensive=False)
    max_relationship_strength = max(
        (
            graph.graph.number_of_edges(u, v)
            for u, v in graph.graph.edges()
        ),
        default=1,
    )

    # BFS frontier: (node, carried_risk, depth, path)
    frontier = [(source_entity, float(source_risk), 0, [source_entity])]
    visited_best_risk = {source_entity: float(source_risk)}
    affected = {}
    paths = []
    max_depth_reached = 0

    while frontier and len(affected) < config.max_affected_entities:
        node, carried_risk, depth, path = frontier.pop(0)
        if depth >= config.max_depth:
            continue

        neighbors = graph.find_neighbors(node, "both")
        for neighbor in neighbors:
            if neighbor == source_entity:
                continue
            strength = _relationship_strength(graph, node, neighbor)
            strength_factor = min(strength / max_relationship_strength, 1.0) if max_relationship_strength else 0.0
            # relationship strength scales how much of the decayed risk actually transfers
            criticality = _node_criticality(graph, neighbor, all_features, config)
            propagated = (
                carried_risk
                * config.decay_per_hop
                * (0.5 + 0.5 * strength_factor)  # weak links still carry a floor of half the decayed risk
                * criticality
            )
            propagated = float(np.clip(propagated, 0.0, 100.0))

            if propagated < config.min_risk_to_propagate:
                continue

            new_depth = depth + 1
            new_path = path + [neighbor]

            if neighbor not in visited_best_risk or propagated > visited_best_risk[neighbor]:
                visited_best_risk[neighbor] = propagated
                affected[neighbor] = {
                    "entity_id": neighbor,
                    "propagated_risk": round(propagated, 2),
                    "depth": new_depth,
                    "path": new_path,
                }
                paths.append(new_path)
                max_depth_reached = max(max_depth_reached, new_depth)
                frontier.append((neighbor, propagated, new_depth, new_path))

    affected_list = sorted(affected.values(), key=lambda a: -a["propagated_risk"])
    highest_risk = affected_list[:10]

    return {
        "source_entity": source_entity,
        "source_risk": round(float(source_risk), 2),
        "affected_entities": affected_list,
        "propagation_paths": [a["path"] for a in affected_list],
        "propagation_depth": max_depth_reached,
        "blast_radius": len(affected_list),
        "highest_risk_downstream_entities": highest_risk,
        "config": config.__dict__,
        "disclaimer": (
            "This is a simulated risk-propagation ESTIMATE based on graph "
            "structure and configurable decay assumptions. It does NOT "
            "predict that fraud, money-laundering, or an attack will "
            "actually spread to these entities — it estimates which "
            "entities are structurally close enough to the source that "
            "elevated scrutiny may be warranted."
        ),
    }
