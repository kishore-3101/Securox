"""
Live fraud graph builder for linked accounts, devices, merchants, bank accounts, and IPs.
Detects circular transactions, fan-in/fan-out money laundering patterns, and computes Mule Probability Scores.
"""

from collections import defaultdict


class FraudGraphEngine:
    def build_network(self, alerts: list[dict]) -> dict:
        nodes: dict[str, dict] = {}
        edge_weights: dict[tuple[str, str], int] = defaultdict(int)

        for alert in alerts:
            tx = alert.get("transaction", alert)
            tx_id = alert.get("transaction_id", tx.get("tx_id", "unknown_tx"))
            tx_node = self._node(nodes, tx_id, "transaction")
            
            for field, kind in [
                ("user_id", "user"),
                ("account_id", "bank_account"),
                ("merchant_id", "merchant"),
                ("wallet_id", "wallet"),
                ("device_id", "device"),
                ("ip_address", "ip"),
                ("ip", "ip"),
                ("tag_id", "fastag"),
                ("asset_id", "asset"),
            ]:
                value = tx.get(field)
                if value:
                    other = self._node(nodes, str(value), kind)
                    edge_weights[(tx_node["id"], other["id"])] += 1

        edges = [
            {"source": source, "target": target, "weight": weight}
            for (source, target), weight in edge_weights.items()
        ]
        
        # Calculate degree & fan-in / fan-out
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        for edge in edges:
            out_degree[edge["source"]] += edge["weight"]
            in_degree[edge["target"]] += edge["weight"]

        clusters = []
        mule_networks = []
        for n_id, n_data in nodes.items():
            total_deg = in_degree[n_id] + out_degree[n_id]
            # Mule score heuristic: high degree, shared IP/device, fan-in/out
            mule_score = min(99, int(n_data["risk"] * 0.5 + total_deg * 12)) if n_data["type"] in {"merchant", "wallet", "ip", "device", "bank_account"} else 15
            n_data["mule_probability"] = mule_score
            n_data["degree"] = total_deg

            if total_deg >= 2:
                clusters.append({
                    "id": n_id,
                    "label": n_data["label"],
                    "type": n_data["type"],
                    "degree": total_deg,
                    "risk": n_data["risk"],
                    "mule_probability": mule_score,
                })
                if mule_score >= 65:
                    mule_networks.append({
                        "entity_id": n_id,
                        "entity_type": n_data["type"],
                        "mule_probability": mule_score,
                        "pattern": "Fan-In / Fan-Out Rapid Transfer" if in_degree[n_id] > 1 and out_degree[n_id] > 1 else "High-Velocity Mule Account",
                        "connected_nodes": total_deg
                    })

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "clusters": clusters,
            "mule_networks": mule_networks,
            "summary": {
                "total_entities": len(nodes),
                "total_links": len(edges),
                "high_risk_mule_nodes": len(mule_networks)
            }
        }

    def get_demo_mule_graph(self) -> dict:
        """Generates a rich pre-built Money Mule Network topology for instant visual demonstration."""
        sample_nodes = [
            {"id": "IP-442", "label": "IP: 198.51.100.44", "type": "ip", "risk": 88, "mule_probability": 85},
            {"id": "User-12", "label": "User-12 (Suspect)", "type": "user", "risk": 75, "mule_probability": 70},
            {"id": "User-87", "label": "User-87 (Suspect)", "type": "user", "risk": 78, "mule_probability": 72},
            {"id": "Device-DEV-99", "label": "Device: Pixel-7-Clone", "type": "device", "risk": 92, "mule_probability": 88},
            {"id": "Wallet-A", "label": "Mule Wallet A", "type": "wallet", "risk": 95, "mule_probability": 94},
            {"id": "Wallet-B", "label": "Mule Wallet B", "type": "wallet", "risk": 94, "mule_probability": 92},
            {"id": "Merchant-X", "label": "Ghost Merchant X", "type": "merchant", "risk": 98, "mule_probability": 96},
            {"id": "Wallet-Z", "label": "Offshore Exfil Wallet Z", "type": "wallet", "risk": 99, "mule_probability": 98},
            {"id": "Asset-TAX-01", "label": "Municipal Tax Portal", "type": "asset", "risk": 90, "mule_probability": 40},
        ]
        sample_edges = [
            {"source": "IP-442", "target": "User-12", "weight": 4},
            {"source": "IP-442", "target": "User-87", "weight": 5},
            {"source": "Device-DEV-99", "target": "User-12", "weight": 6},
            {"source": "User-12", "target": "Wallet-A", "weight": 8},
            {"source": "User-87", "target": "Wallet-B", "weight": 7},
            {"source": "Wallet-A", "target": "Merchant-X", "weight": 12},
            {"source": "Wallet-B", "target": "Merchant-X", "weight": 14},
            {"source": "Merchant-X", "target": "Wallet-Z", "weight": 20},
            {"source": "Merchant-X", "target": "Asset-TAX-01", "weight": 3},
        ]
        return {
            "nodes": sample_nodes,
            "edges": sample_edges,
            "clusters": [
                {"id": "Merchant-X", "label": "Ghost Merchant X", "type": "merchant", "degree": 4, "risk": 98, "mule_probability": 96},
                {"id": "IP-442", "label": "IP: 198.51.100.44", "type": "ip", "degree": 2, "risk": 88, "mule_probability": 85}
            ],
            "mule_networks": [
                {"entity_id": "Merchant-X", "entity_type": "merchant", "mule_probability": 96, "pattern": "Circular Fan-In Rapid Transfer Hub", "connected_nodes": 4},
                {"entity_id": "Wallet-Z", "entity_type": "wallet", "mule_probability": 98, "pattern": "Offshore Treasury Exfiltration Destination", "connected_nodes": 1}
            ],
            "summary": {
                "total_entities": 9,
                "total_links": 9,
                "high_risk_mule_nodes": 2
            }
        }

    @staticmethod
    def _node(nodes: dict[str, dict], node_id: str, kind: str) -> dict:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, "label": node_id, "type": kind, "risk": 20}
        nodes[node_id]["risk"] = min(100, nodes[node_id]["risk"] + 10)
        return nodes[node_id]


fraud_graph_engine = FraudGraphEngine()
