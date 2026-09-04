"""
Loader for the Indian Banking Transactions dataset.

Responsibilities only: read the raw CSV, validate its schema, do minimal
safe dtype coercion, and hand back a clean DataFrame plus the identifier /
target columns split out. No feature engineering happens here.
"""
from dataclasses import dataclass

import pandas as pd

from src.config.paths import INDIAN_BANKING_RAW
from src.data.schemas import (
    INDIAN_BANKING_COLUMNS,
    INDIAN_BANKING_ID_COLS,
    INDIAN_BANKING_TARGET,
    validate_columns,
)


@dataclass
class IndianBankingData:
    """Container that keeps identifiers, features, and target explicitly separate."""

    full: pd.DataFrame          # everything, for convenience / EDA
    ids: pd.DataFrame           # transaction_id, customer_id
    features: pd.DataFrame      # all columns except ids + target
    target: pd.Series           # is_fraud


def load_indian_banking(path=INDIAN_BANKING_RAW) -> IndianBankingData:
    if not path.exists():
        raise FileNotFoundError(
            f"Indian Banking raw file not found at {path}. "
            "Raw data must not be moved from data/raw/indian_banking/."
        )

    df = pd.read_csv(path)

    try:
        validate_columns(df.columns, INDIAN_BANKING_COLUMNS, "Indian Banking")
    except Exception as e:
        raise RuntimeError(f"Indian Banking schema validation failed: {e}") from e

    # Minimal, non-destructive dtype coercion (no imputation/encoding here —
    # that belongs to preprocessing, not loading).
    df = df.copy()
    df["transaction_id"] = df["transaction_id"].astype(str)
    df["customer_id"] = df["customer_id"].astype(str)

    if df["transaction_id"].duplicated().any():
        n_dupes = int(df["transaction_id"].duplicated().sum())
        raise RuntimeError(
            f"Indian Banking loader found {n_dupes} duplicate transaction_id "
            "values — refusing to proceed silently."
        )

    if INDIAN_BANKING_TARGET not in df.columns:
        raise RuntimeError("Indian Banking target column 'is_fraud' missing.")

    ids = df[INDIAN_BANKING_ID_COLS].copy()
    target = df[INDIAN_BANKING_TARGET].astype(int).copy()
    features = df.drop(columns=INDIAN_BANKING_ID_COLS + [INDIAN_BANKING_TARGET])

    return IndianBankingData(full=df, ids=ids, features=features, target=target)
