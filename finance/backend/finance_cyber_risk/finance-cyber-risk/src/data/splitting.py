"""
Splitting utilities. Time-based data must be split chronologically (never
shuffled) to avoid leaking future information into training.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from src.config.paths import RANDOM_SEED


@dataclass
class Split:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def chronological_split(
    df: pd.DataFrame, time_col: str, train_frac: float = 0.7, val_frac: float = 0.15
) -> Split:
    df_sorted = df.sort_values(time_col).reset_index(drop=True)
    n = len(df_sorted)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))

    train = df_sorted.iloc[:train_end]
    val = df_sorted.iloc[train_end:val_end]
    test = df_sorted.iloc[val_end:]

    # Guard rail: verify no overlap and strictly increasing time boundaries.
    if len(train) and len(val):
        assert train[time_col].max() <= val[time_col].min(), "train/val time overlap"
    if len(val) and len(test):
        assert val[time_col].max() <= test[time_col].min(), "val/test time overlap"

    return Split(train, val, test)


def stratified_split(
    df: pd.DataFrame,
    target_col: str,
    train_frac: float = 0.7,
    val_frac: float = 0.15,
    seed: int = RANDOM_SEED,
) -> Split:
    """
    Used only where no valid chronological ordering exists (e.g. AMLSim
    account-level features have no per-account timestamp in the raw
    simulator output we have). Stratifies on the target to keep class
    balance roughly consistent across splits.
    """
    train, temp = train_test_split(
        df, train_size=train_frac, stratify=df[target_col], random_state=seed
    )
    relative_val_frac = val_frac / (1 - train_frac)
    val, test = train_test_split(
        temp, train_size=relative_val_frac, stratify=temp[target_col], random_state=seed
    )
    return Split(train, val, test)
