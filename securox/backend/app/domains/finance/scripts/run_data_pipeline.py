"""
End-to-end DATA PREPARATION pipeline for all three FINANCE datasets.

For each dataset: load -> engineer features -> chronological/stratified
split -> fit preprocessor on TRAIN ONLY -> transform all splits -> save
processed matrices + preprocessors + a feature dictionary.

No model training happens here.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import scipy.sparse as sp

from src.config.paths import (
    AMLSIM_PROCESSED_DIR,
    FEATURE_DICTIONARY_PATH,
    INDIAN_BANKING_PROCESSED_DIR,
    PREPROCESSORS_DIR,
    RANDOM_SEED,
    ULB_PROCESSED_DIR,
    ensure_dirs,
)
from src.data.amlsim_loader import load_amlsim
from src.data.indian_banking_loader import load_indian_banking
from src.data.preprocessing_amlsim import fit_amlsim_preprocessor, transform_amlsim
from src.data.preprocessing_indian_banking import (
    fit_indian_banking_preprocessor,
    transform_indian_banking,
)
from src.data.preprocessing_ulb import fit_ulb_preprocessor, transform_ulb
from src.data.splitting import chronological_split, stratified_split
from src.data.ulb_loader import load_ulb
from src.features.amlsim_features import (
    AMLSIM_FEATURE_COLUMNS,
    engineer_amlsim_account_features,
)
from src.features.indian_banking_features import engineer_indian_banking_features
from src.features.ulb_features import engineer_ulb_features
from src.utils.io import save_json, save_object
from src.utils.seeding import set_global_seed


def _save_split_arrays(prefix: Path, name: str, X, y, ids):
    if sp.issparse(X):
        sp.save_npz(prefix / f"{name}_X.npz", sp.csr_matrix(X))
    else:
        np.save(prefix / f"{name}_X.npy", np.asarray(X))
    y.to_csv(prefix / f"{name}_y.csv", index=False)
    ids.to_csv(prefix / f"{name}_ids.csv", index=False)


def run_indian_banking():
    print("\n--- Indian Banking: load ---")
    data = load_indian_banking()
    full_with_target = data.full.copy()

    print("--- Indian Banking: feature engineering ---")
    engineered = engineer_indian_banking_features(full_with_target)

    print("--- Indian Banking: chronological split ---")
    split = chronological_split(engineered, time_col="transaction_datetime")
    print(f"  train={len(split.train)} val={len(split.val)} test={len(split.test)}")

    print("--- Indian Banking: fit preprocessor on TRAIN only ---")
    fitted = fit_indian_banking_preprocessor(split.train)
    save_object(fitted, PREPROCESSORS_DIR / "indian_banking_preprocessor.joblib")

    for name, part in [("train", split.train), ("val", split.val), ("test", split.test)]:
        X = transform_indian_banking(part, fitted)
        y = part[["is_fraud"]].reset_index(drop=True)
        ids = part[["transaction_id", "customer_id", "transaction_datetime"]].reset_index(drop=True)
        _save_split_arrays(INDIAN_BANKING_PROCESSED_DIR, name, X, y, ids)

    return {
        "n_rows": len(engineered),
        "n_raw_features": engineered.shape[1],
        "n_processed_features": len(fitted.output_feature_names),
        "splits": {k: len(v) for k, v in zip(["train", "val", "test"], [split.train, split.val, split.test])},
        "processed_feature_names": fitted.output_feature_names,
    }


def run_ulb():
    print("\n--- ULB: load ---")
    data = load_ulb()
    full = data.full.copy()

    print("--- ULB: feature engineering ---")
    engineered = engineer_ulb_features(full)

    print("--- ULB: chronological split (by Time) ---")
    split = chronological_split(engineered, time_col="Time")
    print(f"  train={len(split.train)} val={len(split.val)} test={len(split.test)}")

    print("--- ULB: fit preprocessor on TRAIN only ---")
    fitted = fit_ulb_preprocessor(split.train)
    save_object(fitted, PREPROCESSORS_DIR / "ulb_preprocessor.joblib")

    for name, part in [("train", split.train), ("val", split.val), ("test", split.test)]:
        X = transform_ulb(part, fitted)
        y = part[["Class"]].reset_index(drop=True)
        ids = part[["row_id", "Time"]].reset_index(drop=True)
        _save_split_arrays(ULB_PROCESSED_DIR, name, X, y, ids)

    return {
        "n_rows": len(engineered),
        "n_raw_features": engineered.shape[1],
        "n_processed_features": len(fitted.output_feature_names),
        "splits": {k: len(v) for k, v in zip(["train", "val", "test"], [split.train, split.val, split.test])},
        "processed_feature_names": fitted.output_feature_names,
    }


def run_amlsim():
    print("\n--- AMLSim: load ---")
    data = load_amlsim()

    print("--- AMLSim: account-level graph feature engineering ---")
    account_features = engineer_amlsim_account_features(
        data.accounts, data.transactions, data.alert_members
    )

    print(
        "--- AMLSim: stratified split (no per-account timestamp exists in the "
        "raw simulator output, so a chronological split is not possible here; "
        "documented explicitly, not silently assumed) ---"
    )
    split = stratified_split(account_features, target_col="is_sar")
    print(f"  train={len(split.train)} val={len(split.val)} test={len(split.test)}")

    print("--- AMLSim: fit preprocessor on TRAIN only ---")
    fitted = fit_amlsim_preprocessor(split.train)
    save_object(fitted, PREPROCESSORS_DIR / "amlsim_preprocessor.joblib")

    for name, part in [("train", split.train), ("val", split.val), ("test", split.test)]:
        X = transform_amlsim(part, fitted)
        y = part[["is_sar"]].reset_index(drop=True)
        ids = part[["ACCOUNT_ID", "is_alert_member", "alert_reason"]].reset_index(drop=True)
        _save_split_arrays(AMLSIM_PROCESSED_DIR, name, X, y, ids)

    return {
        "n_accounts": len(account_features),
        "n_raw_features": account_features.shape[1],
        "n_processed_features": len(fitted.output_feature_names),
        "splits": {k: len(v) for k, v in zip(["train", "val", "test"], [split.train, split.val, split.test])},
        "processed_feature_names": fitted.output_feature_names,
        "excluded_metadata_columns": ["is_alert_member", "alert_reason", "is_sar (target)"],
    }


def build_feature_dictionary(ib_summary, ulb_summary, aml_summary):
    """Machine-readable dictionary of original -> generated features per dataset."""
    fd = {
        "indian_banking": {
            "target": "is_fraud",
            "identifiers": ["transaction_id", "customer_id"],
            "original_features": {
                "transaction_amount": {"dtype": "float64", "purpose": "raw transaction value", "temporal": False, "historical": False},
                "account_balance": {"dtype": "float64", "purpose": "account balance at time of txn", "temporal": False, "historical": False},
                "credit_score": {"dtype": "int64", "purpose": "customer credit score", "temporal": False, "historical": False},
                "has_loan": {"dtype": "int64", "purpose": "loan flag", "temporal": False, "historical": False},
                "loan_type": {"dtype": "category", "purpose": "loan category; null split into two explicit categories: 'NoLoan' when has_loan==0 (structural), 'UnknownLoanType' when has_loan==1 but type missing (data-quality gap, verified via crosstab, not assumed)", "temporal": False, "historical": False},
                "emi_amount": {"dtype": "float64", "purpose": "EMI amount, 0 when no loan", "temporal": False, "historical": False},
                "account_type": {"dtype": "category", "purpose": "account type", "temporal": False, "historical": False},
                "transaction_type": {"dtype": "category", "purpose": "payment rail used", "temporal": False, "historical": False},
                "transaction_direction": {"dtype": "category", "purpose": "debit/credit", "temporal": False, "historical": False},
                "merchant_category": {"dtype": "category", "purpose": "merchant category", "temporal": False, "historical": False},
                "state": {"dtype": "category", "purpose": "geographic state", "temporal": False, "historical": False},
                "transaction_status": {"dtype": "category", "purpose": "txn outcome status", "temporal": False, "historical": False},
                "channel": {"dtype": "category", "purpose": "channel used", "temporal": False, "historical": False},
                "kyc_status": {"dtype": "category", "purpose": "KYC status", "temporal": False, "historical": False},
                "transaction_hour": {"dtype": "int64", "purpose": "hour of day", "temporal": True, "historical": False},
            },
            "generated_features": {
                "hour_sin": {"dtype": "float64", "purpose": "cyclical encoding of hour", "temporal": True, "historical": False, "leakage_risk": "none"},
                "hour_cos": {"dtype": "float64", "purpose": "cyclical encoding of hour", "temporal": True, "historical": False, "leakage_risk": "none"},
                "time_of_day_bucket": {"dtype": "category", "purpose": "morning/afternoon/evening/night bucket", "temporal": True, "historical": False, "leakage_risk": "none"},
                "day_of_week": {"dtype": "int64", "purpose": "0=Mon..6=Sun", "temporal": True, "historical": False, "leakage_risk": "none"},
                "is_weekend": {"dtype": "int64", "purpose": "weekend flag", "temporal": True, "historical": False, "leakage_risk": "none"},
                "seconds_since_prev_txn": {"dtype": "float64", "purpose": "velocity: gap to customer's previous txn", "temporal": True, "historical": True, "leakage_risk": "none (uses only the prior txn's timestamp)"},
                "cust_txn_count_so_far": {"dtype": "int64", "purpose": "count of this customer's txns strictly before current", "temporal": True, "historical": True, "leakage_risk": "none (shift(1) applied before counting)"},
                "cust_amount_mean_so_far": {"dtype": "float64", "purpose": "expanding mean of past amounts", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_amount_std_so_far": {"dtype": "float64", "purpose": "expanding std of past amounts", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_amount_max_so_far": {"dtype": "float64", "purpose": "expanding max of past amounts", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_txn_count_past_24h": {"dtype": "float64", "purpose": "rolling count, trailing 24h, excludes current txn", "temporal": True, "historical": True, "leakage_risk": "none (amount series shifted before rolling)"},
                "cust_amount_sum_past_24h": {"dtype": "float64", "purpose": "rolling amount sum, trailing 24h, excludes current txn", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_txn_count_past_7d": {"dtype": "float64", "purpose": "rolling count, trailing 7 days, excludes current txn", "temporal": True, "historical": True, "leakage_risk": "none"},
                "amount_zscore_vs_history": {"dtype": "float64", "purpose": "deviation of current amount from past baseline", "temporal": True, "historical": True, "leakage_risk": "none"},
                "amount_ratio_vs_history_mean": {"dtype": "float64", "purpose": "current amount / past mean amount", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_channel_prior_count": {"dtype": "int64", "purpose": "prior uses of this channel by this customer", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_channel_prior_share": {"dtype": "float64", "purpose": "share of past txns using this channel", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_txn_type_prior_count": {"dtype": "int64", "purpose": "prior uses of this transaction_type", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_txn_type_prior_share": {"dtype": "float64", "purpose": "share of past txns of this type", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_merchant_cat_prior_count": {"dtype": "int64", "purpose": "prior txns in this merchant category", "temporal": True, "historical": True, "leakage_risk": "none"},
                "cust_merchant_cat_prior_share": {"dtype": "float64", "purpose": "share of past txns in this category", "temporal": True, "historical": True, "leakage_risk": "none"},
                "balance_change_vs_prev": {"dtype": "float64", "purpose": "account_balance - previous txn's balance", "temporal": True, "historical": True, "leakage_risk": "none"},
                "amount_to_balance_ratio": {"dtype": "float64", "purpose": "current amount / current balance", "temporal": False, "historical": False, "leakage_risk": "none (uses only current-row fields, not the label)"},
                "cust_past_fraud_count": {"dtype": "float64", "purpose": "count of PAST fraud-flagged txns for this customer", "temporal": True, "historical": True, "leakage_risk": "uses past is_fraud values only, via shift(1) before the expanding sum; current row's own label never included"},
                "cust_past_fraud_rate": {"dtype": "float64", "purpose": "past fraud count / past txn count", "temporal": True, "historical": True, "leakage_risk": "same as above"},
            },
            "final_processed_feature_count": ib_summary["n_processed_features"],
        },
        "ulb": {
            "target": "Class",
            "identifiers": ["row_id (synthetic, positional)"],
            "original_features": {
                **{f"V{i}": {"dtype": "float64", "purpose": "PCA-anonymized feature from publisher — no semantic meaning assumed", "temporal": False, "historical": False} for i in range(1, 29)},
                "Amount": {"dtype": "float64", "purpose": "transaction amount", "temporal": False, "historical": False},
                "Time": {"dtype": "float64", "purpose": "seconds since first transaction in dataset (not wall clock)", "temporal": True, "historical": False},
            },
            "generated_features": {
                "amount_log1p": {"dtype": "float64", "purpose": "log1p(Amount) to reduce skew", "temporal": False, "historical": False, "leakage_risk": "none"},
                "time_day_index": {"dtype": "int64", "purpose": "Time // 86400", "temporal": True, "historical": False, "leakage_risk": "none"},
                "time_hour_of_day": {"dtype": "float64", "purpose": "(Time % 86400)/3600", "temporal": True, "historical": False, "leakage_risk": "none"},
                "time_hour_sin": {"dtype": "float64", "purpose": "cyclical encoding", "temporal": True, "historical": False, "leakage_risk": "none"},
                "time_hour_cos": {"dtype": "float64", "purpose": "cyclical encoding", "temporal": True, "historical": False, "leakage_risk": "none"},
            },
            "no_customer_identifier": "This dataset has no account/customer ID, so no cross-transaction rolling/behavioral features are possible or attempted.",
            "final_processed_feature_count": ulb_summary["n_processed_features"],
        },
        "amlsim": {
            "target": "is_sar (accounts.csv IS_SAR, account-level)",
            "identifiers": ["ACCOUNT_ID"],
            "original_features": {
                "INIT_BALANCE": {"dtype": "float64", "purpose": "starting account balance", "temporal": False, "historical": False},
                "ACCOUNT_TYPE": {"dtype": "category", "purpose": "account type", "temporal": False, "historical": False},
                "COUNTRY": {"dtype": "category", "purpose": "account country", "temporal": False, "historical": False},
            },
            "generated_features": {
                "in_degree": {"dtype": "int64", "purpose": "count of incoming transaction edges", "temporal": False, "historical": False, "leakage_risk": "none — derived purely from transaction graph structure"},
                "out_degree": {"dtype": "int64", "purpose": "count of outgoing transaction edges", "temporal": False, "historical": False, "leakage_risk": "none"},
                "total_degree": {"dtype": "int64", "purpose": "in_degree + out_degree", "temporal": False, "historical": False, "leakage_risk": "none"},
                "degree_ratio": {"dtype": "float64", "purpose": "in_degree / total_degree", "temporal": False, "historical": False, "leakage_risk": "none"},
                "unique_senders": {"dtype": "int64", "purpose": "distinct accounts that sent to this account", "temporal": False, "historical": False, "leakage_risk": "none"},
                "unique_receivers": {"dtype": "int64", "purpose": "distinct accounts this account sent to", "temporal": False, "historical": False, "leakage_risk": "none"},
                "account_type_encoded": {"dtype": "int64", "purpose": "category code of ACCOUNT_TYPE", "temporal": False, "historical": False, "leakage_risk": "none"},
                "country_encoded": {"dtype": "int64", "purpose": "category code of COUNTRY", "temporal": False, "historical": False, "leakage_risk": "none"},
            },
            "excluded_as_leakage": {
                "is_alert_member": "True iff account appears in alert_members.csv — near-perfectly correlated with the label by construction of the simulator; kept as metadata only, never a model input.",
                "alert_reason": "The alert typology (fan_in/fan_out/etc) — only defined for already-labeled SAR accounts; metadata only.",
            },
            "no_transaction_level_timestamp": "The raw tmp/1K/transactions.csv we have access to contains only id/src/dst/ttype — no amount or step/time column — so this is an account-level static graph problem here, not a per-transaction temporal one. A chronological split was therefore not possible; a stratified split on the label was used instead (see splitting.py).",
            "not_reused_from_reference": "aml_detection/ bundled inside the same zip was NOT read, imported, or used to derive any of the above.",
            "final_processed_feature_count": aml_summary["n_processed_features"],
        },
    }
    return fd


def main():
    set_global_seed(RANDOM_SEED)
    ensure_dirs()

    ib_summary = run_indian_banking()
    ulb_summary = run_ulb()
    aml_summary = run_amlsim()

    fd = build_feature_dictionary(ib_summary, ulb_summary, aml_summary)
    save_json(fd, FEATURE_DICTIONARY_PATH)

    summary = {
        "indian_banking": ib_summary,
        "ulb": ulb_summary,
        "amlsim": aml_summary,
    }
    save_json(summary, INDIAN_BANKING_PROCESSED_DIR.parent / "pipeline_run_summary.json")

    print("\n=== DATA PREPARATION PIPELINE COMPLETE ===")
    print(f"Feature dictionary written to {FEATURE_DICTIONARY_PATH}")
    return summary


if __name__ == "__main__":
    main()
