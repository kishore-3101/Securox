"""
Preprocessing (encoding/scaling/imputation) for Indian Banking, built on top
of the already-engineered feature table from
src.features.indian_banking_features.engineer_indian_banking_features.

Fit ONLY on the training split; the fitted ColumnTransformer is what gets
saved to artifacts/preprocessors/ and reloaded (never refit) at inference.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_COLS = [
    "account_type",
    "transaction_type",
    "transaction_direction",
    "merchant_category",
    "state",
    "transaction_status",
    "channel",
    "kyc_status",
    "loan_type",
    "time_of_day_bucket",
]

NUMERIC_COLS = [
    "transaction_amount",
    "account_balance",
    "credit_score",
    "has_loan",
    "emi_amount",
    "transaction_hour",
    "hour_sin",
    "hour_cos",
    "day_of_week",
    "is_weekend",
    "seconds_since_prev_txn",
    "cust_txn_count_so_far",
    "cust_amount_mean_so_far",
    "cust_amount_std_so_far",
    "cust_amount_max_so_far",
    "cust_txn_count_past_24h",
    "cust_amount_sum_past_24h",
    "cust_txn_count_past_7d",
    "amount_zscore_vs_history",
    "amount_ratio_vs_history_mean",
    "cust_channel_prior_count",
    "cust_channel_prior_share",
    "cust_txn_type_prior_count",
    "cust_txn_type_prior_share",
    "cust_merchant_cat_prior_count",
    "cust_merchant_cat_prior_share",
    "balance_change_vs_prev",
    "amount_to_balance_ratio",
    "cust_past_fraud_count",
    "cust_past_fraud_rate",
]


def _handle_structural_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """
    loan_type is null for ALL has_loan==0 rows (structural — there's no loan,
    so no loan_type) but is ALSO null for a subset (~10%) of has_loan==1
    rows (verified via crosstab in EDA — this is a genuine data-quality gap,
    not something we can explain away as structural). We therefore encode
    two distinct explicit categories rather than one, so the model can tell
    "no loan" apart from "has a loan but its type is unknown":
      - has_loan == 0        -> "NoLoan"
      - has_loan == 1 & null -> "UnknownLoanType"
    """
    df = df.copy()
    no_loan_mask = df["has_loan"] == 0
    unknown_mask = (df["has_loan"] == 1) & df["loan_type"].isna()
    df.loc[no_loan_mask, "loan_type"] = df.loc[no_loan_mask, "loan_type"].fillna("NoLoan")
    df.loc[unknown_mask, "loan_type"] = "UnknownLoanType"
    return df


def build_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_pipeline, CATEGORICAL_COLS),
            ("num", numeric_pipeline, NUMERIC_COLS),
        ]
    )
    return preprocessor


@dataclass
class FittedIndianBankingPreprocessor:
    preprocessor: ColumnTransformer
    output_feature_names: list


def fit_indian_banking_preprocessor(train_df: pd.DataFrame) -> FittedIndianBankingPreprocessor:
    train_df = _handle_structural_missingness(train_df)
    preprocessor = build_preprocessor()
    preprocessor.fit(train_df[CATEGORICAL_COLS + NUMERIC_COLS])
    feature_names = list(preprocessor.get_feature_names_out())
    return FittedIndianBankingPreprocessor(preprocessor, feature_names)


def transform_indian_banking(
    df: pd.DataFrame, fitted: FittedIndianBankingPreprocessor
) -> np.ndarray:
    df = _handle_structural_missingness(df)
    return fitted.preprocessor.transform(df[CATEGORICAL_COLS + NUMERIC_COLS])
