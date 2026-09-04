"""
Securox — Machine Learning Training Pipeline
Trains:
- Model A: Unsupervised Anomaly Detector (Isolation Forest)
- Model B: Supervised Attack Classifier (XGBoost / Random Forest)
- Model C: Behavioral Entity Clusterer (DBSCAN)
- Model D: Temporal Momentum Predictor

Usage:
    python ml/train.py --dataset cicids2017
    python ml/train.py --dataset unsw_nb15
    python ml/train.py --dataset all
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import joblib

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.cluster import DBSCAN
import xgboost as xgb

from data.feature_engineering import pipeline, MODELS_DIR, FEATURE_COLUMNS
from data.schema import ATTACK_CLASSES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("securox.train")

MODELS_DIR.mkdir(parents=True, exist_ok=True)
(MODELS_DIR / "isolation_forest").mkdir(parents=True, exist_ok=True)
(MODELS_DIR / "classifier").mkdir(parents=True, exist_ok=True)
(MODELS_DIR / "clustering").mkdir(parents=True, exist_ok=True)


def train_isolation_forest(X_train: np.ndarray, y_train: np.ndarray, dataset_name: str) -> IsolationForest:
    """
    Model A — Unsupervised Anomaly Detection
    Trained predominantly on benign records to detect unseen zero-day deviations.
    """
    logger.info("--- Training Model A: Isolation Forest on %s ---", dataset_name)
    # Filter benign records for nominal baseline fitting
    benign_mask = (y_train == "BENIGN")
    X_benign = X_train[benign_mask] if np.sum(benign_mask) > 100 else X_train

    logger.info("Fitting Isolation Forest on %d benign baseline records...", len(X_benign))
    iso_forest = IsolationForest(
        n_estimators=150,
        contamination=0.05,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    iso_forest.fit(X_benign)

    model_path = MODELS_DIR / "isolation_forest" / f"{dataset_name}_iso_forest.joblib"
    joblib.dump(iso_forest, model_path)
    logger.info("Saved Isolation Forest model to %s", model_path)
    return iso_forest


def train_classifier(X_train: np.ndarray, y_train: np.ndarray, dataset_name: str):
    """
    Model B — Supervised Multi-Class Attack Classifier
    Uses XGBoost with fallbacks to Random Forest if necessary.
    """
    logger.info("--- Training Model B: Supervised Attack Classifier on %s ---", dataset_name)
    # Create class label encoding mapping
    unique_classes = sorted(list(np.unique(y_train)))
    class_to_idx = {cls: idx for idx, cls in enumerate(unique_classes)}
    idx_to_class = {idx: cls for idx, cls in enumerate(unique_classes)}
    y_encoded = np.array([class_to_idx[c] for c in y_train])

    logger.info("Classes detected (%d): %s", len(unique_classes), unique_classes)
    
    try:
        clf = xgb.XGBClassifier(
            n_estimators=120,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_train, y_encoded)
        model_type = "XGBoost"
    except Exception as e:
        logger.warning("XGBoost training exception (%s). Falling back to RandomForestClassifier.", e)
        clf = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_train, y_encoded)
        model_type = "RandomForest"

    # Save classifier and label mapping
    model_path = MODELS_DIR / "classifier" / f"{dataset_name}_classifier.joblib"
    meta_path = MODELS_DIR / "classifier" / f"{dataset_name}_metadata.joblib"
    
    joblib.dump(clf, model_path)
    joblib.dump({
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "classes": unique_classes,
        "feature_names": FEATURE_COLUMNS,
        "model_type": model_type
    }, meta_path)

    logger.info("Saved %s classifier and metadata to %s", model_type, model_path)
    return clf, class_to_idx, idx_to_class


def train_dbscan_clustering(X_train: np.ndarray, dataset_name: str) -> DBSCAN:
    """
    Model C — Behavioral Clustering Engine (DBSCAN)
    Identifies anomalous clusters and botnet groups.
    """
    logger.info("--- Fitting Model C: DBSCAN Entity Clusterer on %s ---", dataset_name)
    sample_sub = X_train[:min(3000, len(X_train))]
    dbscan = DBSCAN(eps=0.75, min_samples=5, n_jobs=-1)
    dbscan.fit(sample_sub)

    model_path = MODELS_DIR / "clustering" / f"{dataset_name}_dbscan.joblib"
    joblib.dump(dbscan, model_path)
    logger.info("Fitted and saved DBSCAN to %s", model_path)
    return dbscan


def train_dataset(dataset_name: str):
    """Executes full multi-model training pipeline for a given dataset."""
    logger.info("============================================================")
    logger.info("STARTING TRAINING PIPELINE FOR: %s", dataset_name.upper())
    logger.info("============================================================")

    # 1. Preprocess and split
    X_train, y_train, X_val, y_val, X_test, y_test, classes = pipeline.load_and_preprocess(
        dataset_name=dataset_name,
        test_size=0.20,
        val_size=0.10,
        random_state=42
    )

    # 2. Train Model A: Isolation Forest
    train_isolation_forest(X_train, y_train, dataset_name)

    # 3. Train Model B: Supervised Classifier
    train_classifier(X_train, y_train, dataset_name)

    # 4. Train Model C: DBSCAN
    train_dbscan_clustering(X_train, dataset_name)

    # Save preprocessed evaluation test partition for evaluate.py
    test_cache = MODELS_DIR / f"{dataset_name}_test_partition.joblib"
    joblib.dump({
        "X_test": X_test,
        "y_test": y_test,
        "X_val": X_val,
        "y_val": y_val,
        "feature_names": FEATURE_COLUMNS
    }, test_cache)
    logger.info("Saved test partition cache to %s (%d test records).", test_cache, len(y_test))
    logger.info("TRAINING COMPLETE FOR: %s", dataset_name.upper())


def main():
    parser = argparse.ArgumentParser(description="Securox AI Model Training CLI")
    parser.add_argument(
        "--dataset",
        choices=["cicids2017", "unsw_nb15", "nsl_kdd", "all"],
        default="cicids2017",
        help="Dataset on which to train the multi-model architecture."
    )
    args = parser.parse_args()

    if args.dataset == "all":
        for ds in ["cicids2017", "unsw_nb15", "nsl_kdd"]:
            train_dataset(ds)
    else:
        train_dataset(args.dataset)


if __name__ == "__main__":
    main()
