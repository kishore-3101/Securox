import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from src.models.aml.aml_classifier import fit_and_tune_aml_model, predict, predict_proba
from src.config.paths import ARTIFACTS_DIR, AMLSIM_PROCESSED_DIR, PREPROCESSORS_DIR
from src.data.processed_loader import load_processed_dataset
from src.utils.io import load_object

AML_MODELS_DIR = ARTIFACTS_DIR / "models" / "aml"


def _toy_aml_data(n=200, n_features=5, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n_features))
    y = np.zeros(n, dtype=int)
    sar_idx = rng.choice(n, size=max(5, n // 20), replace=False)
    y[sar_idx] = 1
    X[sar_idx, 0] += 4.0
    names = [f"f{i}" for i in range(n_features)]
    return X, y, names


def _split(X, y, train_frac=0.6, val_frac=0.2):
    n = len(X)
    a, b = int(n * train_frac), int(n * (train_frac + val_frac))
    return (X[:a], y[:a]), (X[a:b], y[a:b]), (X[b:], y[b:])


def test_logistic_regression_baseline_trains_and_predicts():
    X, y, names = _toy_aml_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_aml_model("logistic_regression", Xtr, ytr, Xval, yval, names)
    out = predict(fitted, Xte)
    assert out["sar_probability"].shape[0] == Xte.shape[0]
    assert set(np.unique(out["predicted_class"])).issubset({0, 1})


def test_xgboost_aml_trains_and_predicts():
    X, y, names = _toy_aml_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_aml_model("xgboost", Xtr, ytr, Xval, yval, names)
    out = predict(fitted, Xte)
    assert out["sar_probability"].shape[0] == Xte.shape[0]
    assert (out["sar_probability"] >= 0).all() and (out["sar_probability"] <= 1).all()


def test_unknown_model_name_raises():
    X, y, names = _toy_aml_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    with pytest.raises(ValueError):
        fit_and_tune_aml_model("not_a_real_model", Xtr, ytr, Xval, yval, names)


def test_aml_model_never_receives_more_features_than_given():
    X, y, names = _toy_aml_data()
    (Xtr, ytr), (Xval, yval), (Xte, yte) = _split(X, y)
    fitted = fit_and_tune_aml_model("xgboost", Xtr, ytr, Xval, yval, names)
    assert fitted.model.n_features_in_ == X.shape[1]


# --------------------------------------------------- saved-artifact tests

pytestmark_skip = pytest.mark.skipif(
    not (AML_MODELS_DIR / "aml_logistic_regression.joblib").exists(),
    reason="AML models not yet trained — run scripts/train_aml_model.py first.",
)


@pytestmark_skip
def test_saved_aml_models_load_and_match_feature_count():
    fitted_preproc = load_object(PREPROCESSORS_DIR / "amlsim_preprocessor.joblib")
    dataset = load_processed_dataset(
        AMLSIM_PROCESSED_DIR, "is_sar", fitted_preproc.output_feature_names
    )
    for name in ["logistic_regression", "xgboost"]:
        fitted = load_object(AML_MODELS_DIR / f"aml_{name}.joblib")
        assert len(fitted.feature_names) == dataset.test.X.shape[1]
        prob = predict_proba(fitted, dataset.test.X)
        assert prob.shape[0] == dataset.test.X.shape[0]


@pytestmark_skip
def test_saved_aml_models_never_used_target_as_feature():
    for name in ["logistic_regression", "xgboost"]:
        fitted = load_object(AML_MODELS_DIR / f"aml_{name}.joblib")
        assert "is_sar" not in fitted.feature_names
        assert "is_alert_member" not in fitted.feature_names
        assert "alert_reason" not in fitted.feature_names
