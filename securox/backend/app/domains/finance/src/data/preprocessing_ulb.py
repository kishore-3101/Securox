"""
Preprocessing for ULB. V1-V28 are NOT re-scaled or re-transformed (they are
already a PCA-whitened-ish output from the publisher and we do not re-apply
PCA or assume anything about their scale/meaning). We only scale the
human-interpretable, unbounded columns: Amount (already log1p'd upstream in
feature engineering) and the derived Time features.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

V_COLS = [f"V{i}" for i in range(1, 29)]
SCALED_COLS = ["amount_log1p", "time_hour_sin", "time_hour_cos", "time_day_index"]
PASSTHROUGH_COLS = V_COLS  # untouched


@dataclass
class FittedULBPreprocessor:
    preprocessor: ColumnTransformer
    output_feature_names: list


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("scaled", StandardScaler(), SCALED_COLS),
            ("passthrough", "passthrough", PASSTHROUGH_COLS),
        ]
    )


def fit_ulb_preprocessor(train_df: pd.DataFrame) -> FittedULBPreprocessor:
    preprocessor = build_preprocessor()
    preprocessor.fit(train_df[SCALED_COLS + PASSTHROUGH_COLS])
    names = SCALED_COLS + PASSTHROUGH_COLS
    return FittedULBPreprocessor(preprocessor, names)


def transform_ulb(df: pd.DataFrame, fitted: FittedULBPreprocessor) -> np.ndarray:
    return fitted.preprocessor.transform(df[SCALED_COLS + PASSTHROUGH_COLS])
