"""
Shared evaluation utilities used by both the Indian Banking and ULB fraud
models (Isolation Forest + XGBoost). Every number returned here is computed
directly from sklearn on the actual predictions/labels passed in — nothing
is hardcoded.
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class ClassificationReport:
    threshold: float
    precision: float
    recall: float
    f1: float
    f2: float
    roc_auc: Optional[float]
    pr_auc: Optional[float]
    tp: int
    fp: int
    fn: int
    tn: int
    n_positive: int
    n_total: int

    def to_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "f2": self.f2,
            "roc_auc": self.roc_auc,
            "pr_auc": self.pr_auc,
            "confusion_matrix": {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn},
            "n_positive": self.n_positive,
            "n_total": self.n_total,
        }


def evaluate_at_threshold(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> ClassificationReport:
    y_true = np.asarray(y_true).astype(int)
    y_pred = (np.asarray(y_score) >= threshold).astype(int)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    f2 = fbeta_score(y_true, y_pred, beta=2, zero_division=0)

    try:
        roc_auc = roc_auc_score(y_true, y_score) if len(np.unique(y_true)) > 1 else None
    except ValueError:
        roc_auc = None
    try:
        pr_auc = average_precision_score(y_true, y_score) if len(np.unique(y_true)) > 1 else None
    except ValueError:
        pr_auc = None

    return ClassificationReport(
        threshold=float(threshold),
        precision=float(precision),
        recall=float(recall),
        f1=float(f1),
        f2=float(f2),
        roc_auc=float(roc_auc) if roc_auc is not None else None,
        pr_auc=float(pr_auc) if pr_auc is not None else None,
        tp=int(tp),
        fp=int(fp),
        fn=int(fn),
        tn=int(tn),
        n_positive=int(y_true.sum()),
        n_total=int(len(y_true)),
    )


def search_best_threshold(
    y_true: np.ndarray,
    y_score: np.ndarray,
    metric: str = "f1",
    n_thresholds: int = 200,
) -> tuple:
    """
    Grid-search a threshold over the observed score range, on WHATEVER split
    is passed in (caller must pass validation data, never test, for tuning).
    Returns (best_threshold, best_report, full_search_table).
    """
    y_true = np.asarray(y_true).astype(int)
    y_score = np.asarray(y_score)
    lo, hi = np.percentile(y_score, 0.1), np.percentile(y_score, 99.9)
    candidates = np.linspace(lo, hi, n_thresholds)

    search_table = []
    best = None
    best_report = None
    for t in candidates:
        report = evaluate_at_threshold(y_true, y_score, t)
        score = getattr(report, metric)
        search_table.append({"threshold": float(t), "precision": report.precision, "recall": report.recall, "f1": report.f1})
        if score is not None and (best is None or score > best):
            best = score
            best_report = report

    if best_report is None:
        # degenerate case (e.g. no positives) -> default mid threshold
        best_report = evaluate_at_threshold(y_true, y_score, float(np.median(y_score)))

    return best_report.threshold, best_report, search_table
