"""
AML (Anti-Money-Laundering) account-level classification.

Target: `is_sar` from accounts.csv (IS_SAR), i.e. whether the simulator
flagged this account as part of a Suspicious Activity Report pattern.
Features: the leakage-safe structural feature set built in
src/features/amlsim_features.py (graph degree stats + account attributes
only — never `is_alert_member`/`alert_reason`/`is_sar` itself).

Two models are trained and compared:
  - Logistic Regression (simple, interpretable baseline)
  - XGBoost (higher-capacity comparison)

Both use class_weight='balanced' / scale_pos_weight, respectively, since
alert accounts are a small minority (~5% here) — no SMOTE.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
import xgboost as xgb

from src.config.paths import RANDOM_SEED
from src.evaluation.metrics import evaluate_at_threshold, search_best_threshold


@dataclass
class FittedAMLModel:
    model_name: str
    model: object
    threshold: float
    threshold_metric: str
    feature_names: list


def train_logistic_regression_baseline(
    X_train: np.ndarray, y_train: np.ndarray, seed: int = RANDOM_SEED
) -> LogisticRegression:
    model = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        random_state=seed,
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost_aml(
    X_train: np.ndarray, y_train: np.ndarray, seed: int = RANDOM_SEED
) -> xgb.XGBClassifier:
    n_pos = int(y_train.sum())
    n_neg = int(len(y_train) - n_pos)
    scale_pos_weight = n_neg / max(n_pos, 1)
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="aucpr",
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        n_jobs=-1,
        tree_method="hist",
    )
    model.fit(X_train, y_train)
    return model


def _predict_proba_generic(model, X: np.ndarray) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def fit_and_tune_aml_model(
    model_name: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list,
    threshold_metric: str = "f1",
) -> FittedAMLModel:
    if model_name == "logistic_regression":
        model = train_logistic_regression_baseline(X_train, y_train)
    elif model_name == "xgboost":
        model = train_xgboost_aml(X_train, y_train)
    else:
        raise ValueError(f"Unknown AML model_name: {model_name}")

    val_prob = _predict_proba_generic(model, X_val)
    best_threshold, _report, _table = search_best_threshold(y_val, val_prob, metric=threshold_metric)

    return FittedAMLModel(
        model_name=model_name,
        model=model,
        threshold=best_threshold,
        threshold_metric=threshold_metric,
        feature_names=feature_names,
    )


def predict_proba(fitted: FittedAMLModel, X: np.ndarray) -> np.ndarray:
    return _predict_proba_generic(fitted.model, X)


def predict(fitted: FittedAMLModel, X: np.ndarray) -> dict:
    prob = predict_proba(fitted, X)
    label = (prob >= fitted.threshold).astype(int)
    return {"sar_probability": prob, "predicted_class": label}
