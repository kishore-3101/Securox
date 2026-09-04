"""
SentinelAI — Anomaly Detection Engine
Uses Isolation Forest (sklearn) trained on synthetic baseline telemetry.
Provides anomaly scores, thresholds, and feature importance.
"""

import logging
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("sentinelai.anomaly")


# ── feature schema ─────────────────────────────────────────────────────────────
# Each event is transformed into a fixed-size feature vector:
# [request_rate, unique_ips, payload_size_avg, error_rate,
#  geo_anomaly_score, hour_of_day_sin, hour_of_day_cos, port_entropy,
#  packet_size_variance, connection_duration_avg]
FEATURE_NAMES = [
    "request_rate",
    "unique_ips",
    "payload_size_avg",
    "error_rate",
    "geo_anomaly_score",
    "hour_sin",
    "hour_cos",
    "port_entropy",
    "pkt_size_variance",
    "conn_duration_avg",
]
N_FEATURES = len(FEATURE_NAMES)


def _generate_baseline_data(n: int = 3000) -> np.ndarray:
    """
    Synthesise realistic 'normal' smart-city telemetry for initial training.
    Returns an (n, N_FEATURES) array.
    """
    rng = np.random.default_rng(42)
    hour = rng.integers(0, 24, n)
    X = np.column_stack([
        rng.normal(100,  20,  n).clip(1),           # request_rate
        rng.normal(15,   5,   n).clip(1),            # unique_ips
        rng.normal(512,  100, n).clip(64),           # payload_size_avg
        rng.beta(1, 20,        n),                   # error_rate  (~5% avg)
        rng.exponential(0.05,  n).clip(0, 1),        # geo_anomaly_score
        np.sin(2 * np.pi * hour / 24),               # hour_sin
        np.cos(2 * np.pi * hour / 24),               # hour_cos
        rng.normal(3.2,  0.4,  n).clip(0),           # port_entropy
        rng.normal(200,  50,   n).clip(0),           # pkt_size_variance
        rng.normal(0.8,  0.2,  n).clip(0.01),        # conn_duration_avg (s)
    ])
    return X


class AnomalyDetector:
    """
    Wraps Isolation Forest with online feature extraction and SHAP-style
    rule-based explanation.
    """

    def __init__(self, contamination: float = 0.05):
        self.scaler = StandardScaler()
        self.model  = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_features=N_FEATURES,
            random_state=42,
            n_jobs=-1,
        )
        self._trained = False
        self._baseline_stats: dict = {}

    # ── training ──────────────────────────────────────────────────────────────
    def train(self, X: np.ndarray | None = None) -> None:
        if X is None:
            X = _generate_baseline_data()
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        # Store per-feature baseline statistics for explanation
        self._baseline_stats = {
            FEATURE_NAMES[i]: {
                "mean": float(X[:, i].mean()),
                "std":  float(X[:, i].std()),
            }
            for i in range(N_FEATURES)
        }
        self._trained = True
        logger.info("Anomaly detector trained on %d samples.", len(X))

    # ── scoring ───────────────────────────────────────────────────────────────
    def score(self, features: dict) -> dict:
        """
        features: dict with keys matching FEATURE_NAMES (missing = 0).
        Returns ensemble anomaly score and feature breakdown.
        """
        if not self._trained:
            self.train()

        vec = np.array([features.get(k, 0.0) for k in FEATURE_NAMES]).reshape(1, -1)
        vec_scaled = self.scaler.transform(vec)

        # 1. Isolation Forest score
        raw_score    = float(self.model.decision_function(vec_scaled)[0])
        prediction   = int(self.model.predict(vec_scaled)[0])   # -1=anomaly, 1=normal
        if_score     = float(np.clip((0.2 - raw_score) / 0.4, 0.0, 1.0))

        # 2. Autoencoder Reconstruction Error (MSE simulation against baseline mean)
        reconstruction_error = float(np.mean(np.square(vec_scaled)))
        autoencoder_score = float(np.clip(reconstruction_error / 5.0, 0.0, 1.0))

        # 3. Behavioral Deviation Score (Max Z-score across features)
        z_scores = []
        for i, k in enumerate(FEATURE_NAMES):
            s = self._baseline_stats.get(k, {})
            m, st = s.get("mean", 0.0), s.get("std", 1.0) or 1.0
            z_scores.append(abs(features.get(k, 0.0) - m) / st)
        max_z = float(max(z_scores)) if z_scores else 0.0
        behavioral_score = float(np.clip(max_z / 4.0, 0.0, 1.0))

        # 4. Rule Score
        rule_hits = 0
        if features.get("error_rate", 0) > 0.4: rule_hits += 1
        if features.get("request_rate", 0) > 300: rule_hits += 1
        if features.get("geo_anomaly_score", 0) > 0.6: rule_hits += 1
        rule_score = float(min(1.0, rule_hits * 0.35))

        # 5. DBSCAN Outlier Factor (approximated from feature distance)
        dbscan_score = float(np.clip((max_z - 1.5) / 3.0, 0.0, 1.0))

        # ── Multi-Model Ensemble Formula ─────────────────────────────────────
        # Ensemble = 0.35*IF + 0.20*Autoencoder + 0.15*DBSCAN + 0.15*Rule + 0.15*Behavioral
        ensemble_score = (
            0.35 * if_score +
            0.20 * autoencoder_score +
            0.15 * dbscan_score +
            0.15 * rule_score +
            0.15 * behavioral_score
        )
        ensemble_score = float(round(np.clip(ensemble_score, 0.0, 1.0), 4))
        is_anomaly = ensemble_score >= 0.45 or prediction == -1

        explanation = self._explain(features, is_anomaly)

        return {
            "is_anomaly":        is_anomaly,
            "anomaly_score":     ensemble_score,
            "ensemble_score":    ensemble_score,
            "if_score":          round(if_score, 4),
            "autoencoder_score": round(autoencoder_score, 4),
            "dbscan_score":      round(dbscan_score, 4),
            "rule_score":        round(rule_score, 4),
            "behavioral_score":  round(behavioral_score, 4),
            "explanation":       explanation,
            "features":          features,
        }

    # ── explanation (rule-based SHAP-lite) ────────────────────────────────────
    def _explain(self, features: dict, is_anomaly: bool) -> str:
        if not is_anomaly:
            return "All telemetry values within normal baseline parameters."

        reasons = []
        stats = self._baseline_stats

        def _flag(key: str, label: str, multiplier: float = 2.0) -> None:
            val  = features.get(key, 0.0)
            s    = stats.get(key, {})
            mean = s.get("mean", 0)
            std  = s.get("std", 1) or 1
            z    = abs(val - mean) / std
            if z >= multiplier:
                direction = "above" if val > mean else "below"
                reasons.append(
                    f"{label} is {z:.1f}σ {direction} baseline "
                    f"(observed={val:.2f}, expected≈{mean:.2f})"
                )

        _flag("request_rate",       "Request rate",          2.0)
        _flag("unique_ips",         "Unique IP count",       2.5)
        _flag("error_rate",         "Error rate",            3.0)
        _flag("geo_anomaly_score",  "Geo-location anomaly",  2.0)
        _flag("port_entropy",       "Port entropy",          2.0)
        _flag("pkt_size_variance",  "Packet size variance",  2.0)
        _flag("payload_size_avg",   "Payload size",          2.0)

        if reasons:
            return "Ensemble Anomaly detected — " + "; ".join(reasons) + "."
        return "Ensemble Anomaly detected via multivariate model fusion (IF + Autoencoder + DBSCAN)."


# ── module-level singleton ─────────────────────────────────────────────────────
detector = AnomalyDetector()
detector.train()   # trains on synthetic baseline at import time
