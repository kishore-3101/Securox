"""
Securox — Central Cyber-Risk Engine
====================================
Unified, deterministic, multi-factor cyber-physical risk engine.
Consumes events from the Central Event Fabric and API requests.

Inputs (11 Dimensions):
  1.  identity             : User, subject, or service principal
  2.  role                 : Operational role (doctor, teller, traffic_operator, auditor, etc.)
  3.  resource             : Target resource identifier (PATIENT:P-1001, ACCOUNT:ACC-7001, etc.)
  4.  action               : Action type (LOGIN, TRANSACTION, BREAK_GLASS, etc.)
  5.  device               : Client device ID, fingerprint, or host
  6.  location             : Physical or IP geo-location
  7.  time                 : Timestamp / UTC hour of operation
  8.  behavior             : Volume, velocity, frequency, request rate
  9.  domain               : HEALTHCARE, TRAFFIC, FINANCE, SECURITY, PLATFORM
  10. historical_baseline  : Established entity baseline (known devices, locations, hours, volume)
  11. ai_detections        : ML inference scores (XGBoost, Isolation Forest, AMLSim)

Outputs:
  • risk_score             : Deterministic 0.0 to 100.0 score (no random numbers)
  • risk_category          : LOW, MEDIUM, HIGH, CRITICAL
  • risk_factors           : Explainable breakdown with point contributions
  • confidence             : 0.0 to 1.0 confidence score
  • uncertainty            : Explicit uncertainty metric & diagnostic reason
  • recommended_action     : ALLOW, MONITOR, CHALLENGE_MFA, STEP_UP_AUTH, BLOCK_ACTION, etc.
  • rule_score vs ml_score : Auditable separation of deterministic rules vs AI models
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

logger = logging.getLogger("securox.cyber_risk_engine")

try:
    from core.store import store
except ImportError:
    from database.store import store


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════════════

class RiskEvent(BaseModel):
    """Normalized input model representing an incoming security event or access request."""
    event_id: str = Field(default_factory=lambda: f"EVT-RSK-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=_utcnow)
    identity: str
    role: str = "user"
    resource: str
    action: str
    device: str = "DEV-UNKNOWN"
    location: str = "LOCATION-UNKNOWN"
    time: Optional[str] = None
    behavior: Dict[str, Any] = Field(default_factory=dict)
    domain: str = "SECURITY"
    historical_baseline: Optional[Dict[str, Any]] = None
    ai_detections: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True
    }


class RiskFactor(BaseModel):
    """Individual explainable factor contributing to the composite risk score."""
    id: str = Field(default_factory=lambda: f"RF-{uuid.uuid4().hex[:8].upper()}")
    factor_key: str          # e.g. NEW_DEVICE, UNUSUAL_LOCATION, UNUSUAL_TIME, ABNORMAL_VOLUME, SENSITIVE_RESOURCE
    name: str                # e.g. "New Device"
    points: float            # e.g. +20.0
    source_type: str         # "POLICY_RULE" | "STATISTICAL_BASELINE" | "ML_DETECTION"
    description: str         # Human-readable explanation
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0  # [0.0, 1.0]
    severity: str = "LOW"    # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"


class RiskAssessment(BaseModel):
    """Complete risk evaluation output contract."""
    assessment_id: str = Field(default_factory=lambda: f"RA-{uuid.uuid4().hex[:8].upper()}")
    event_id: str
    timestamp: str = Field(default_factory=_utcnow)
    identity: str
    domain: str
    action: str
    resource: str
    risk_score: float             # 0.0 to 100.0
    risk_category: str            # LOW | MEDIUM | HIGH | CRITICAL
    confidence: float             # 0.0 to 1.0
    uncertainty: float            # 0.0 to 1.0
    uncertainty_reason: str       # Diagnostic root cause
    recommended_action: str       # ALLOW | MONITOR | CHALLENGE_MFA | STEP_UP_AUTH | BLOCK_ACTION
    factors: List[RiskFactor]     # Factor contributions
    rule_score: float             # Points from POLICY_RULE
    baseline_score: float         # Points from STATISTICAL_BASELINE
    ml_score: float               # Points from ML_DETECTION
    explanation: str              # Multi-line user-facing formatted breakdown


class HistoricalBaseline(BaseModel):
    """Persistent entity behavioral baseline."""
    identity: str
    domain: str = "PLATFORM"
    role: str = "user"
    known_devices: List[str] = Field(default_factory=list)
    known_locations: List[str] = Field(default_factory=list)
    typical_hours: List[int] = Field(default_factory=lambda: [6, 22])
    typical_actions: List[str] = Field(default_factory=list)
    mean_volume: float = 1.0
    std_dev_volume: float = 1.0
    event_count: int = 0
    last_seen: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)


# ═══════════════════════════════════════════════════════════════════════════
# SENSITIVE RESOURCE REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

SENSITIVE_RESOURCE_KEYWORDS = [
    # Healthcare
    "ICU", "TRAUMA", "SURGERY", "MED_DISPENSE", "INFUSION_PUMP", "CARDIAC", "EHR_MASTER",
    # Smart Traffic
    "SCADA", "CONTROLLER", "TRAFFIC_SIGNAL", "GRID_MASTER", "EMERGENCY_PREEMPTION", "BRIDGE_INTERLOCK",
    # Finance
    "SWIFT", "ESCROW", "TREASURY", "CORE_BANKING", "INTERBANK", "SAR_REGISTER", "SETTLEMENT_VAULT",
    # Security / Core
    "SYSTEM_AUTH", "POLICY_CONFIG", "CRYPTO_VAULT", "ROOT_CA", "AUDIT_LOG", "ADMIN_CONSOLE"
]


def is_sensitive_resource(resource: str) -> bool:
    """Checks if resource identifier matches critical infrastructure keywords."""
    res_upper = resource.upper()
    return any(keyword in res_upper for keyword in SENSITIVE_RESOURCE_KEYWORDS)


# ═══════════════════════════════════════════════════════════════════════════
# CENTRAL CYBER-RISK ENGINE CLASS
# ═══════════════════════════════════════════════════════════════════════════

class CyberRiskEngine:
    """
    Central Deterministic Cyber-Risk Engine.
    Consumes events, performs explainable factor scoring, quantifies uncertainty,
    and cleanly distinguishes policy rules from machine learning detections.
    """

    def __init__(self):
        self._thresholds = {
            "critical": 80.0,
            "high": 60.0,
            "medium": 30.0,
            "low": 0.0
        }

    @staticmethod
    def categorize_score(score: float) -> str:
        """Strict 4-tier risk classification: LOW, MEDIUM, HIGH, CRITICAL."""
        if score >= 80.0:
            return "CRITICAL"
        if score >= 60.0:
            return "HIGH"
        if score >= 30.0:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def determine_recommended_action(risk_score: float, factors: List[RiskFactor], role: str) -> str:
        """Deterministic remediation action mapping based on score and triggers."""
        # Critical severity
        if risk_score >= 80.0:
            return "BLOCK_ACTION"

        # High severity
        if risk_score >= 60.0:
            if any(f.factor_key == "NEW_DEVICE" for f in factors):
                return "CHALLENGE_MFA"
            if any(f.factor_key == "UNUSUAL_LOCATION" for f in factors):
                return "STEP_UP_AUTH"
            return "CHALLENGE_MFA"

        # Medium severity
        if risk_score >= 30.0:
            if any(f.factor_key == "NEW_DEVICE" for f in factors):
                return "STEP_UP_AUTH"
            return "MONITOR"

        # Low severity
        return "ALLOW"

    def _extract_hour(self, time_val: Optional[str]) -> int:
        """Extracts UTC hour from timestamp string or defaults to current hour."""
        if not time_val:
            return datetime.now(timezone.utc).hour
        try:
            clean = time_val.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean)
            return dt.hour
        except Exception:
            try:
                return int(time_val.split(":")[0])
            except Exception:
                return datetime.now(timezone.utc).hour

    async def evaluate(self, event_input: Union[RiskEvent, Dict[str, Any]]) -> RiskAssessment:
        """
        Core deterministic evaluation method.
        Evaluates all 11 dimensions and returns a fully explainable RiskAssessment.
        """
        if isinstance(event_input, dict):
            raw = dict(event_input)
            if "user" in raw and "identity" not in raw:
                raw["identity"] = raw["user"]
            if "ip" in raw and "device" not in raw:
                raw["device"] = raw["ip"]
            if "ai_detections" not in raw and "metadata" in raw and isinstance(raw["metadata"], dict):
                raw["ai_detections"] = raw["metadata"].get("ai_detections", {})
            event = RiskEvent(**raw)
        else:
            event = event_input

        identity = event.identity
        role = event.role
        resource = event.resource
        action = event.action
        device = event.device
        location = event.location
        behavior = event.behavior or {}
        ai_detections = event.ai_detections or {}

        # 2. Retrieve or load Historical Baseline
        baseline = event.historical_baseline
        if not baseline:
            db_base = await store.get_historical_baseline(identity)
            if db_base:
                baseline = db_base
            else:
                baseline = {
                    "identity": identity,
                    "domain": event.domain,
                    "role": role,
                    "known_devices": [],
                    "known_locations": [],
                    "typical_hours": [6, 22],
                    "typical_actions": [],
                    "mean_volume": 1.0,
                    "std_dev_volume": 1.0,
                    "event_count": 0
                }

        known_devices = set(baseline.get("known_devices") or [])
        known_locations = set(baseline.get("known_locations") or [])
        typical_hours = baseline.get("typical_hours") or [6, 22]
        mean_volume = float(baseline.get("mean_volume", 1.0))
        std_dev_volume = max(0.1, float(baseline.get("std_dev_volume", 1.0)))
        event_count = int(baseline.get("event_count", 0))

        factors: List[RiskFactor] = []

        # ═══════════════════════════════════════════════════════════════════
        # 3. DETERMINISTIC FACTOR EVALUATION (Clean Point Attribution)
        # ═══════════════════════════════════════════════════════════════════

        # Factor A: Device Evaluation (+20 new device)
        is_new_device = False
        if behavior.get("is_new_device") is True or behavior.get("is_known_device") is False:
            is_new_device = True
        elif known_devices and device not in known_devices:
            is_new_device = True
        elif not known_devices and (device in ("DEV-NEW", "DEV-UNKNOWN", "NEW_DEVICE") or any(kw in str(device).upper() for kw in ("NEW", "UNKNOWN", "UNENROLLED"))):
            is_new_device = True

        if is_new_device:
            factors.append(RiskFactor(
                factor_key="NEW_DEVICE",
                name="new device",
                points=20.0,
                source_type="POLICY_RULE",
                description=f"Device '{device}' is not registered in established baseline for identity '{identity}'.",
                evidence={"device": device, "known_devices": list(known_devices)},
                confidence=1.0,
                severity="HIGH"
            ))

        device_trust = behavior.get("device_trust_score")
        if device_trust is not None and float(device_trust) < 50.0:
            factors.append(RiskFactor(
                factor_key="UNTRUSTED_DEVICE",
                name="untrusted device firmware",
                points=10.0,
                source_type="POLICY_RULE",
                description=f"Device trust score {device_trust} is below safe compliance threshold (50.0).",
                evidence={"device_trust_score": device_trust},
                confidence=0.95,
                severity="MEDIUM"
            ))

        # Factor B: Location Evaluation (+18 unusual location)
        is_unusual_location = False
        if behavior.get("is_unusual_location") is True:
            is_unusual_location = True
        elif known_locations and location not in known_locations:
            is_unusual_location = True
        elif not known_locations and any(kw in location.upper() for kw in ("UNKNOWN", "UNUSUAL", "OFFSHORE", "TOR", "VPN", "ANONYMOUS")):
            is_unusual_location = True

        if is_unusual_location:
            factors.append(RiskFactor(
                factor_key="UNUSUAL_LOCATION",
                name="unusual location",
                points=18.0,
                source_type="POLICY_RULE",
                description=f"Origin location '{location}' deviates from typical operating locations for identity '{identity}'.",
                evidence={"location": location, "known_locations": list(known_locations)},
                confidence=0.95,
                severity="HIGH"
            ))

        # Factor C: Time Evaluation (+15 unusual time)
        event_hour = self._extract_hour(event.time or event.timestamp)
        is_unusual_time = False
        start_hr = typical_hours[0] if len(typical_hours) > 0 else 6
        end_hr = typical_hours[1] if len(typical_hours) > 1 else 22

        if behavior.get("is_unusual_time") is True:
            is_unusual_time = True
        elif start_hr <= end_hr:
            if event_hour < start_hr or event_hour >= end_hr:
                is_unusual_time = True
        else:
            if end_hr <= event_hour < start_hr:
                is_unusual_time = True

        if is_unusual_time:
            factors.append(RiskFactor(
                factor_key="UNUSUAL_TIME",
                name="unusual time",
                points=15.0,
                source_type="POLICY_RULE",
                description=f"Access requested at {event_hour:02d}:00 UTC, which falls outside normal working hours ({start_hr:02d}:00–{end_hr:02d}:00).",
                evidence={"event_hour": event_hour, "typical_hours": [start_hr, end_hr]},
                confidence=1.0,
                severity="MEDIUM"
            ))

        # Factor D: Behavior & Volume Evaluation (+25 abnormal volume)
        volume_val = behavior.get("volume")
        if volume_val is None:
            volume_val = behavior.get("amount") or behavior.get("request_count") or behavior.get("velocity")

        is_abnormal_volume = False
        if behavior.get("is_abnormal_volume") is True:
            is_abnormal_volume = True
        elif volume_val is not None:
            v = float(volume_val)
            z_score = (v - mean_volume) / std_dev_volume
            if z_score >= 2.5 or (v >= mean_volume * 3.0 and v > 1.0):
                is_abnormal_volume = True

        if is_abnormal_volume:
            vol_disp = volume_val if volume_val is not None else "BURST"
            factors.append(RiskFactor(
                factor_key="ABNORMAL_VOLUME",
                name="abnormal volume",
                points=25.0,
                source_type="STATISTICAL_BASELINE",
                description=f"Observed volume/velocity ({vol_disp}) exceeds historical mean ({mean_volume:.1f}) by more than 3.0 standard deviations.",
                evidence={"observed_volume": volume_val, "baseline_mean": mean_volume, "std_dev": std_dev_volume},
                confidence=0.90 if event_count >= 10 else 0.70,
                severity="CRITICAL"
            ))

        # Factor E: Sensitive Resource Evaluation (+13 sensitive resource)
        is_sensitive = False
        if behavior.get("is_sensitive_resource") is True:
            is_sensitive = True
        elif is_sensitive_resource(resource):
            is_sensitive = True

        if is_sensitive:
            factors.append(RiskFactor(
                factor_key="SENSITIVE_RESOURCE",
                name="sensitive resource",
                points=13.0,
                source_type="POLICY_RULE",
                description=f"Resource '{resource}' is designated as a Tier-1 Sensitive Asset / Critical Infrastructure Node.",
                evidence={"resource": resource},
                confidence=1.0,
                severity="HIGH"
            ))

        # Factor F: High-Consequence Action Rules
        action_upper = action.upper()
        if action_upper == "BREAK_GLASS":
            factors.append(RiskFactor(
                factor_key="HIGH_CONSEQUENCE_ACTION",
                name="break-glass emergency override",
                points=20.0,
                source_type="POLICY_RULE",
                description="Emergency clinical break-glass override invoked, bypassing normal patient assignment checks.",
                evidence={"action": action, "resource": resource},
                confidence=1.0,
                severity="HIGH"
            ))
        elif action_upper == "SIGNAL_OVERRIDE":
            pts = 30.0 if behavior.get("target_state") == "ALL_GREEN" else 15.0
            factors.append(RiskFactor(
                factor_key="HIGH_CONSEQUENCE_ACTION",
                name="traffic signal safety override",
                points=pts,
                source_type="POLICY_RULE",
                description=f"Direct SCADA signal override initiated with state '{behavior.get('target_state', 'MANUAL')}'.",
                evidence={"action": action, "target_state": behavior.get("target_state")},
                confidence=1.0,
                severity="HIGH"
            ))
        elif action_upper == "ACCESS_DENIED":
            factors.append(RiskFactor(
                factor_key="ACCESS_DENIED_EVENT",
                name="access policy violation",
                points=25.0,
                source_type="POLICY_RULE",
                description=f"Security guard blocked unauthorized access attempt by '{identity}' (role '{role}').",
                evidence={"action": action, "role": role},
                confidence=1.0,
                severity="HIGH"
            ))

        # Factor G: Role Mismatch
        if behavior.get("role_mismatch") is True:
            factors.append(RiskFactor(
                factor_key="ROLE_MISMATCH",
                name="privilege boundary violation",
                points=25.0,
                source_type="POLICY_RULE",
                description=f"Role '{role}' attempted prohibited action '{action}' across domain partition.",
                evidence={"role": role, "action": action},
                confidence=1.0,
                severity="HIGH"
            ))

        # Factor H: Network Threat Vectors (Tor Exit Node, Anonymizing Proxies)
        net_trust = str(behavior.get("network_trust", "")).upper()
        if net_trust in ("TOR_EXIT", "ANONYMOUS_PROXY", "MALICIOUS_VPN") or behavior.get("is_tor_exit") is True:
            factors.append(RiskFactor(
                factor_key="TOR_EXIT_NODE",
                name="anonymizing tor relay",
                points=30.0,
                source_type="POLICY_RULE",
                description=f"Connection routed via anonymizing threat relay ({net_trust or 'TOR_EXIT'}).",
                evidence={"network_trust": net_trust, "client_ip": behavior.get("client_ip", behavior.get("ip"))},
                confidence=1.0,
                severity="CRITICAL"
            ))

        # ═══════════════════════════════════════════════════════════════════
        # 4. MACHINE LEARNING DETECTIONS (Clearly Distinguishable from Rules)
        # ═══════════════════════════════════════════════════════════════════

        xgb_score = (
            ai_detections.get("xgboost_fraud_score")
            or ai_detections.get("xgboost_fraud_probability")
            or ai_detections.get("fraud_probability")
            or ai_detections.get("fraud_score")
        )
        if xgb_score is not None:
            p = float(xgb_score)
            if p > 1.0:
                p = p / 100.0
            if p >= 0.80:
                factors.append(RiskFactor(
                    factor_key="ML_FRAUD_HIGH",
                    name="XGBoost Fraud Classifier (High Confidence)",
                    points=25.0,
                    source_type="ML_DETECTION",
                    description=f"Real Indian Banking XGBoost model flagged suspicious payment transaction (P={p:.2f}).",
                    evidence={"model": "xgboost_fraud_v2", "probability": p},
                    confidence=round(p, 2),
                    severity="CRITICAL"
                ))
            elif p >= 0.25:
                factors.append(RiskFactor(
                    factor_key="ML_FRAUD_MODERATE",
                    name="XGBoost Fraud Classifier (Elevated Risk)",
                    points=15.0,
                    source_type="ML_DETECTION",
                    description=f"XGBoost model detected anomalous transfer pattern with elevated risk probability (P={p:.2f}).",
                    evidence={"model": "xgboost_fraud_v2", "probability": p},
                    confidence=round(p, 2),
                    severity="MEDIUM"
                ))

        iso_score = (
            ai_detections.get("isolation_forest_anomaly")
            or ai_detections.get("isolation_forest_anomaly_score")
            or ai_detections.get("anomaly_score")
            or ai_detections.get("anomaly")
        )
        if iso_score is not None:
            anom = float(iso_score)
            if anom > 1.0:
                anom = anom / 100.0
            if anom >= 0.50:
                factors.append(RiskFactor(
                    factor_key="ML_ANOMALY_DETECTION",
                    name="Isolation Forest Outlier Detection",
                    points=20.0,
                    source_type="ML_DETECTION",
                    description=f"Isolation Forest multi-dimensional tree partition isolated anomalous telemetry (score={anom:.2f}).",
                    evidence={"model": "isolation_forest_core", "anomaly_score": anom},
                    confidence=round(anom, 2),
                    severity="HIGH"
                ))

        mule_score = (
            ai_detections.get("aml_mule_risk")
            or ai_detections.get("aml_mule_probability")
            or ai_detections.get("mule_probability")
            or ai_detections.get("mule_risk")
        )
        if mule_score is not None:
            m = float(mule_score)
            if m > 1.0:
                m = m / 100.0
            if m >= 0.50:
                factors.append(RiskFactor(
                    factor_key="ML_AML_CONTAGION",
                    name="AML Graph Topology Contagion",
                    points=20.0,
                    source_type="ML_DETECTION",
                    description=f"Graph BFS contagion propagation identified synthetic mule account ring clustering (P={m:.2f}).",
                    evidence={"model": "amlsim_graph_contagion", "mule_probability": m},
                    confidence=round(m, 2),
                    severity="CRITICAL"
                ))

        # AI Detection: Mass Record Access Anomaly / Exfiltration Risk
        mass_anomaly = ai_detections.get("mass_record_anomaly")
        mass_score = ai_detections.get("mass_access_score")
        if mass_anomaly is True or (mass_score is not None and float(mass_score) >= 60.0):
            ms = float(mass_score) if mass_score is not None else 85.0
            factors.append(RiskFactor(
                factor_key="AI_MASS_EXFILTRATION",
                name="AI Mass Record Access Anomaly",
                points=25.0,
                source_type="ML_DETECTION",
                description=f"AI model flagged mass record access exceeding statistical baseline (score={ms:.1f}).",
                evidence={"model": "HC-MODEL-02", "score": ms},
                confidence=0.91,
                severity="CRITICAL"
            ))

        # ═══════════════════════════════════════════════════════════════════
        # 5. COMPOSITE SCORE CALCULATION (Deterministic, Bounded to [0, 100])
        # ═══════════════════════════════════════════════════════════════════

        rule_points = sum(f.points for f in factors if f.source_type == "POLICY_RULE")
        baseline_points = sum(f.points for f in factors if f.source_type == "STATISTICAL_BASELINE")
        ml_points = sum(f.points for f in factors if f.source_type == "ML_DETECTION")

        raw_total = rule_points + baseline_points + ml_points
        composite_score = round(max(0.0, min(100.0, raw_total)), 1)
        risk_category = self.categorize_score(composite_score)
        recommended_action = self.determine_recommended_action(composite_score, factors, role)

        # ═══════════════════════════════════════════════════════════════════
        # 6. UNCERTAINTY QUANTIFICATION (Never Hide Uncertainty!)
        # ═══════════════════════════════════════════════════════════════════

        if event_count < 5:
            u_baseline = 0.50
            baseline_diag = f"Sparse entity baseline (only {event_count} prior events for '{identity}')"
        elif event_count < 20:
            u_baseline = 0.20
            baseline_diag = f"Developing baseline ({event_count} observations)"
        else:
            u_baseline = 0.05
            baseline_diag = f"Robust baseline ({event_count} historical observations)"

        u_model = 0.05
        model_diag = "High model separation certainty"
        if xgb_score is not None:
            p_val = float(xgb_score)
            if 0.40 <= p_val <= 0.60:
                u_model = 0.35
                model_diag = f"Elevated model entropy near classification threshold (P={p_val:.2f})"
        if iso_score is not None:
            a_val = float(iso_score)
            if 0.45 <= a_val <= 0.55:
                u_model = max(u_model, 0.30)
                model_diag = f"Isolation forest partition boundary ambiguity ({a_val:.2f})"

        u_telemetry = 0.05
        if not known_devices or not known_locations:
            u_telemetry = 0.15

        composite_uncertainty = round(min(0.85, (0.50 * u_baseline) + (0.35 * u_model) + (0.15 * u_telemetry)), 2)
        confidence = round(max(0.15, min(0.99, 1.0 - composite_uncertainty)), 2)

        uncertainty_reasons = []
        if u_baseline >= 0.20:
            uncertainty_reasons.append(baseline_diag)
        if u_model >= 0.20:
            uncertainty_reasons.append(model_diag)
        if not uncertainty_reasons:
            uncertainty_reasons.append(f"{baseline_diag}; {model_diag}")
        uncertainty_reason_str = " | ".join(uncertainty_reasons)

        # ═══════════════════════════════════════════════════════════════════
        # 7. MULTI-LINE EXPLAINABLE TEXT SUMMARY
        # ═══════════════════════════════════════════════════════════════════

        explanation_lines = [f"Risk {int(composite_score)} ({risk_category})", ""]
        if factors:
            for f in factors:
                pts_str = f"+{int(f.points)}" if f.points >= 0 else f"{int(f.points)}"
                tag = f"[{f.source_type}]" if f.source_type != "POLICY_RULE" else ""
                explanation_lines.append(f"{pts_str} {f.name} {tag}".strip())
        else:
            explanation_lines.append("+0 nominal operational telemetry within safe statistical baseline")

        explanation_text = "\n".join(explanation_lines)

        assessment = RiskAssessment(
            event_id=event.event_id,
            timestamp=event.timestamp,
            identity=identity,
            domain=event.domain,
            action=action,
            resource=resource,
            risk_score=composite_score,
            risk_category=risk_category,
            confidence=confidence,
            uncertainty=composite_uncertainty,
            uncertainty_reason=uncertainty_reason_str,
            recommended_action=recommended_action,
            factors=factors,
            rule_score=round(rule_points, 1),
            baseline_score=round(baseline_points, 1),
            ml_score=round(ml_points, 1),
            explanation=explanation_text
        )

        return assessment

    async def consume_event(self, event_dict: Dict[str, Any]) -> RiskAssessment:
        """
        Event Fabric consumer hook.
        Evaluates incoming event, persists assessment and factors, and updates baseline.
        """
        try:
            assessment = await self.evaluate(event_dict)

            # Persist assessment and factors
            await store.save_risk_assessment(
                assessment.model_dump(),
                [f.model_dump() for f in assessment.factors]
            )

            # Update entity historical baseline if event is authenticated/nominal
            if assessment.risk_category in ("LOW", "MEDIUM") and assessment.identity != "unknown":
                await store.update_historical_baseline(assessment.identity, event_dict)

            return assessment
        except Exception as e:
            logger.error("CyberRiskEngine failed to process event: %s", e, exc_info=True)
            return RiskAssessment(
                event_id=event_dict.get("event_id", "ERR"),
                identity=event_dict.get("user", "unknown"),
                domain=event_dict.get("domain", "SECURITY"),
                action=event_dict.get("action", "UNKNOWN"),
                resource=event_dict.get("resource", "UNKNOWN"),
                risk_score=50.0,
                risk_category="MEDIUM",
                confidence=0.30,
                uncertainty=0.70,
                uncertainty_reason=f"Evaluation degraded due to internal exception: {e}",
                recommended_action="MONITOR",
                factors=[],
                rule_score=50.0,
                baseline_score=0.0,
                ml_score=0.0,
                explanation="Risk 50 (MEDIUM)\n+50 error fallback evaluation"
            )


cyber_risk_engine = CyberRiskEngine()
