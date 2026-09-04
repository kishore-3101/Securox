"""
SentinelAI — Behavioural Clustering Engine
DBSCAN clusters IP/device behaviour profiles.  Outlier clusters indicate
coordinated attacks (botnets, insider-threat pivoting, etc.).
"""

import logging
from collections import defaultdict, deque
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("sentinelai.clustering")

MAX_PROFILES = 500    # rolling window of device profiles to cluster


# ── cluster labels ────────────────────────────────────────────────────────────
CLUSTER_LABELS = {
    -1: "Outlier / Suspicious",
    0:  "Normal Traffic",
    1:  "Elevated Activity",
    2:  "Coordinated Behaviour",
    3:  "High-Volume Sender",
    4:  "Scanning Pattern",
}


class BehaviouralClusterer:
    """
    Maintains a rolling buffer of (ip, feature_vector) pairs.
    Re-clusters every N new observations; exposes cluster summary and
    anomalous cluster membership for any given IP.
    """

    def __init__(self, eps: float = 0.5, min_samples: int = 3,
                 recluster_every: int = 20):
        self.eps             = eps
        self.min_samples     = min_samples
        self.recluster_every = recluster_every
        self._scaler         = StandardScaler()
        self._profiles:      deque = deque(maxlen=MAX_PROFILES)
        self._labels:        list  = []
        self._cluster_summary: dict = {}
        self._n_since_last   = 0

    # ── public API ────────────────────────────────────────────────────────────
    def add_profile(self, ip: str, features: dict) -> None:
        """
        features expected keys:
            req_count, unique_endpoints, error_ratio, bytes_sent,
            bytes_recv, session_duration, port_variety, hour_of_day
        """
        vec = [
            features.get("req_count",         0),
            features.get("unique_endpoints",  0),
            features.get("error_ratio",       0),
            features.get("bytes_sent",        0),
            features.get("bytes_recv",        0),
            features.get("session_duration",  0),
            features.get("port_variety",      0),
            features.get("hour_of_day",       0),
        ]
        self._profiles.append({"ip": ip, "vec": vec})
        self._n_since_last += 1
        if self._n_since_last >= self.recluster_every:
            self._recluster()
            self._n_since_last = 0

    def get_cluster_summary(self) -> dict:
        if not self._cluster_summary:
            self._recluster()
        return self._cluster_summary

    def is_suspicious(self, ip: str) -> bool:
        """True if the most recent profile for this IP landed in cluster -1."""
        for i in range(len(self._profiles) - 1, -1, -1):
            profile = list(self._profiles)[i]
            if profile["ip"] == ip and i < len(self._labels):
                return int(self._labels[i]) == -1
        return False

    # ── internal ──────────────────────────────────────────────────────────────
    def _recluster(self) -> None:
        profiles = list(self._profiles)
        if len(profiles) < self.min_samples + 1:
            return
        X = np.array([p["vec"] for p in profiles], dtype=float)
        try:
            X_scaled      = self._scaler.fit_transform(X)
            db            = DBSCAN(eps=self.eps, min_samples=self.min_samples, n_jobs=-1)
            self._labels  = db.fit_predict(X_scaled).tolist()
        except Exception as exc:
            logger.warning("DBSCAN failed: %s", exc)
            return

        # Summarise clusters
        cluster_counts: dict = defaultdict(int)
        cluster_ips:    dict = defaultdict(list)
        for i, label in enumerate(self._labels):
            cluster_counts[label] += 1
            cluster_ips[label].append(profiles[i]["ip"])

        self._cluster_summary = {
            "n_profiles":  len(profiles),
            "n_clusters":  len([k for k in cluster_counts if k != -1]),
            "n_outliers":  cluster_counts.get(-1, 0),
            "clusters": [
                {
                    "id":    int(k),
                    "label": CLUSTER_LABELS.get(k, f"Cluster {k}"),
                    "size":  v,
                    "sample_ips": list(set(cluster_ips[k]))[:5],
                    "is_anomalous": k == -1,
                }
                for k, v in sorted(cluster_counts.items())
            ],
        }
        logger.debug("Reclustered %d profiles → %d clusters, %d outliers.",
                     len(profiles),
                     self._cluster_summary["n_clusters"],
                     self._cluster_summary["n_outliers"])

    # ── seed with synthetic normal data ───────────────────────────────────────
    def seed_baseline(self, n: int = 80) -> None:
        rng = np.random.default_rng(21)
        for _ in range(n):
            ip  = f"10.0.{rng.integers(0,255)}.{rng.integers(1,254)}"
            self.add_profile(ip, {
                "req_count":        float(rng.normal(50, 15)),
                "unique_endpoints": float(rng.integers(2, 10)),
                "error_ratio":      float(rng.beta(1, 20)),
                "bytes_sent":       float(rng.normal(10_000, 3_000)),
                "bytes_recv":       float(rng.normal(50_000, 10_000)),
                "session_duration": float(rng.normal(120, 30)),
                "port_variety":     float(rng.integers(1, 5)),
                "hour_of_day":      float(rng.integers(0, 24)),
            })


# ── module singleton ──────────────────────────────────────────────────────────
clusterer = BehaviouralClusterer()
clusterer.seed_baseline()
