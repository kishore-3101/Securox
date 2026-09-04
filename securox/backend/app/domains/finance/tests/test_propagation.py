import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from src.models.graph.transaction_graph import load_graph
from src.risk_engine.propagation import PropagationConfig, propagate_risk


@pytest.fixture
def chain_graph_data():
    """A simple directed chain 1->2->3->4->5 plus an isolated node 6, so
    distance-decay is easy to verify by hand."""
    accounts = pd.DataFrame(
        {
            "ACCOUNT_ID": [1, 2, 3, 4, 5, 6],
            "CUSTOMER_ID": [f"C{i}" for i in range(6)],
            "INIT_BALANCE": [100.0] * 6,
            "COUNTRY": ["US"] * 6,
            "ACCOUNT_TYPE": ["I"] * 6,
            "IS_SAR": ["false"] * 6,
            "BANK_ID": ["bank"] * 6,
        }
    )
    transactions = pd.DataFrame(
        {"id": [0, 1, 2, 3], "src": [1, 2, 3, 4], "dst": [2, 3, 4, 5], "ttype": ["TRANSFER"] * 4}
    )
    return accounts, transactions


def test_propagation_from_missing_entity_returns_empty(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    result = propagate_risk(g, 999, source_risk=80.0)
    assert result["blast_radius"] == 0
    assert result["affected_entities"] == []
    assert "disclaimer" in result


def test_propagation_respects_max_depth(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    config = PropagationConfig(max_depth=2, decay_per_hop=0.9, min_risk_to_propagate=0.01)
    result = propagate_risk(g, 1, source_risk=100.0, config=config)
    assert result["propagation_depth"] <= 2
    depths = [a["depth"] for a in result["affected_entities"]]
    assert max(depths) <= 2


def test_propagation_risk_decays_with_distance(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    config = PropagationConfig(max_depth=4, decay_per_hop=0.5, min_risk_to_propagate=0.001)
    result = propagate_risk(g, 1, source_risk=100.0, config=config)
    by_entity = {a["entity_id"]: a for a in result["affected_entities"]}
    # further nodes in the chain must have depth >= closer nodes, and
    # propagated risk must be non-increasing with depth along this simple chain
    assert by_entity[2]["depth"] < by_entity[3]["depth"] < by_entity[4]["depth"]
    assert by_entity[2]["propagated_risk"] >= by_entity[3]["propagated_risk"] >= by_entity[4]["propagated_risk"]


def test_propagation_stops_below_min_risk_threshold(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    config = PropagationConfig(max_depth=10, decay_per_hop=0.1, min_risk_to_propagate=50.0)
    result = propagate_risk(g, 1, source_risk=100.0, config=config)
    # decay_per_hop=0.1 means risk drops below 50 after the very first hop
    # (100 * 0.1 * relationship/criticality factors < 50), so nothing distant should appear
    assert result["propagation_depth"] <= 1


def test_blast_radius_matches_affected_entities_count(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    result = propagate_risk(g, 1, source_risk=100.0)
    assert result["blast_radius"] == len(result["affected_entities"])


def test_isolated_node_has_no_propagation(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    result = propagate_risk(g, 6, source_risk=90.0)
    assert result["blast_radius"] == 0


def test_zero_source_risk_propagates_nothing(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    result = propagate_risk(g, 1, source_risk=0.0)
    assert result["blast_radius"] == 0


def test_propagation_config_is_included_in_output(chain_graph_data):
    accounts, transactions = chain_graph_data
    g = load_graph(transactions, accounts)
    config = PropagationConfig(max_depth=2)
    result = propagate_risk(g, 1, source_risk=90.0, config=config)
    assert result["config"]["max_depth"] == 2
