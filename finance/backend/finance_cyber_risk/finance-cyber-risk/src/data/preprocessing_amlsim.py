"""
Preprocessing for AMLSim account-level features. Purely numeric structural
features (graph degrees + account attributes) -> impute + scale. The
metadata columns (is_alert_member, alert_reason, is_sar) are never passed
into this transformer.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.features.amlsim_features import AMLSIM_FEATURE_COLUMNS


@dataclass
class FittedAMLSimPreprocessor:
    pipeline: Pipeline
    output_feature_names: list


def build_preprocessor() -> Pipeline:
    return Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )


def fit_amlsim_preprocessor(train_df: pd.DataFrame) -> FittedAMLSimPreprocessor:
    pipeline = build_preprocessor()
    pipeline.fit(train_df[AMLSIM_FEATURE_COLUMNS])
    return FittedAMLSimPreprocessor(pipeline, list(AMLSIM_FEATURE_COLUMNS))


def transform_amlsim(df: pd.DataFrame, fitted: FittedAMLSimPreprocessor) -> np.ndarray:
    return fitted.pipeline.transform(df[AMLSIM_FEATURE_COLUMNS])
