"""
Supervised XGBoost fraud classifier.

Imbalance handling: we compare a small set of `scale_pos_weight` candidates
(1x = no reweighting, sqrt of the imbalance ratio, and the full imbalance
ratio) by training one model per candidate and selecting whichever scores
best on the VALIDATION split's PR-AUC (appropriate for severe imbalance —
ROC-AUC is misleadingly optimistic here). We deliberately do NOT apply
SMOTE to this temporal transaction data (a project rule): oversampling
minority rows would fabricate synthetic points out of chronological order
and could leak the local structure of nearby real fraud cases across the
train/val/test time boundary.

Test data is only ever used once, at the very end, after both the
imbalance-handling strategy and the classification threshold have already
been fixed using train/validation only.
"""
from dataclasses import dataclass
from typing import Optional

import numpy as np
import xgboost as xgb

from src.config.paths import RANDOM_SEED
from src.evaluation.metrics import evaluate_at_threshold, search_best_threshold


@dataclass
class ScalePosWeightCandidate:
    name: str
    scale_pos_weight: float
    val_pr_auc: Optional[float]
    val_roc_auc: Optional[float]


@dataclass
class FittedXGBoostFraudModel:
    model: xgb.XGBClassifier
    scale_pos_weight_used: float
    scale_pos_weight_search: list
    threshold: float
    threshold_metric: str
    feature_names: list


def _make_model(scale_pos_weight: float, seed: int = RANDOM_SEED) -> xgb.XGBClassifier:
    return xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="aucpr",
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        n_jobs=-1,
        tree_method="hist",
    )


def compare_imbalance_strategies(
    X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray
) -> list:
    n_pos = int(y_train.sum())
    n_neg = int(len(y_train) - n_pos)
    ratio = n_neg / max(n_pos, 1)

    candidates = {
        "no_reweighting (scale_pos_weight=1)": 1.0,
        "sqrt_imbalance_ratio": float(np.sqrt(ratio)),
        "full_imbalance_ratio": float(ratio),
    }

    results = []
    for name, spw in candidates.items():
        model = _make_model(spw)
        model.fit(X_train, y_train)
        val_prob = model.predict_proba(X_val)[:, 1]
        report = evaluate_at_threshold(y_val, val_prob, threshold=0.5)
        results.append(
            ScalePosWeightCandidate(
                name=name,
                scale_pos_weight=spw,
                val_pr_auc=report.pr_auc,
                val_roc_auc=report.roc_auc,
            )
        )
    return results


def fit_and_tune_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    feature_names: list,
    threshold_metric: str = "f1",
) -> FittedXGBoostFraudModel:
    candidates = compare_imbalance_strategies(X_train, y_train, X_val, y_val)
    best_candidate = max(candidates, key=lambda c: (c.val_pr_auc or -1))

    final_model = _make_model(best_candidate.scale_pos_weight)
    final_model.fit(X_train, y_train)

    val_prob = final_model.predict_proba(X_val)[:, 1]
    best_threshold, _best_report, _search_table = search_best_threshold(
        y_val, val_prob, metric=threshold_metric
    )

    return FittedXGBoostFraudModel(
        model=final_model,
        scale_pos_weight_used=best_candidate.scale_pos_weight,
        scale_pos_weight_search=[c.__dict__ for c in candidates],
        threshold=best_threshold,
        threshold_metric=threshold_metric,
        feature_names=feature_names,
    )


def predict_proba(fitted: FittedXGBoostFraudModel, X: np.ndarray) -> np.ndarray:
    return fitted.model.predict_proba(X)[:, 1]


def predict(fitted: FittedXGBoostFraudModel, X: np.ndarray) -> dict:
    prob = predict_proba(fitted, X)
    label = (prob >= fitted.threshold).astype(int)
    return {"fraud_probability": prob, "predicted_class": label}
