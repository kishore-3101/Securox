import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.data.splitting import chronological_split, stratified_split


def test_chronological_split_preserves_order_and_no_overlap():
    df = pd.DataFrame({"t": pd.date_range("2023-01-01", periods=100, freq="h"), "v": range(100)})
    shuffled = df.sample(frac=1.0, random_state=0).reset_index(drop=True)
    split = chronological_split(shuffled, time_col="t", train_frac=0.6, val_frac=0.2)

    assert len(split.train) + len(split.val) + len(split.test) == 100
    assert split.train["t"].max() <= split.val["t"].min()
    assert split.val["t"].max() <= split.test["t"].min()


def test_chronological_split_sizes_roughly_match_fractions():
    df = pd.DataFrame({"t": pd.date_range("2023-01-01", periods=1000, freq="min"), "v": range(1000)})
    split = chronological_split(df, time_col="t", train_frac=0.7, val_frac=0.15)
    assert 690 <= len(split.train) <= 710
    assert 140 <= len(split.val) <= 160


def test_stratified_split_keeps_all_rows_and_stratifies():
    n = 500
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"y": rng.choice([0, 1], size=n, p=[0.9, 0.1]), "x": rng.normal(size=n)})
    split = stratified_split(df, target_col="y", train_frac=0.7, val_frac=0.15)
    assert len(split.train) + len(split.val) + len(split.test) == n
    for part in [split.train, split.val, split.test]:
        rate = part["y"].mean()
        assert 0.03 < rate < 0.20  # roughly preserved, generous tolerance for small splits
