"""
Isolation Forest anomaly detector.

Strict rule: is_fraud/Class is NEVER passed to `.fit()`. Labels are used
only afterwards, to (a) evaluate the model and (b) pick an operating
threshold on the anomaly score using the VALIDATION split.
"""
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from src.config.paths import RANDOM_SEED
from src.evaluation.metrics import search_best_threshold


@dataclass
class FittedIsolationForest:
    model: IsolationForest
    threshold: float
    threshold_metric: str
    feature_names: list


def train_isolation_forest(
    X_train: np.ndarray,
    n_estimators: int = 200,
    max_samples: str = "auto",
    seed: int = RANDOM_SEED,
) -> IsolationForest:
    """Fit with sklearn defaults for `contamination` ('auto') specifically so
    that no label-derived fraud-rate estimate ever touches model fitting."""
    model = IsolationForest(
        n_estimators=n_estimators,
        max_samples=max_samples,
        contamination="auto",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train)
    return model


def anomaly_scores(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    """Higher = more anomalous (sklearn's decision_function is the opposite
    sign, so we flip it for an intuitive 'anomaly_score')."""
    return -model.decision_function(X)


def anomaly_labels(scores: np.ndarray, threshold: float) -> np.ndarray:
    return (scores >= threshold).astype(int)


def fit_and_tune_isolation_forest(
    X_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list,
    threshold_metric: str = "f1",
) -> FittedIsolationForest:
    model = train_isolation_forest(X_train)
    val_scores = anomaly_scores(model, X_val)
    best_threshold, best_report, _search_table = search_best_threshold(
        y_val, val_scores, metric=threshold_metric
    )
    return FittedIsolationForest(
        model=model,
        threshold=best_threshold,
        threshold_metric=threshold_metric,
        feature_names=feature_names,
    )


def predict(fitted: FittedIsolationForest, X: np.ndarray) -> dict:
    scores = anomaly_scores(fitted.model, X)
    labels = anomaly_labels(scores, fitted.threshold)
    return {"anomaly_score": scores, "anomaly_label": labels}
