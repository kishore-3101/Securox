"""
Transaction graph over AMLSim accounts.

Account = node. Transaction = directed edge, carrying only what the raw
simulator output actually gives us: `id` (transaction id) and `ttype`
(transaction type). No amount or timestamp is invented anywhere in this
module — the underlying tmp/1K/transactions.csv genuinely has none.

A MultiDiGraph is used (not a simple DiGraph) because the raw data can
contain more than one transaction between the same ordered pair of
accounts, and each should remain a distinct edge/transaction record.
"""
from dataclasses import dataclass, field
from typing import Iterable, Optional

import networkx as nx
import pandas as pd

# Above this many nodes, betweenness/closeness centrality (both O(V*E) or
# worse) are skipped by default to keep this "hackathon-friendly" rather
# than accidentally hanging on a much bigger future AMLSim run.
EXPENSIVE_METRIC_NODE_LIMIT = 5000


class TransactionGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    # ------------------------------------------------------------- building

    def load_from_transactions(
        self, transactions: pd.DataFrame, accounts: Optional[pd.DataFrame] = None
    ) -> "TransactionGraph":
        """Build the graph from the raw AMLSim transactions table (id, src,
        dst, ttype) and, optionally, add any known accounts with no
        transactions yet as isolated nodes so they aren't silently absent
        from node-level feature output."""
        if accounts is not None:
            self.graph.add_nodes_from(accounts["ACCOUNT_ID"].tolist())

        for row in transactions.itertuples(index=False):
            self.add_transaction(row.src, row.dst, transaction_id=row.id, ttype=row.ttype)
        return self

    def add_transaction(self, src, dst, transaction_id, ttype: Optional[str] = None) -> None:
        """Add a single transaction as a directed edge. Only structural
        fields available in the raw data are stored — no amount/timestamp."""
        self.graph.add_edge(src, dst, key=transaction_id, transaction_id=transaction_id, ttype=ttype)

    # ------------------------------------------------------------- lookups

    def find_neighbors(self, node, direction: str = "both") -> set:
        if node not in self.graph:
            return set()
        if direction == "in":
            return set(u for u, _ in self.graph.in_edges(node))
        if direction == "out":
            return set(v for _, v in self.graph.out_edges(node))
        if direction == "both":
            return self.find_neighbors(node, "in") | self.find_neighbors(node, "out")
        raise ValueError("direction must be 'in', 'out', or 'both'")

    def find_paths(self, source, target, cutoff: int = 4, max_paths: int = 20) -> list:
        """All simple directed paths from source to target, up to `cutoff`
        hops. Capped at `max_paths` to stay cheap on denser graphs — this is
        exploratory tracing, not exhaustive enumeration."""
        if source not in self.graph or target not in self.graph:
            return []
        simple_graph = nx.DiGraph(self.graph)  # collapse parallel edges for path search
        paths = []
        try:
            for path in nx.all_simple_paths(simple_graph, source, target, cutoff=cutoff):
                paths.append(path)
                if len(paths) >= max_paths:
                    break
        except nx.NodeNotFound:
            return []
        return paths

    # --------------------------------------------------------- node metrics

    def node_degree_features(self, node) -> dict:
        if node not in self.graph:
            return {
                "in_degree": 0, "out_degree": 0, "total_degree": 0,
                "degree_ratio": 0.0, "unique_senders": 0, "unique_receivers": 0,
            }
        in_deg = self.graph.in_degree(node)
        out_deg = self.graph.out_degree(node)
        total = in_deg + out_deg
        senders = self.find_neighbors(node, "in")
        receivers = self.find_neighbors(node, "out")
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": total,
            "degree_ratio": (in_deg / total) if total > 0 else 0.0,
            "unique_senders": len(senders),
            "unique_receivers": len(receivers),
        }

    def calculate_node_features(self, compute_expensive: Optional[bool] = None) -> pd.DataFrame:
        """
        Bulk node-level feature table for every node currently in the graph.

        `compute_expensive`: whether to also compute PageRank, betweenness
        centrality, closeness centrality, and clustering coefficient. These
        are all documented AMLSim-style graph metrics but are more costly;
        by default they're computed only when the graph is small enough
        (<= EXPENSIVE_METRIC_NODE_LIMIT nodes) to keep this fast for a
        hackathon-scale run, and skipped (with a printed note) otherwise.
        """
        nodes = list(self.graph.nodes())
        n = len(nodes)
        if compute_expensive is None:
            compute_expensive = n <= EXPENSIVE_METRIC_NODE_LIMIT

        rows = [{"ACCOUNT_ID": node, **self.node_degree_features(node)} for node in nodes]
        df = pd.DataFrame(rows).set_index("ACCOUNT_ID")

        if not compute_expensive:
            reason = (
                f"{n} nodes exceeds EXPENSIVE_METRIC_NODE_LIMIT={EXPENSIVE_METRIC_NODE_LIMIT}"
                if n > EXPENSIVE_METRIC_NODE_LIMIT
                else "compute_expensive=False was explicitly requested"
            )
            print(f"[TransactionGraph] Skipping PageRank/betweenness/closeness/clustering ({reason}).")
            for col in ["pagerank", "betweenness_centrality", "closeness_centrality", "clustering_coefficient"]:
                df[col] = None
            return df.reset_index()

        simple_digraph = nx.DiGraph(self.graph)
        pagerank = nx.pagerank(simple_digraph) if n > 0 else {}
        betweenness = nx.betweenness_centrality(simple_digraph) if n > 0 else {}
        closeness = nx.closeness_centrality(simple_digraph) if n > 0 else {}
        # clustering coefficient is defined on undirected simple graphs
        undirected = nx.Graph(simple_digraph)
        clustering = nx.clustering(undirected) if n > 0 else {}

        df["pagerank"] = df.index.map(pagerank).astype(float)
        df["betweenness_centrality"] = df.index.map(betweenness).astype(float)
        df["closeness_centrality"] = df.index.map(closeness).astype(float)
        df["clustering_coefficient"] = df.index.map(clustering).astype(float)

        return df.reset_index()

    # --------------------------------------------------------- global views

    def connected_components(self, kind: str = "weak") -> list:
        """List of node sets. `kind='weak'` (default) treats direction as
        irrelevant for reachability grouping — the standard choice for
        finding clusters of related accounts in a directed transaction
        graph; `kind='strong'` requires mutual directed reachability."""
        if kind == "weak":
            return [set(c) for c in nx.weakly_connected_components(self.graph)]
        if kind == "strong":
            return [set(c) for c in nx.strongly_connected_components(self.graph)]
        raise ValueError("kind must be 'weak' or 'strong'")

    def component_size_for_node(self, node) -> int:
        if node not in self.graph:
            return 0
        for component in self.connected_components("weak"):
            if node in component:
                return len(component)
        return 0

    def identify_hubs(self, top_n: int = 10, metric: str = "total_degree") -> list:
        """Top-N nodes by a chosen structural metric. `metric` must be a
        column produced by calculate_node_features (degree-based metrics
        are always available; pagerank/centrality only if computed)."""
        features = self.calculate_node_features()
        if metric not in features.columns:
            raise ValueError(f"Unknown metric '{metric}'. Available: {list(features.columns)}")
        top = features.dropna(subset=[metric]).sort_values(metric, ascending=False).head(top_n)
        return list(zip(top["ACCOUNT_ID"], top[metric]))

    def find_suspicious_nodes(
        self,
        fan_in_percentile: float = 95.0,
        fan_out_percentile: float = 95.0,
        top_n: int = 20,
    ) -> pd.DataFrame:
        """
        Purely STRUCTURAL flagging — no SAR/alert labels are used here (that
        would just be re-reading the ground truth, not detecting anything).
        Flags accounts with unusually high fan-in and/or fan-out relative to
        the rest of the current graph, which is the generic shape AML
        layering/fan-in/fan-out typologies produce.
        """
        features = self.calculate_node_features(compute_expensive=False)
        if features.empty:
            return features
        in_threshold = features["in_degree"].quantile(fan_in_percentile / 100.0)
        out_threshold = features["out_degree"].quantile(fan_out_percentile / 100.0)

        features["high_fan_in"] = features["in_degree"] >= in_threshold
        features["high_fan_out"] = features["out_degree"] >= out_threshold
        features["structural_risk_flag"] = features["high_fan_in"] | features["high_fan_out"]

        suspicious = features[features["structural_risk_flag"]].copy()
        suspicious = suspicious.sort_values("total_degree", ascending=False).head(top_n)
        return suspicious.reset_index(drop=True)

    def local_network_risk(self, node, suspicious_node_ids: Optional[set] = None) -> dict:
        """
        Aggregate 1-hop neighborhood signal for a single node: how many of
        its direct neighbors are themselves structurally suspicious (per
        find_suspicious_nodes, or a caller-supplied set — e.g. accounts
        already known to be SAR-labeled, if the caller explicitly wants
        that lens), plus the size of its connected component.
        """
        if suspicious_node_ids is None:
            suspicious_node_ids = set(self.find_suspicious_nodes()["ACCOUNT_ID"])

        neighbors = self.find_neighbors(node, "both")
        suspicious_neighbors = neighbors & suspicious_node_ids
        return {
            "node": node,
            "neighbor_count": len(neighbors),
            "suspicious_neighbor_count": len(suspicious_neighbors),
            "suspicious_neighbors": sorted(suspicious_neighbors),
            "suspicious_neighbor_ratio": (
                len(suspicious_neighbors) / len(neighbors) if neighbors else 0.0
            ),
            "connected_component_size": self.component_size_for_node(node),
        }


def load_graph(transactions: pd.DataFrame, accounts: Optional[pd.DataFrame] = None) -> TransactionGraph:
    return TransactionGraph().load_from_transactions(transactions, accounts)
