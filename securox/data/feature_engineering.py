"""
Securox — Feature Engineering & Preprocessing Pipeline
Handles data cleaning, normalization, missing values, infinite values,
feature scaling, and stratified train/val/test splitting without data leakage.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

from data.schema import CanonicalEvent, ATTACK_CLASSES
from data.normalizer import DatasetNormalizer

logger = logging.getLogger("securox.features")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ── Canonical Feature Vector Column Names ─────────────────────────────────────
FEATURE_COLUMNS = [
    "duration",
    "bytes_in",
    "bytes_out",
    "total_bytes",
    "packets",
    "request_rate",
    "byte_rate",
    "packet_rate",
    "error_rate",
    "dst_port_norm",
    "is_tcp",
    "is_udp"
]


class FeatureEngineeringPipeline:
    """End-to-end data preparation and feature extraction for AI/ML models."""

    def __init__(self, scaler_path: Optional[Path] = None):
        self.scaler_path = scaler_path or (MODELS_DIR / "feature_scaler.joblib")
        self.scaler = StandardScaler()
        self.is_fitted = False

    def extract_features_from_event(self, event: CanonicalEvent) -> np.ndarray:
        """Transforms a single CanonicalEvent into a scaled feature vector."""
        tot_bytes = float(event.bytes_in + event.bytes_out)
        dur = max(0.0001, float(event.duration))
        byte_rate = tot_bytes / dur
        pkt_rate = float(event.packets) / dur
        dst_port_norm = float(event.destination_port % 1024) / 1024.0
        proto = str(event.protocol).upper()

        raw_vec = np.array([[
            float(event.duration),
            float(event.bytes_in),
            float(event.bytes_out),
            tot_bytes,
            float(event.packets),
            float(event.request_rate),
            min(1e8, byte_rate),
            min(1e6, pkt_rate),
            float(event.error_rate),
            dst_port_norm,
            1.0 if proto == "TCP" else 0.0,
            1.0 if proto == "UDP" else 0.0,
        ]], dtype=np.float32)

        if self.is_fitted:
            return self.scaler.transform(raw_vec)[0]
        return raw_vec[0]

    def load_and_preprocess(
        self,
        dataset_name: str = "cicids2017",
        test_size: float = 0.20,
        val_size: float = 0.10,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
        """
        Loads the specified raw dataset, normalizes via DatasetNormalizer,
        cleans inf/nan, extracts features, fits/applies scaler, and returns
        (X_train, y_train, X_val, y_val, X_test, y_test, attack_labels).
        """
        csv_map = {
            "cicids2017": (DATA_DIR / "cicids2017_sample.csv", DatasetNormalizer.normalize_cicids2017),
            "unsw_nb15":  (DATA_DIR / "unsw_nb15_sample.csv",  DatasetNormalizer.normalize_unsw_nb15),
            "nsl_kdd":    (DATA_DIR / "nsl_kdd_sample.csv",    DatasetNormalizer.normalize_nsl_kdd),
            "ton_iot":    (DATA_DIR / "ton_iot_sample.csv",    DatasetNormalizer.normalize_unsw_nb15),
        }

        if dataset_name not in csv_map:
            raise ValueError(f"Unknown dataset '{dataset_name}'. Choose from: {list(csv_map.keys())}")

        file_path, normalizer_fn = csv_map[dataset_name]
        if not file_path.exists():
            from data.download_datasets import main as run_download
            logger.info("Dataset file not found at %s. Triggering download...", file_path)
            run_download()

        df_raw = pd.read_csv(file_path)
        logger.info("Loaded %d raw records from %s.", len(df_raw), file_path.name)

        # 1. Normalize rows into CanonicalEvents
        events: List[CanonicalEvent] = []
        for _, row in df_raw.iterrows():
            try:
                evt = normalizer_fn(row.to_dict())
                events.append(evt)
            except Exception as e:
                continue

        logger.info("Normalized %d events successfully into CanonicalEvent schema.", len(events))

        # 2. Build feature matrix X and target labels y
        X_rows = []
        y_attack_classes = []
        y_binary = []

        for e in events:
            tot_bytes = float(e.bytes_in + e.bytes_out)
            dur = max(0.0001, float(e.duration))
            byte_rate = tot_bytes / dur
            pkt_rate = float(e.packets) / dur
            dst_port_norm = float(e.destination_port % 1024) / 1024.0
            proto = str(e.protocol).upper()

            X_rows.append([
                float(e.duration),
                float(e.bytes_in),
                float(e.bytes_out),
                tot_bytes,
                float(e.packets),
                float(e.request_rate),
                min(1e8, byte_rate),
                min(1e6, pkt_rate),
                float(e.error_rate),
                dst_port_norm,
                1.0 if proto == "TCP" else 0.0,
                1.0 if proto == "UDP" else 0.0,
            ])
            y_attack_classes.append(e.attack_type)
            y_binary.append(e.label)

        X = np.array(X_rows, dtype=np.float32)
        y = np.array(y_attack_classes)

        # 3. Clean NaN and Inf
        X = np.nan_to_num(X, nan=0.0, posinf=1e8, neginf=-1e8)

        # Filter out extremely rare classes (< 5 occurrences) so stratified splitting succeeds
        counts = pd.Series(y).value_counts()
        rare_classes = counts[counts < 5].index.tolist()
        if rare_classes:
            valid_mask = ~np.isin(y, rare_classes)
            X = X[valid_mask]
            y = y[valid_mask]
            logger.info("Filtered %d rare class records (< 5 samples) for stable stratified split.", int(np.sum(~valid_mask)))

        # 4. Stratified Split: Train (70%), Val (10%), Test (20%)
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        # Further split train_val into train and validation
        adjusted_val_size = val_size / (1.0 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val, y_train_val, test_size=adjusted_val_size, random_state=random_state, stratify=y_train_val
        )

        # 5. Fit Scaler strictly on Training Data (Zero Data Leakage)
        self.scaler.fit(X_train)
        self.is_fitted = True
        joblib.dump(self.scaler, self.scaler_path)
        logger.info("Fitted StandardScaler saved to %s.", self.scaler_path)

        # 6. Transform all partitions
        X_train_scaled = self.scaler.transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)

        logger.info("Dataset splits ready:")
        logger.info("  X_train: %s | X_val: %s | X_test: %s", X_train_scaled.shape, X_val_scaled.shape, X_test_scaled.shape)

        return X_train_scaled, y_train, X_val_scaled, y_val, X_test_scaled, y_test, list(np.unique(y))


pipeline = FeatureEngineeringPipeline()
extract_features_from_event = pipeline.extract_features_from_event
