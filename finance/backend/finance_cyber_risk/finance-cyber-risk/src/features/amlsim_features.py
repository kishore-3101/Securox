"""
Account-level feature engineering for AMLSim, computed independently from
the raw simulator files (accounts.csv + transactions.csv) via networkx.

Deliberately NOT reused from the bundled `aml_detection/` reference
sub-project — this is our own computation, from our own loader.

Leakage note: `alert_members.csv` / `normal_models.csv` describe *why* an
account was labeled SAR/non-SAR by the simulator (reason/typology, model
assignment) — using membership in alert_members as an input feature would
leak the label almost by definition (an account appears there essentially
because it IS part of a SAR pattern). Those tables are therefore kept only
as label/metadata references (see `alert_reason` and `is_alert_member`
columns below, which are excluded from the model-facing feature set) and
never merged into the feature columns used for training.
"""
import networkx as nx
import numpy as np
import pandas as pd

# Columns considered safe, structural, model-facing features (graph + account
# attributes only — no alert/typology/label-adjacent information).
AMLSIM_FEATURE_COLUMNS = [
    "in_degree",
    "out_degree",
    "total_degree",
    "degree_ratio",
    "unique_senders",
    "unique_receivers",
    "init_balance",
    "account_type_encoded",
    "country_encoded",
]

# Columns kept for reference/analysis only — never fed to a model.
AMLSIM_METADATA_COLUMNS = [
    "is_alert_member",
    "alert_reason",
    "is_sar",
]


def build_transaction_graph(transactions: pd.DataFrame) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    g.add_edges_from(zip(transactions["src"], transactions["dst"]))
    return g


def compute_graph_features(accounts: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:
    g = build_transaction_graph(transactions)
    account_ids = accounts["ACCOUNT_ID"].tolist()

    rows = []
    for acc in account_ids:
        in_deg = g.in_degree(acc) if acc in g else 0
        out_deg = g.out_degree(acc) if acc in g else 0
        senders = set(u for u, _ in g.in_edges(acc)) if acc in g else set()
        receivers = set(v for _, v in g.out_edges(acc)) if acc in g else set()
        total = in_deg + out_deg
        rows.append(
            {
                "ACCOUNT_ID": acc,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "total_degree": total,
                "degree_ratio": (in_deg / total) if total > 0 else 0.0,
                "unique_senders": len(senders),
                "unique_receivers": len(receivers),
            }
        )
    return pd.DataFrame(rows)


def engineer_amlsim_account_features(
    accounts: pd.DataFrame,
    transactions: pd.DataFrame,
    alert_members: pd.DataFrame,
) -> pd.DataFrame:
    graph_feats = compute_graph_features(accounts, transactions)

    merged = accounts.merge(graph_feats, on="ACCOUNT_ID", how="left")
    merged["init_balance"] = merged["INIT_BALANCE"].astype(float)

    # simple, transparent categorical encodings (no target used)
    merged["account_type_encoded"] = merged["ACCOUNT_TYPE"].astype("category").cat.codes
    merged["country_encoded"] = merged["COUNTRY"].astype("category").cat.codes

    # metadata only (never a model feature)
    alert_flags = (
        alert_members.groupby("accountID")["reason"]
        .agg(lambda x: x.mode().iat[0] if not x.mode().empty else None)
        .rename("alert_reason")
    )
    merged = merged.merge(
        alert_flags, left_on="ACCOUNT_ID", right_index=True, how="left"
    )
    merged["is_alert_member"] = merged["alert_reason"].notna()
    merged["is_sar"] = merged["IS_SAR"].astype(bool)

    keep_cols = ["ACCOUNT_ID"] + AMLSIM_FEATURE_COLUMNS + AMLSIM_METADATA_COLUMNS
    return merged[keep_cols]
