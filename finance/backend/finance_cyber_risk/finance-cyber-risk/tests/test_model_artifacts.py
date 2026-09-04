"""
These tests exercise the actual saved artifacts produced by
scripts/train_fraud_models.py, so they only run when those artifacts exist
(they are skipped, not failed, in a fresh checkout before training has run).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from src.config.paths import ARTIFACTS_DIR, INDIAN_BANKING_PROCESSED_DIR, PREPROCESSORS_DIR
from src.data.processed_loader import load_processed_dataset
from src.models.fraud.xgboost_model import predict as xgb_predict, predict_proba
from src.models.anomaly.isolation_forest_model import predict as if_predict
from src.utils.io import load_object

MODELS_DIR = ARTIFACTS_DIR / "models"

pytestmark = pytest.mark.skipif(
    not (MODELS_DIR / "indian_banking_xgboost.joblib").exists(),
    reason="Fraud models not yet trained — run scripts/train_fraud_models.py first.",
)


@pytest.fixture(scope="module")
def ib_dataset():
    fitted_preproc = load_object(PREPROCESSORS_DIR / "indian_banking_preprocessor.joblib")
    return load_processed_dataset(
        INDIAN_BANKING_PROCESSED_DIR, "is_fraud", fitted_preproc.output_feature_names
    )


def test_saved_xgboost_model_loads_and_matches_feature_count(ib_dataset):
    fitted = load_object(MODELS_DIR / "indian_banking_xgboost.joblib")
    assert fitted.model.n_features_in_ == ib_dataset.test.X.shape[1]
    assert len(fitted.feature_names) == ib_dataset.test.X.shape[1]


def test_saved_isolation_forest_model_loads_and_matches_feature_count(ib_dataset):
    fitted = load_object(MODELS_DIR / "indian_banking_isolation_forest.joblib")
    scores = fitted.model.decision_function(ib_dataset.test.X[:5])
    assert scores.shape[0] == 5


def test_saved_xgboost_inference_is_deterministic(ib_dataset):
    fitted = load_object(MODELS_DIR / "indian_banking_xgboost.joblib")
    X = ib_dataset.test.X[:50]
    out1 = xgb_predict(fitted, X)
    out2 = xgb_predict(fitted, X)
    np.testing.assert_array_equal(out1["predicted_class"], out2["predicted_class"])
    np.testing.assert_allclose(out1["fraud_probability"], out2["fraud_probability"])


def test_saved_xgboost_threshold_is_within_valid_probability_range(ib_dataset):
    fitted = load_object(MODELS_DIR / "indian_banking_xgboost.joblib")
    assert 0.0 <= fitted.threshold <= 1.0


def test_saved_models_never_received_target_as_a_feature_column(ib_dataset):
    fitted_xgb = load_object(MODELS_DIR / "indian_banking_xgboost.joblib")
    assert "is_fraud" not in fitted_xgb.feature_names
    fitted_if = load_object(MODELS_DIR / "indian_banking_isolation_forest.joblib")
    assert "is_fraud" not in fitted_if.feature_names
