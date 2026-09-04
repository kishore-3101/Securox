"""
Loads the already-processed (feature-engineered + preprocessed) train/val/
test splits written by scripts/run_data_pipeline.py. This module does not
recompute or alter any feature engineering — it only reads the .npy/.csv
artifacts already validated in the data-preparation stage.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ProcessedSplit:
    X: np.ndarray
    y: np.ndarray
    ids: pd.DataFrame


@dataclass
class ProcessedDataset:
    train: ProcessedSplit
    val: ProcessedSplit
    test: ProcessedSplit
    feature_names: list


def _load_split(processed_dir: Path, name: str, target_col: str) -> ProcessedSplit:
    X = np.load(processed_dir / f"{name}_X.npy")
    y = pd.read_csv(processed_dir / f"{name}_y.csv")[target_col].to_numpy()
    ids = pd.read_csv(processed_dir / f"{name}_ids.csv")
    if len(X) != len(y):
        raise RuntimeError(
            f"{processed_dir}/{name}: X has {len(X)} rows but y has {len(y)} — "
            "processed artifacts are inconsistent, refusing to proceed."
        )
    return ProcessedSplit(X=X, y=y, ids=ids)


def load_processed_dataset(processed_dir: Path, target_col: str, feature_names: list) -> ProcessedDataset:
    train = _load_split(processed_dir, "train", target_col)
    val = _load_split(processed_dir, "val", target_col)
    test = _load_split(processed_dir, "test", target_col)

    for split_name, split in [("train", train), ("val", val), ("test", test)]:
        if split.X.shape[1] != len(feature_names):
            raise RuntimeError(
                f"{processed_dir}/{split_name}_X.npy has {split.X.shape[1]} columns "
                f"but the fitted preprocessor reports {len(feature_names)} feature "
                "names — these must match exactly."
            )

    return ProcessedDataset(train=train, val=val, test=test, feature_names=feature_names)
