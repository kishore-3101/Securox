"""
Securox — Risk Intelligence Engine (Upgraded for SH-FIN-05)
Computes a dynamic, transparent composite 0–100 risk score per smart-city asset
governed by configurable YAML weights in risk/config.yaml.

Mathematical Formulation:
  Risk Score =
      30% ML Anomaly (Isolation Forest)
    + 20% Attack Classification Severity (XGBoost)
    + 20% Asset Criticality (Smart City Asset Registry)
    + 15% Dependency Propagation Impact (Digital Twin Graph)
    + 10% Behavioral Anomaly (DBSCAN Cluster Outlier)
    +  5% Threat Intelligence (IOC & IP Reputation Match)
"""

import os
import sys
import logging
import math
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
backend_dir = PROJECT_ROOT / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from data.schema import ATTACK_WEIGHT_MAP, ATTACK_SEVERITY_MAP
try:
    from backend.assets.registry import asset_registry
except ImportError:
    from assets.registry import asset_registry

logger = logging.getLogger("securox.risk")
CONFIG_PATH = PROJECT_ROOT / "risk" / "config.yaml"

# Default fallback weights if YAML is missing
DEFAULT_WEIGHTS = {
    "ml_anomaly": 0.30,
    "attack_severity": 0.20,
    "asset_criticality": 0.20,
    "propagation_impact": 0.15,
    "behavioral_anomaly": 0.10,
    "threat_intelligence": 0.05,
}

RiskCategory = Literal["CATASTROPHIC", "CRITICAL", "HIGH", "MODERATE", "LOW", "NORMAL"]


def load_risk_config() -> dict:
    """Loads risk configuration from risk/config.yaml."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fp:
                return yaml.safe_load(fp) or {}
        except Exception as e:
            logger.warning("Failed to parse risk/config.yaml (%s). Using defaults.", e)
    return {
        "weights": DEFAULT_WEIGHTS,
        "thresholds": {"critical": 75.0, "high": 60.0, "moderate": 40.0, "low": 20.0},
        "confidence_weights": {"base": 0.40, "corroborating_source_factor": 0.15, "ml_certainty_weight": 0.45}
    }


def categorise(score: float, thresholds: Optional[dict] = None) -> RiskCategory:
    th = thresholds or {"critical": 75.0, "high": 60.0, "moderate": 40.0, "low": 20.0}
    if score >= 90.0: return "CATASTROPHIC"
    if score >= th.get("critical", 75.0): return "CRITICAL"
    if score >= th.get("high", 60.0):     return "HIGH"
    if score >= th.get("moderate", 40.0): return "MODERATE"
    if score >= th.get("low", 20.0):      return "LOW"
    return "NORMAL"


class RiskEngine:
    """
    Transparent Multidimensional Composite Risk Intelligence Engine.
    Conforms strictly to Section 13 of SH-FIN-05.
    """

    def __init__(self):
        self.config = load_risk_config()
        self.weights = self.config.get("weights", DEFAULT_WEIGHTS)
        self.thresholds = self.config.get("thresholds", {"critical": 75.0, "high": 60.0, "moderate": 40.0, "low": 20.0})

    def reload_config(self):
        self.config = load_risk_config()
        self.weights = self.config.get("weights", DEFAULT_WEIGHTS)
        self.thresholds = self.config.get("thresholds", {"critical": 75.0, "high": 60.0, "moderate": 40.0, "low": 20.0})

    def compute(
        self,
        asset: str,
        anomaly_score: float,                  # 0.0 to 1.0 (Isolation Forest)
        predicted_peak: float = 20.0,          # 0 to 100 (LSTM forecast)
        n_outlier_ips: int = 0,                # from DBSCAN
        active_threat_flags: list[str] = None, # Threat intel flags
        attack_type: str = "BENIGN",           # from Classifier
        attack_confidence: float = 0.90,       # 0.0 to 1.0
        financial_anomaly_factor: float = 0.0, # 0.0 to 1.0
        historical_avg: float = 20.0,
    ) -> dict:
        """
        Computes the complete, explainable 0–100 composite risk score.
        """
        flags = active_threat_flags or []
        asset_info = asset_registry.get_asset(asset)
        criticality = asset_info.get("criticality", 0.5) if asset_info else 0.5
        downstream_dependents = asset_registry.get_downstream_dependents(asset)
        
        # 1. Normalize individual risk factors (0.0 to 1.0)
        c_anomaly = min(1.0, max(0.0, float(anomaly_score)))
        
        # Attack severity factor
        att_key = str(attack_type).upper()
        base_attack_weight = ATTACK_WEIGHT_MAP.get(att_key, 0.40)
        c_attack = min(1.0, max(0.0, base_attack_weight * float(attack_confidence)))
        
        # Asset criticality factor
        c_criticality = min(1.0, max(0.0, float(criticality)))
        
        # Propagation blast radius factor
        prop_count = len(downstream_dependents)
        c_propagation = min(1.0, max(0.0, prop_count / 5.0))
        
        # Behavioral anomaly factor (from DBSCAN cluster outliers)
        c_behavior = min(1.0, max(0.0, n_outlier_ips * 0.20))
        
        # Threat intelligence factor
        c_threat_intel = 1.0 if len(flags) > 0 else 0.0

        # 2. Weighted Sum Formula
        w_anom = self.weights.get("ml_anomaly", 0.30)
        w_attk = self.weights.get("attack_severity", 0.20)
        w_crit = self.weights.get("asset_criticality", 0.20)
        w_prop = self.weights.get("propagation_impact", 0.15)
        w_behav = self.weights.get("behavioral_anomaly", 0.10)
        w_intel = self.weights.get("threat_intelligence", 0.05)

        raw_score = (
            w_anom  * c_anomaly +
            w_attk  * c_attack +
            w_crit  * c_criticality +
            w_prop  * c_propagation +
            w_behav * c_behavior +
            w_intel * c_threat_intel
        ) * 100.0

        overall_score = round(max(0.0, min(100.0, raw_score)), 1)
        severity = categorise(overall_score, self.thresholds)

        # 3. Dynamic Confidence Calculation
        n_sources = 1 + (1 if flags else 0) + (1 if n_outlier_ips > 0 else 0) + (1 if att_key != "BENIGN" else 0)
        source_factor = min(1.0, n_sources / 4.0)
        confidence = round(0.40 + 0.60 * source_factor * max(c_anomaly, float(attack_confidence)), 2)

        # 4. Human-Readable "Why is this High Risk?" Evidence Reasons
        reasons = []
        if c_anomaly > 0.60:
            reasons.append(f"High ML anomaly probability ({c_anomaly*100:.0f}%) detected by Isolation Forest")
        if att_key != "BENIGN":
            reasons.append(f"Attack classified as {att_key} with {attack_confidence*100:.0f}% confidence")
        if c_criticality >= 0.85:
            reasons.append(f"Target is a Tier-1 Critical Infrastructure asset ({asset_info.get('name', asset)})")
        if downstream_dependents:
            dep_str = ", ".join(downstream_dependents[:3])
            reasons.append(f"Cascading failure risk to {len(downstream_dependents)} downstream dependent services ({dep_str})")
        if n_outlier_ips > 0:
            reasons.append(f"Behavioral DBSCAN flagged {n_outlier_ips} abnormal entity cluster IPs")
        if flags:
            reasons.append(f"Threat intelligence matched {len(flags)} active indicators ({', '.join(flags[:2])})")
        if not reasons:
            reasons.append("Nominal baseline telemetry within safe statistical tolerances")

        # Monetary financial exposure in ₹ Crores
        base_exp = asset_info.get("financial_exposure_cr", 15.0) if asset_info else 15.0
        exposure_cr = round(base_exp * (overall_score / 100.0), 2)

        return {
            "asset": asset,
            "asset_name": asset_info.get("name", asset) if asset_info else asset,
            "risk_score": overall_score,
            "overall_risk": overall_score,
            "severity": severity,
            "risk_category": severity,
            "confidence": confidence,
            "reasons": reasons,
            "financial_exposure_cr": exposure_cr,
            "component_scores": {
                "ml_anomaly": round(c_anomaly * 100, 1),
                "attack_severity": round(c_attack * 100, 1),
                "asset_criticality": round(c_criticality * 100, 1),
                "propagation_impact": round(c_propagation * 100, 1),
                "behavioral_anomaly": round(c_behavior * 100, 1),
                "threat_intelligence": round(c_threat_intel * 100, 1),
            },
            "weights_used": self.weights,
            "affected_assets": downstream_dependents,
            "active_threat_flags": flags,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def calculate_risk(
        self,
        anomaly_score: float,
        attack_type: str = "BENIGN",
        asset_id: str = "TRAFFIC_CONTROL",
        is_anomaly: bool = False,
        threat_intel_flag: bool = False
    ) -> tuple[float, str]:
        """Convenience method returning (risk_score, risk_category)."""
        flags = ["THREAT_INTEL_MATCH"] if threat_intel_flag else []
        res = self.compute(
            asset=asset_id,
            anomaly_score=anomaly_score,
            attack_type=attack_type,
            active_threat_flags=flags
        )
        return res["risk_score"], res["risk_category"]

    def city_aggregate(self, asset_scores: list[dict]) -> dict:
        """Roll up per-asset scores into city-wide summary."""
        if not asset_scores:
            return {
                "overall_score": 0.0, "category": "NORMAL", "severity": "NORMAL",
                "financial_exposure_cr": 0.0, "assets_at_risk": 0
            }
        scores = [a["risk_score"] for a in asset_scores]
        avg_score = round(sum(scores) / len(scores), 1)
        max_score = max(scores)
        # Weighted towards peak asset risk
        city_score = round(0.4 * avg_score + 0.6 * max_score, 1)
        tot_exp = round(sum(a.get("financial_exposure_cr", 0.0) for a in asset_scores), 2)
        at_risk = sum(1 for a in asset_scores if a["risk_score"] >= self.thresholds.get("moderate", 40.0))

        return {
            "overall_score": city_score,
            "peak_asset_score": max_score,
            "average_score": avg_score,
            "category": categorise(city_score, self.thresholds),
            "severity": categorise(city_score, self.thresholds),
            "financial_exposure_cr": tot_exp,
            "assets_at_risk": at_risk,
            "total_monitored_assets": len(asset_scores),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


risk_engine = RiskEngine()
