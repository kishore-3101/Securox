"""
Targeted tests proving that a transaction's engineered features never see
information from transactions that happen AFTER it (for the same customer),
and that the target is never used as a direct input feature.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.features.indian_banking_features import engineer_indian_banking_features
from src.data.preprocessing_indian_banking import CATEGORICAL_COLS, NUMERIC_COLS
from src.data.preprocessing_ulb import PASSTHROUGH_COLS as ULB_PASSTHROUGH
from src.data.preprocessing_ulb import SCALED_COLS as ULB_SCALED


def _toy_indian_banking_df():
    """
    Hand-built customer history where we know the right answer:
    customer C1 makes 3 transactions of amount 100, 300, 200 in that order.
    """
    return pd.DataFrame(
        {
            "transaction_id": ["T1", "T2", "T3", "T4"],
            "customer_id": ["C1", "C1", "C1", "C2"],
            "transaction_date": ["2023-01-01", "2023-01-01", "2023-01-02", "2023-01-01"],
            "transaction_time": ["10:00", "11:00", "10:00", "09:00"],
            "account_type": ["Savings"] * 4,
            "transaction_type": ["UPI"] * 4,
            "transaction_amount": [100.0, 300.0, 200.0, 50.0],
            "transaction_direction": ["Debit"] * 4,
            "account_balance": [1000.0, 900.0, 700.0, 500.0],
            "merchant_category": ["Retail"] * 4,
            "state": ["Karnataka"] * 4,
            "credit_score": [700, 700, 700, 650],
            "has_loan": [0, 0, 0, 0],
            "loan_type": [None, None, None, None],
            "emi_amount": [0.0, 0.0, 0.0, 0.0],
            "transaction_status": ["Success"] * 4,
            "channel": ["Mobile_App"] * 4,
            "kyc_status": ["Verified"] * 4,
            "is_fraud": [0, 1, 0, 0],
            "transaction_hour": [10, 11, 10, 9],
        }
    )


def test_first_transaction_has_no_history():
    df = _toy_indian_banking_df()
    out = engineer_indian_banking_features(df)
    first_txn = out[out["transaction_id"] == "T1"].iloc[0]
    assert first_txn["cust_txn_count_so_far"] == 0
    assert first_txn["cust_amount_mean_so_far"] == 0
    assert first_txn["cust_past_fraud_count"] == 0


def test_second_transaction_only_sees_first():
    df = _toy_indian_banking_df()
    out = engineer_indian_banking_features(df)
    t2 = out[out["transaction_id"] == "T2"].iloc[0]
    # T2's baseline mean must equal T1's own amount (100), NOT include T2's own 300
    assert t2["cust_amount_mean_so_far"] == pytest.approx(100.0)
    assert t2["cust_txn_count_so_far"] == 1
    # T1 was not fraud, so past fraud count for T2 must be 0
    assert t2["cust_past_fraud_count"] == 0


def test_third_transaction_does_not_see_future_fraud_flag():
    df = _toy_indian_banking_df()
    out = engineer_indian_banking_features(df)
    t3 = out[out["transaction_id"] == "T3"].iloc[0]
    # T3 comes after T2 (which WAS fraud) -> past fraud count must be 1
    assert t3["cust_past_fraud_count"] == 1
    # mean of past amounts (T1=100, T2=300) = 200, must NOT include T3's own 200
    assert t3["cust_amount_mean_so_far"] == pytest.approx(200.0)


def test_customers_do_not_leak_into_each_other():
    df = _toy_indian_banking_df()
    out = engineer_indian_banking_features(df)
    t4 = out[out["transaction_id"] == "T4"].iloc[0]  # customer C2, first txn
    assert t4["cust_txn_count_so_far"] == 0
    assert t4["cust_amount_mean_so_far"] == 0


def test_chronological_ordering_within_customer_is_enforced():
    """Shuffle the input rows; output engineered history must be identical
    to the sorted-input case, proving the function sorts internally rather
    than trusting input row order."""
    df = _toy_indian_banking_df()
    shuffled = df.sample(frac=1.0, random_state=1).reset_index(drop=True)

    out_sorted = engineer_indian_banking_features(df).set_index("transaction_id")
    out_shuffled = engineer_indian_banking_features(shuffled).set_index("transaction_id")

    for txn_id in df["transaction_id"]:
        assert out_sorted.loc[txn_id, "cust_amount_mean_so_far"] == pytest.approx(
            out_shuffled.loc[txn_id, "cust_amount_mean_so_far"]
        )
        assert (
            out_sorted.loc[txn_id, "cust_past_fraud_count"]
            == out_shuffled.loc[txn_id, "cust_past_fraud_count"]
        )


def test_target_column_excluded_from_indian_banking_feature_columns():
    assert "is_fraud" not in CATEGORICAL_COLS
    assert "is_fraud" not in NUMERIC_COLS


def test_target_column_excluded_from_ulb_feature_columns():
    assert "Class" not in ULB_PASSTHROUGH
    assert "Class" not in ULB_SCALED


def test_engineered_history_features_are_monotonic_count():
    """cust_txn_count_so_far must strictly increase (by 1) within a customer
    when sorted chronologically — a basic sanity property of a past-only
    running count."""
    df = _toy_indian_banking_df()
    out = engineer_indian_banking_features(df)
    c1 = out[out["customer_id"] == "C1"].sort_values("transaction_datetime")
    counts = c1["cust_txn_count_so_far"].tolist()
    assert counts == [0, 1, 2]
