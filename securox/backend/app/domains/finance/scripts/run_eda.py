"""
Reusable EDA over the three raw datasets (read-only). Saves:
- plots (PNG) -> artifacts/eda/
- numeric/statistical summaries (JSON) -> artifacts/metrics/eda/

Does not fit or train anything. Every number here comes from pandas/numpy
computed directly on the loaded data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.config.paths import EDA_DIR, EDA_METRICS_DIR, ensure_dirs
from src.data.amlsim_loader import load_amlsim
from src.data.indian_banking_loader import load_indian_banking
from src.data.ulb_loader import load_ulb
from src.features.amlsim_features import engineer_amlsim_account_features
from src.features.indian_banking_features import engineer_indian_banking_features
from src.utils.io import save_json


def eda_indian_banking():
    print("--- EDA: Indian Banking ---")
    data = load_indian_banking()
    df = engineer_indian_banking_features(data.full)

    report = {
        "shape": list(df.shape),
        "class_balance": df["is_fraud"].value_counts().to_dict(),
        "class_balance_pct": (df["is_fraud"].value_counts(normalize=True) * 100).round(4).to_dict(),
        "missing_values": {k: int(v) for k, v in df.isna().sum().items() if v > 0},
        "loan_type_missingness_breakdown": {
            "has_loan_0_null_count": int(((df["has_loan"] == 0) & df["loan_type"].isna()).sum()),
            "has_loan_0_total": int((df["has_loan"] == 0).sum()),
            "has_loan_1_null_count": int(((df["has_loan"] == 1) & df["loan_type"].isna()).sum()),
            "has_loan_1_total": int((df["has_loan"] == 1).sum()),
            "interpretation": "loan_type is null for 100% of has_loan==0 rows "
            "(structural: no loan -> no type) AND for a subset of has_loan==1 "
            "rows (a genuine data-quality gap, not structural). Both cases "
            "are handled as distinct explicit categories in preprocessing "
            "('NoLoan' vs 'UnknownLoanType') rather than assumed identical.",
        },
        "amount_stats": df["transaction_amount"].describe().to_dict(),
        "amount_outliers_iqr": _iqr_outlier_count(df["transaction_amount"]),
        "fraud_rate_by_channel": (
            df.groupby("channel")["is_fraud"].mean().sort_values(ascending=False).round(5).to_dict()
        ),
        "fraud_rate_by_transaction_type": (
            df.groupby("transaction_type")["is_fraud"].mean().sort_values(ascending=False).round(5).to_dict()
        ),
        "fraud_rate_by_merchant_category": (
            df.groupby("merchant_category")["is_fraud"].mean().sort_values(ascending=False).round(5).to_dict()
        ),
        "fraud_rate_by_state": (
            df.groupby("state")["is_fraud"].mean().sort_values(ascending=False).round(5).to_dict()
        ),
        "fraud_rate_by_hour": (
            df.groupby("transaction_hour")["is_fraud"].mean().sort_values(ascending=False).round(5).to_dict()
        ),
        "customer_txn_count_stats": df.groupby("customer_id").size().describe().to_dict(),
    }
    save_json(report, EDA_METRICS_DIR / "indian_banking_eda.json")

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    df["is_fraud"].value_counts().plot(kind="bar", ax=axes[0, 0], title="Class balance (is_fraud)")
    np.log1p(df["transaction_amount"]).hist(bins=60, ax=axes[0, 1])
    axes[0, 1].set_title("log1p(transaction_amount) distribution")
    df.groupby("transaction_hour")["is_fraud"].mean().plot(ax=axes[1, 0], title="Fraud rate by hour")
    df.groupby("channel")["is_fraud"].mean().sort_values().plot(kind="barh", ax=axes[1, 1], title="Fraud rate by channel")
    fig.tight_layout()
    fig.savefig(EDA_DIR / "indian_banking_overview.png", dpi=110)
    plt.close(fig)

    return report


def eda_ulb():
    print("--- EDA: ULB ---")
    data = load_ulb()
    df = data.full

    v_cols = [f"V{i}" for i in range(1, 29)]
    report = {
        "shape": list(df.shape),
        "class_balance": df["Class"].value_counts().to_dict(),
        "class_balance_pct": (df["Class"].value_counts(normalize=True) * 100).round(6).to_dict(),
        "missing_values_total": int(df.isna().sum().sum()),
        "amount_stats": df["Amount"].describe().to_dict(),
        "amount_outliers_iqr": _iqr_outlier_count(df["Amount"]),
        "time_stats": df["Time"].describe().to_dict(),
        "v_columns_statistical_summary_no_semantic_meaning": df[v_cols].describe().T[
            ["mean", "std", "min", "max"]
        ].round(4).to_dict(orient="index"),
        "amount_mean_by_class": df.groupby("Class")["Amount"].mean().round(2).to_dict(),
    }
    save_json(report, EDA_METRICS_DIR / "ulb_eda.json")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    df["Class"].value_counts().plot(kind="bar", ax=axes[0], title="Class balance")
    axes[0].set_yscale("log")
    np.log1p(df["Amount"]).hist(bins=60, ax=axes[1])
    axes[1].set_title("log1p(Amount) distribution")
    df[v_cols].std().plot(kind="bar", ax=axes[2], title="Std dev of V1-V28 (no meaning assumed)")
    fig.tight_layout()
    fig.savefig(EDA_DIR / "ulb_overview.png", dpi=110)
    plt.close(fig)

    return report


def eda_amlsim():
    print("--- EDA: AMLSim ---")
    data = load_amlsim()
    account_features = engineer_amlsim_account_features(
        data.accounts, data.transactions, data.alert_members
    )

    report = {
        "n_accounts": len(data.accounts),
        "n_transactions_edges": len(data.transactions),
        "n_alert_members_rows": len(data.alert_members),
        "label_balance_is_sar": data.account_labels["is_sar"].value_counts().to_dict(),
        "label_balance_pct": (
            data.account_labels["is_sar"].value_counts(normalize=True) * 100
        ).round(3).to_dict(),
        "alert_typologies": data.alert_members["reason"].value_counts().to_dict(),
        "account_type_distribution": data.accounts["ACCOUNT_TYPE"].value_counts().to_dict(),
        "country_distribution": data.accounts["COUNTRY"].value_counts().to_dict(),
        "init_balance_stats": data.accounts["INIT_BALANCE"].describe().to_dict(),
        "graph_degree_stats": account_features[
            ["in_degree", "out_degree", "total_degree"]
        ].describe().to_dict(),
        "degree_stats_by_label": account_features.groupby("is_sar")[
            ["in_degree", "out_degree", "total_degree"]
        ].mean().round(3).to_dict(),
        "note": "transactions.csv (raw simulator output available here) has no "
        "amount/timestamp column, so no per-transaction amount/time EDA is "
        "possible for AMLSim in this workspace — only graph/account-level EDA.",
    }
    save_json(report, EDA_METRICS_DIR / "amlsim_eda.json")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    account_features["is_sar"].value_counts().plot(kind="bar", ax=axes[0], title="Account label balance (is_sar)")
    account_features.boxplot(column="total_degree", by="is_sar", ax=axes[1])
    axes[1].set_title("Total degree by label")
    fig.suptitle("")
    fig.tight_layout()
    fig.savefig(EDA_DIR / "amlsim_overview.png", dpi=110)
    plt.close(fig)

    return report


def _iqr_outlier_count(series: pd.Series) -> dict:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_outliers = int(((series < lower) | (series > upper)).sum())
    return {"q1": float(q1), "q3": float(q3), "iqr": float(iqr), "n_outliers": n_outliers}


def main():
    ensure_dirs()
    ib = eda_indian_banking()
    ulb = eda_ulb()
    aml = eda_amlsim()
    print("\n=== EDA COMPLETE ===")
    print(f"Plots -> {EDA_DIR}")
    print(f"Stat reports -> {EDA_METRICS_DIR}")
    return {"indian_banking": ib, "ulb": ulb, "amlsim": aml}


if __name__ == "__main__":
    main()
