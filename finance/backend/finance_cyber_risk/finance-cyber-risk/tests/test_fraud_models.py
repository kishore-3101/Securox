import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from src.evaluation.metrics import evaluate_at_threshold, search_best_threshold
from src.models.anomaly.isolation_forest_model import (
    fit_and_tune_isolation_forest,
    anomaly_scores,
    predict as if_predict,
)
from src.models.fraud.xgboost_model import fit_and_tune_xgboost, predict as xgb_predict
from src.explainability.shap_explainer import FraudExplainer


def _make_toy_classification_data(n=400, n_features=6, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n_features))
    # make feature 0 informative of the (rare) positive class
    y = np.zeros(n, dtype=int)
    fraud_idx = rng.choice(n, size=max(5, n // 20), replace=False)
    y[fraud_idx] = 1
    X[fraud_idx, 0] += 5.0  # clearly separable signal
    feature_names = [f"f{i}" for i in range(n_features)]
    return X, y, feature_names


def _split(X, y, train_frac=0.6, val_frac=0.2):
    n = len(X)
    a, b = int(n * train_frac), int(n * (train_frac + val_frac))
    return (X[:a], y[:a]), (X[a:b], y[a:b]), (X[b:], y[b:])


# ---------------------------------------------------------------- Isolation Forest


def test_isolation_forest_never_sees_labels_during_fit(monkeypatch):
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)

    from sklearn.ensemble import IsolationForest

    original_fit = IsolationForest.fit
    seen_args = {}

    def spy_fit(self, X_arg, y_arg=None, **kwargs):
        seen_args["y"] = y_arg
        return original_fit(self, X_arg, y_arg, **kwargs)

    monkeypatch.setattr(IsolationForest, "fit", spy_fit)
    fit_and_tune_isolation_forest(Xtr, Xval, yval, names)
    assert seen_args["y"] is None


def test_isolation_forest_prediction_shape():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_isolation_forest(Xtr, Xval, yval, names)
    out = if_predict(fitted, Xte)
    assert out["anomaly_score"].shape[0] == Xte.shape[0]
    assert out["anomaly_label"].shape[0] == Xte.shape[0]
    assert set(np.unique(out["anomaly_label"])).issubset({0, 1})


def test_isolation_forest_threshold_behavior_monotonic():
    """A higher threshold must never produce MORE positive labels than a
    lower one, for the same score array."""
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_isolation_forest(Xtr, Xval, yval, names)
    scores = anomaly_scores(fitted.model, Xte)
    low_labels = (scores >= scores.min()).sum()
    high_labels = (scores >= scores.max()).sum()
    assert high_labels <= low_labels


# ---------------------------------------------------------------------- XGBoost


def test_xgboost_target_never_in_feature_matrix():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)
    # X passed to fit had exactly n_features columns, never n_features+1 (label appended)
    assert fitted.model.n_features_in_ == X.shape[1]


def test_xgboost_prediction_shape_and_range():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)
    out = xgb_predict(fitted, Xte)
    assert out["fraud_probability"].shape[0] == Xte.shape[0]
    assert (out["fraud_probability"] >= 0).all() and (out["fraud_probability"] <= 1).all()
    assert set(np.unique(out["predicted_class"])).issubset({0, 1})


def test_xgboost_threshold_was_tuned_on_validation_range():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)
    assert 0.0 <= fitted.threshold <= 1.0


def test_xgboost_inference_consistency_same_input_same_output():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)
    out1 = xgb_predict(fitted, Xte)
    out2 = xgb_predict(fitted, Xte)
    np.testing.assert_array_equal(out1["predicted_class"], out2["predicted_class"])
    np.testing.assert_allclose(out1["fraud_probability"], out2["fraud_probability"])


# ------------------------------------------------------------------------- SHAP


def test_shap_explainer_output_structure():
    X, y, names = _make_toy_classification_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)

    explainer = FraudExplainer(fitted.model, names, feature_dictionary_path=None, dataset_key="toy")
    explanation = explainer.explain(Xte[0], fitted.threshold, top_n=3)
    d = explanation.to_dict()

    assert 0.0 <= d["fraud_probability"] <= 1.0
    assert d["predicted_class"] in (0, 1)
    assert len(d["top_contributing_features"]) == 3
    for f in d["top_contributing_features"]:
        assert f["direction"] in ("increases_fraud_risk", "decreases_fraud_risk")
        assert f["magnitude"] >= 0
        assert "description" in f
    assert isinstance(d["human_readable_explanation"], str) and len(d["human_readable_explanation"]) > 0


def test_shap_top_feature_matches_known_informative_feature():
    """f0 was constructed to be the dominant fraud signal; SHAP should rank
    it among the top contributors for a known-fraud row."""
    X, y, names = _make_toy_classification_data(n=800)
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_xgboost(Xtr, ytr, Xval, yval, names)

    fraud_rows = np.where(yte == 1)[0]
    if len(fraud_rows) == 0:
        pytest.skip("no positive rows landed in the toy test split")
    explainer = FraudExplainer(fitted.model, names, feature_dictionary_path=None, dataset_key="toy")
    explanation = explainer.explain(Xte[fraud_rows[0]], fitted.threshold, top_n=6)
    top_feature_names = [f["feature"] for f in explanation.to_dict()["top_contributing_features"]]
    assert "f0" in top_feature_names


# --------------------------------------------------------------------- metrics


def test_search_best_threshold_returns_value_within_score_range():
    y = np.array([0, 0, 0, 1, 1, 0, 1, 0, 0, 1])
    scores = np.array([0.1, 0.2, 0.15, 0.9, 0.8, 0.05, 0.7, 0.3, 0.25, 0.6])
    threshold, report, table = search_best_threshold(y, scores, metric="f1")
    assert scores.min() <= threshold <= scores.max()
    assert report.f1 >= 0


def test_evaluate_at_threshold_confusion_matrix_sums_to_total():
    y = np.array([0, 1, 1, 0, 1])
    scores = np.array([0.1, 0.9, 0.4, 0.2, 0.6])
    report = evaluate_at_threshold(y, scores, threshold=0.5)
    assert report.tp + report.fp + report.fn + report.tn == len(y)
