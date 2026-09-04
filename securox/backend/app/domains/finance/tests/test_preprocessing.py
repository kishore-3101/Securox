import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.data.preprocessing_indian_banking import (
    fit_indian_banking_preprocessor,
    transform_indian_banking,
)
from src.features.indian_banking_features import engineer_indian_banking_features
from src.data.preprocessing_ulb import fit_ulb_preprocessor, transform_ulb
from src.features.ulb_features import engineer_ulb_features
from src.data.preprocessing_amlsim import fit_amlsim_preprocessor, transform_amlsim
from src.features.amlsim_features import AMLSIM_FEATURE_COLUMNS


def _toy_indian_banking_df(n=20):
    rng = np.random.default_rng(0)
    dates = pd.date_range("2023-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {
            "transaction_id": [f"T{i}" for i in range(n)],
            "customer_id": [f"C{i % 3}" for i in range(n)],
            "transaction_date": dates.strftime("%Y-%m-%d"),
            "transaction_time": dates.strftime("%H:%M"),
            "account_type": ["Savings"] * n,
            "transaction_type": ["UPI"] * n,
            "transaction_amount": rng.uniform(10, 1000, n),
            "transaction_direction": ["Debit"] * n,
            "account_balance": rng.uniform(1000, 5000, n),
            "merchant_category": ["Retail"] * n,
            "state": ["Karnataka"] * n,
            "credit_score": rng.integers(600, 800, n),
            "has_loan": [0] * n,
            "loan_type": [None] * n,
            "emi_amount": [0.0] * n,
            "transaction_status": ["Success"] * n,
            "channel": ["Mobile_App"] * n,
            "kyc_status": ["Verified"] * n,
            "is_fraud": rng.integers(0, 2, n),
            "transaction_hour": dates.hour,
        }
    )


def test_indian_banking_preprocessor_fit_transform_shape_consistency():
    df = engineer_indian_banking_features(_toy_indian_banking_df())
    train, test = df.iloc[:15], df.iloc[15:]
    fitted = fit_indian_banking_preprocessor(train)
    X_train = transform_indian_banking(train, fitted)
    X_test = transform_indian_banking(test, fitted)
    assert X_train.shape[1] == X_test.shape[1] == len(fitted.output_feature_names)


def test_indian_banking_preprocessor_not_refit_on_test():
    """Transforming test data must not change the fitted preprocessor's
    learned statistics (e.g. StandardScaler mean)."""
    df = engineer_indian_banking_features(_toy_indian_banking_df())
    train, test = df.iloc[:15], df.iloc[15:]
    fitted = fit_indian_banking_preprocessor(train)
    num_transformer = fitted.preprocessor.named_transformers_["num"]
    mean_before = num_transformer.named_steps["scale"].mean_.copy()
    transform_indian_banking(test, fitted)
    mean_after = num_transformer.named_steps["scale"].mean_
    assert np.allclose(mean_before, mean_after)


def test_ulb_preprocessor_passthrough_columns_untouched():
    n = 30
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {**{f"V{i}": rng.normal(size=n) for i in range(1, 29)}, "Time": np.arange(n) * 100.0, "Amount": rng.uniform(1, 500, n), "Class": rng.integers(0, 2, n)}
    )
    df = engineer_ulb_features(df)
    fitted = fit_ulb_preprocessor(df)
    X = transform_ulb(df, fitted)
    # passthrough V columns should appear unchanged at the tail of the output
    v_start = len(fitted.output_feature_names) - 28
    np.testing.assert_allclose(X[:, v_start:], df[[f"V{i}" for i in range(1, 29)]].values)


def test_amlsim_preprocessor_only_uses_declared_feature_columns():
    df = pd.DataFrame(
        {
            **{c: np.random.rand(10) for c in AMLSIM_FEATURE_COLUMNS},
            "is_sar": np.random.randint(0, 2, 10),
            "is_alert_member": [False] * 10,
            "alert_reason": [None] * 10,
        }
    )
    fitted = fit_amlsim_preprocessor(df)
    X = transform_amlsim(df, fitted)
    assert X.shape == (10, len(AMLSIM_FEATURE_COLUMNS))
