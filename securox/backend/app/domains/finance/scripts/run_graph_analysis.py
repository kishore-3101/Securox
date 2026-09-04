"""
Runs the transaction-graph analysis + graph-risk scoring over the actual
AMLSim account graph, and saves a summary. No model training happens here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.paths import ARTIFACTS_DIR, ensure_dirs
from src.data.amlsim_loader import load_amlsim
from src.models.graph.transaction_graph import load_graph
from src.risk_engine.graph_risk_scoring import score_all_entities
from src.utils.io import save_json

GRAPH_METRICS_DIR = ARTIFACTS_DIR / "metrics"


def main():
    ensure_dirs()
    data = load_amlsim()
    graph = load_graph(data.transactions, data.accounts)

    n_nodes = graph.graph.number_of_nodes()
    n_edges = graph.graph.number_of_edges()
    components = graph.connected_components("weak")
    hubs = graph.identify_hubs(top_n=10)
    suspicious = graph.find_suspicious_nodes(top_n=20)

    summary = {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "n_weakly_connected_components": len(components),
        "largest_component_size": max((len(c) for c in components), default=0),
        "top_hubs_by_total_degree": [{"account_id": int(a), "total_degree": int(v)} for a, v in hubs],
        "n_structurally_suspicious_accounts": len(suspicious),
        "structurally_suspicious_account_ids": suspicious["ACCOUNT_ID"].astype(int).tolist(),
    }
    save_json(summary, GRAPH_METRICS_DIR / "amlsim_graph_summary.json")

    print("=== AMLSim transaction graph summary ===")
    for k, v in summary.items():
        if isinstance(v, list) and len(v) > 5:
            print(f"{k}: [{len(v)} items]")
        else:
            print(f"{k}: {v}")

    # Score every account for graph-risk evidence and save alongside the
    # ground-truth label ONLY for reporting/inspection (never fed back as a
    # model feature — this is evidence output, not training data).
    scores = score_all_entities(graph)
    label_by_account = dict(zip(data.account_labels["ACCOUNT_ID"], data.account_labels["is_sar"]))
    for s in scores:
        s["is_sar_ground_truth_for_reference_only"] = bool(label_by_account.get(s["entity_id"], False))
    save_json(scores, GRAPH_METRICS_DIR / "amlsim_graph_risk_scores.json")

    # Quick, honest sanity check: do higher graph-risk scores correlate at
    # all with the ground-truth SAR label? (reported, not tuned to)
    import numpy as np
    sar_scores = [s["graph_risk_score"] for s in scores if s["is_sar_ground_truth_for_reference_only"]]
    non_sar_scores = [s["graph_risk_score"] for s in scores if not s["is_sar_ground_truth_for_reference_only"]]
    print(f"\nMean graph_risk_score for SAR accounts: {np.mean(sar_scores):.2f} (n={len(sar_scores)})")
    print(f"Mean graph_risk_score for non-SAR accounts: {np.mean(non_sar_scores):.2f} (n={len(non_sar_scores)})")

    print(f"\nSaved -> {GRAPH_METRICS_DIR / 'amlsim_graph_summary.json'}")
    print(f"Saved -> {GRAPH_METRICS_DIR / 'amlsim_graph_risk_scores.json'}")
    return summary


if __name__ == "__main__":
    main()
