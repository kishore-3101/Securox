import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from src.models.graph.transaction_graph import TransactionGraph, load_graph
from src.risk_engine.graph_risk_scoring import GraphRiskConfig, score_all_entities, score_entity


@pytest.fixture
def toy_graph_data():
    """
    Hand-built fixture, small enough to reason about by hand:

        1 -> 2, 1 -> 3, 1 -> 4          (account 1 fans out to 2,3,4)
        2 -> 5, 3 -> 5, 4 -> 5          (accounts 2,3,4 fan in to 5 -- classic fan-in/fan-out shape around 5)
        6 -> 7                          (a totally separate, low-degree pair)
        8 (isolated account, no transactions)
    """
    accounts = pd.DataFrame(
        {
            "ACCOUNT_ID": [1, 2, 3, 4, 5, 6, 7, 8],
            "CUSTOMER_ID": [f"C{i}" for i in range(8)],
            "INIT_BALANCE": [100.0] * 8,
            "COUNTRY": ["US"] * 8,
            "ACCOUNT_TYPE": ["I"] * 8,
            "IS_SAR": ["false"] * 8,
            "BANK_ID": ["bank"] * 8,
        }
    )
    transactions = pd.DataFrame(
        {
            "id": list(range(7)),
            "src": [1, 1, 1, 2, 3, 4, 6],
            "dst": [2, 3, 4, 5, 5, 5, 7],
            "ttype": ["TRANSFER"] * 7,
        }
    )
    return accounts, transactions


def test_graph_construction_node_and_edge_counts(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    assert g.graph.number_of_nodes() == 8
    assert g.graph.number_of_edges() == 7


def test_add_transaction_increments_edges(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    before = g.graph.number_of_edges()
    g.add_transaction(src=8, dst=1, transaction_id=999, ttype="TRANSFER")
    assert g.graph.number_of_edges() == before + 1
    assert g.graph.has_edge(8, 1)


def test_node_degree_features_match_hand_computation(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    feats = g.node_degree_features(5)
    assert feats["in_degree"] == 3   # from 2, 3, 4
    assert feats["out_degree"] == 0
    assert feats["unique_senders"] == 3

    feats1 = g.node_degree_features(1)
    assert feats1["out_degree"] == 3  # to 2, 3, 4
    assert feats1["in_degree"] == 0


def test_isolated_node_has_zero_degree(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    feats = g.node_degree_features(8)
    assert feats["total_degree"] == 0


def test_calculate_node_features_covers_all_nodes(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    df = g.calculate_node_features()
    assert set(df["ACCOUNT_ID"]) == set(accounts["ACCOUNT_ID"])
    # graph is tiny, so expensive metrics (pagerank etc.) should be computed
    assert df["pagerank"].notna().all()


def test_find_neighbors_directions(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    assert g.find_neighbors(1, "out") == {2, 3, 4}
    assert g.find_neighbors(5, "in") == {2, 3, 4}
    assert g.find_neighbors(1, "both") == {2, 3, 4}


def test_find_paths_between_entities(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    paths = g.find_paths(1, 5)
    assert [1, 2, 5] in paths
    assert [1, 3, 5] in paths
    assert [1, 4, 5] in paths
    # no path should exist between disconnected components
    assert g.find_paths(1, 7) == []


def test_identify_hubs_ranks_correctly(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    hubs = g.identify_hubs(top_n=2, metric="total_degree")
    top_ids = [h[0] for h in hubs]
    # account 1 (out_degree 3) and account 5 (in_degree 3) are the two highest-degree nodes
    assert set(top_ids) == {1, 5}


def test_connected_components_weak(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    components = g.connected_components("weak")
    sizes = sorted(len(c) for c in components)
    # {1,2,3,4,5} size 5, {6,7} size 2, {8} size 1
    assert sizes == [1, 2, 5]


def test_find_suspicious_nodes_flags_the_fan_in_fan_out_hub(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    suspicious = g.find_suspicious_nodes(fan_in_percentile=50, fan_out_percentile=50, top_n=10)
    flagged_ids = set(suspicious["ACCOUNT_ID"])
    # 1 (high fan-out) and 5 (high fan-in) must both surface with a 50th-pctile threshold on this tiny graph
    assert {1, 5}.issubset(flagged_ids)


def test_local_network_risk_counts_suspicious_neighbors(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    suspicious_ids = {1, 5}
    risk = g.local_network_risk(2, suspicious_node_ids=suspicious_ids)
    # account 2's neighbors are {1, 5} -- both suspicious
    assert risk["suspicious_neighbor_count"] == 2
    assert risk["suspicious_neighbor_ratio"] == 1.0
    assert risk["connected_component_size"] == 5


# ----------------------------------------------------------- risk scoring


def test_graph_risk_score_is_bounded_0_100(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    result = score_entity(g, 5, config=GraphRiskConfig(fan_in_percentile=50, fan_out_percentile=50))
    assert 0.0 <= result["graph_risk_score"] <= 100.0
    assert isinstance(result["risk_factors"], list) and len(result["risk_factors"]) > 0


def test_graph_risk_score_higher_for_hub_than_isolated_node(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    config = GraphRiskConfig(fan_in_percentile=50, fan_out_percentile=50)
    hub_result = score_entity(g, 5, config=config)
    isolated_result = score_entity(g, 8, config=config)
    assert hub_result["graph_risk_score"] > isolated_result["graph_risk_score"]


def test_graph_risk_score_missing_entity_returns_zero(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    result = score_entity(g, 12345)
    assert result["graph_risk_score"] == 0.0
    assert result["connected_component_size"] == 0


def test_score_all_entities_covers_every_node(toy_graph_data):
    accounts, transactions = toy_graph_data
    g = load_graph(transactions, accounts)
    scores = score_all_entities(g)
    assert {s["entity_id"] for s in scores} == set(accounts["ACCOUNT_ID"])
    for s in scores:
        assert 0.0 <= s["graph_risk_score"] <= 100.0
