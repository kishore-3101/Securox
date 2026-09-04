"""
Loader for the ULB Credit Card Fraud dataset.

This dataset has no natural row identifier, so we synthesize a positional
`row_id` purely for traceability (joining features back to predictions
later) — it is never used as a model feature.
"""
from dataclasses import dataclass

import pandas as pd

from src.config.paths import ULB_RAW
from src.data.schemas import ULB_COLUMNS, ULB_TARGET, validate_columns


@dataclass
class ULBData:
    full: pd.DataFrame
    ids: pd.DataFrame       # row_id (synthetic, positional)
    features: pd.DataFrame  # Time, V1..V28, Amount
    target: pd.Series       # Class


def load_ulb(path=ULB_RAW) -> ULBData:
    if not path.exists():
        raise FileNotFoundError(
            f"ULB raw file not found at {path}. Raw data must not be moved "
            "from data/raw/ulb/."
        )

    df = pd.read_csv(path)

    try:
        validate_columns(df.columns, ULB_COLUMNS, "ULB Credit Card Fraud")
    except Exception as e:
        raise RuntimeError(f"ULB schema validation failed: {e}") from e

    df = df.copy()
    df.insert(0, "row_id", range(len(df)))

    if df.isna().any().any():
        na_cols = df.columns[df.isna().any()].tolist()
        raise RuntimeError(
            f"ULB loader found unexpected nulls in columns {na_cols}; "
            "original inspection found none."
        )

    ids = df[["row_id"]].copy()
    target = df[ULB_TARGET].astype(int).copy()
    features = df.drop(columns=["row_id", ULB_TARGET])

    return ULBData(full=df, ids=ids, features=features, target=target)
