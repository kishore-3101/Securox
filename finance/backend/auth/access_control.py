"""
Securox — Enterprise RBAC + ABAC + Adaptive Access Control Engine
Combines Role-Based Permissions, Attribute-Based Context Evaluation,
AI Cyber Risk Scoring, and Automated Policy Enforcement.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import math


class Action(str, Enum):
    VIEW = "VIEW"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    APPROVE = "APPROVE"
    EXPORT = "EXPORT"
    DOWNLOAD = "DOWNLOAD"
    DISPATCH = "DISPATCH"
    INVESTIGATE = "INVESTIGATE"
    BLOCK = "BLOCK"
    RESOLVE = "RESOLVE"
    CONFIGURE = "CONFIGURE"


class ResourceType(str, Enum):
    # Core / Platform
    SYSTEM_CONFIG = "SYSTEM_CONFIG"
    USER_MANAGEMENT = "USER_MANAGEMENT"
    SECURITY_POLICY = "SECURITY_POLICY"
    AUDIT_LOG = "AUDIT_LOG"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    AI_MODEL_CONFIG = "AI_MODEL_CONFIG"
    SOC_DASHBOARD = "SOC_DASHBOARD"

    # Healthcare
    PATIENT_RECORD = "PATIENT_RECORD"
    CLINICAL_NOTE = "CLINICAL_NOTE"
    PRESCRIPTION = "PRESCRIPTION"
    LAB_REPORT = "LAB_REPORT"
    BED_MANAGEMENT = "BED_MANAGEMENT"
    AMBULANCE_DISPATCH = "AMBULANCE_DISPATCH"
    BILLING_INVOICE = "BILLING_INVOICE"
    HOSPITAL_IT_ASSET = "HOSPITAL_IT_ASSET"

    # Smart Traffic
    TRAFFIC_SIGNAL = "TRAFFIC_SIGNAL"
    CCTV_FEED = "CCTV_FEED"
    TRAFFIC_INCIDENT = "TRAFFIC_INCIDENT"
    GREEN_CORRIDOR = "GREEN_CORRIDOR"
    ROAD_MAINTENANCE = "ROAD_MAINTENANCE"
    TRAFFIC_ANALYTICS = "TRAFFIC_ANALYTICS"
    CITIZEN_ALERT = "CITIZEN_ALERT"

    # Finance
    BANK_ACCOUNT = "BANK_ACCOUNT"
    TRANSACTION = "TRANSACTION"
    FRAUD_CASE = "FRAUD_CASE"
    AML_ALERT = "AML_ALERT"
    RISK_EXPOSURE = "RISK_EXPOSURE"
    COMPLIANCE_REPORT = "COMPLIANCE_REPORT"


class Decision(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_MONITORED = "ALLOW_MONITORED"
    STEP_UP_AUTH = "STEP_UP_AUTH"
    BLOCK = "BLOCK"


@dataclass
class AccessContext:
    user_id: str
    username: str
    role: str
    domain: str
    department: Optional[str] = None
    device_id: Optional[str] = None
    device_trust: float = 100.0  # 0 to 100
    is_known_device: bool = True
    client_ip: str = "127.0.0.1"
    geo_location: str = "Bengaluru, IN"
    previous_geo: Optional[str] = None
    previous_login_time: Optional[datetime] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resource_id: Optional[str] = None
    patient_assignment: Optional[str] = None  # e.g., assigned, unassigned
    record_count: int = 1
    transaction_amount: float = 0.0
    network_trust: str = "CORPORATE_SECURE"  # CORPORATE_SECURE, GUEST_WIFI, PUBLIC_VPN, TOR_EXIT
    auth_strength: str = "MFA_HARDWARE"  # PASSWORD_ONLY, MFA_SMS, MFA_APP, MFA_HARDWARE


@dataclass
class PolicyEvaluationResult:
    decision: Decision
    risk_score: float
    risk_category: str  # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    factors: List[Dict[str, Any]]
    policy_triggered: Optional[str] = None
    incident_created: bool = False
    incident_id: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════
# RBAC PERMISSIONS MATRIX
# ═══════════════════════════════════════════════════════════════════════

ROLE_PERMISSIONS: Dict[str, Dict[ResourceType, Set[Action]]] = {
    # ── Super Admin ──────────────────────────────────────────────────
    "superadmin": {
        ResourceType.SYSTEM_CONFIG: {Action.VIEW, Action.UPDATE, Action.CONFIGURE},
        ResourceType.USER_MANAGEMENT: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.DELETE},
        ResourceType.SECURITY_POLICY: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.CONFIGURE},
        ResourceType.AUDIT_LOG: {Action.VIEW, Action.EXPORT},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.AI_MODEL_CONFIG: {Action.VIEW, Action.CONFIGURE},
        ResourceType.SOC_DASHBOARD: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW},
    },
    "admin": {
        ResourceType.SYSTEM_CONFIG: {Action.VIEW, Action.UPDATE, Action.CONFIGURE},
        ResourceType.USER_MANAGEMENT: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.SECURITY_POLICY: {Action.VIEW, Action.UPDATE},
        ResourceType.AUDIT_LOG: {Action.VIEW, Action.EXPORT},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.SOC_DASHBOARD: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW},
    },

    # ── Healthcare Roles ─────────────────────────────────────────────
    "hospital_admin": {
        ResourceType.BED_MANAGEMENT: {Action.VIEW, Action.UPDATE, Action.APPROVE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.AMBULANCE_DISPATCH: {Action.VIEW},
        ResourceType.BILLING_INVOICE: {Action.VIEW, Action.APPROVE},
        ResourceType.HOSPITAL_IT_ASSET: {Action.VIEW},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW},
    },
    "doctor": {
        ResourceType.PATIENT_RECORD: {Action.VIEW, Action.UPDATE},
        ResourceType.CLINICAL_NOTE: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.PRESCRIPTION: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.LAB_REPORT: {Action.VIEW},
        ResourceType.AMBULANCE_DISPATCH: {Action.VIEW},
    },
    "nurse": {
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.CLINICAL_NOTE: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.PRESCRIPTION: {Action.VIEW},
        ResourceType.LAB_REPORT: {Action.VIEW},
        ResourceType.BED_MANAGEMENT: {Action.VIEW, Action.UPDATE},
    },
    "ambulance_driver": {
        ResourceType.AMBULANCE_DISPATCH: {Action.VIEW, Action.UPDATE, Action.DISPATCH},
    },
    "paramedic": {
        ResourceType.AMBULANCE_DISPATCH: {Action.VIEW, Action.UPDATE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.CLINICAL_NOTE: {Action.CREATE, Action.UPDATE},
    },
    "reception": {
        ResourceType.PATIENT_RECORD: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.BED_MANAGEMENT: {Action.VIEW},
        ResourceType.BILLING_INVOICE: {Action.VIEW},
    },
    "pharmacist": {
        ResourceType.PRESCRIPTION: {Action.VIEW, Action.APPROVE, Action.UPDATE},
    },
    "lab_technician": {
        ResourceType.LAB_REPORT: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.APPROVE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
    },
    "billing_staff": {
        ResourceType.BILLING_INVOICE: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.APPROVE},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
    },
    "emergency_coordinator": {
        ResourceType.AMBULANCE_DISPATCH: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.DISPATCH},
        ResourceType.BED_MANAGEMENT: {Action.VIEW, Action.UPDATE},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW},
    },
    "hospital_security": {
        ResourceType.HOSPITAL_IT_ASSET: {Action.VIEW, Action.INVESTIGATE, Action.BLOCK},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.AUDIT_LOG: {Action.VIEW},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
    },
    "patient": {
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.PRESCRIPTION: {Action.VIEW},
        ResourceType.LAB_REPORT: {Action.VIEW},
        ResourceType.BILLING_INVOICE: {Action.VIEW},
    },

    # ── Smart Traffic Roles ──────────────────────────────────────────
    "traffic_operator": {
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW, Action.UPDATE, Action.APPROVE},
        ResourceType.CCTV_FEED: {Action.VIEW},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.RESOLVE},
        ResourceType.GREEN_CORRIDOR: {Action.VIEW, Action.DISPATCH},
        ResourceType.TRAFFIC_ANALYTICS: {Action.VIEW},
    },
    "traffic_police": {
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW, Action.CREATE, Action.UPDATE},
        ResourceType.CCTV_FEED: {Action.VIEW},
        ResourceType.GREEN_CORRIDOR: {Action.VIEW, Action.DISPATCH},
    },
    "traffic_supervisor": {
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW, Action.UPDATE, Action.APPROVE},
        ResourceType.CCTV_FEED: {Action.VIEW},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.TRAFFIC_ANALYTICS: {Action.VIEW, Action.EXPORT},
    },
    "camera_operator": {
        ResourceType.CCTV_FEED: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW, Action.CREATE},
    },
    "signal_technician": {
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW, Action.UPDATE, Action.CONFIGURE},
    },
    "emergency_traffic": {
        ResourceType.GREEN_CORRIDOR: {Action.VIEW, Action.CREATE, Action.DISPATCH},
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW, Action.UPDATE},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW, Action.UPDATE},
    },
    "road_maintenance": {
        ResourceType.ROAD_MAINTENANCE: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.RESOLVE},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW},
    },
    "transport_authority": {
        ResourceType.TRAFFIC_ANALYTICS: {Action.VIEW, Action.EXPORT},
        ResourceType.TRAFFIC_INCIDENT: {Action.VIEW},
    },
    "traffic_analyst": {
        ResourceType.TRAFFIC_ANALYTICS: {Action.VIEW, Action.EXPORT},
    },
    "traffic_cybersecurity": {
        ResourceType.TRAFFIC_SIGNAL: {Action.VIEW, Action.INVESTIGATE, Action.BLOCK},
        ResourceType.CCTV_FEED: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.AUDIT_LOG: {Action.VIEW},
    },
    "citizen": {
        ResourceType.CITIZEN_ALERT: {Action.VIEW},
        ResourceType.TRAFFIC_ANALYTICS: {Action.VIEW},
    },

    # ── Finance Roles ────────────────────────────────────────────────
    "finance_admin": {
        ResourceType.BANK_ACCOUNT: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW},
        ResourceType.RISK_EXPOSURE: {Action.VIEW, Action.EXPORT},
        ResourceType.COMPLIANCE_REPORT: {Action.VIEW, Action.APPROVE},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW},
    },
    "branch_manager": {
        ResourceType.BANK_ACCOUNT: {Action.VIEW, Action.UPDATE},
        ResourceType.TRANSACTION: {Action.VIEW, Action.APPROVE},
        ResourceType.FRAUD_CASE: {Action.VIEW},
    },
    "teller": {
        ResourceType.BANK_ACCOUNT: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW, Action.CREATE},
    },
    "relationship_manager": {
        ResourceType.BANK_ACCOUNT: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW},
    },
    "fraud_analyst": {
        ResourceType.TRANSACTION: {Action.VIEW, Action.INVESTIGATE, Action.BLOCK},
        ResourceType.FRAUD_CASE: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.INVESTIGATE},
    },
    "aml_analyst": {
        ResourceType.TRANSACTION: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.AML_ALERT: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.INVESTIGATE, Action.RESOLVE},
        ResourceType.COMPLIANCE_REPORT: {Action.VIEW, Action.CREATE},
    },
    "risk_analyst": {
        ResourceType.RISK_EXPOSURE: {Action.VIEW, Action.EXPORT},
        ResourceType.TRANSACTION: {Action.VIEW},
        ResourceType.COMPLIANCE_REPORT: {Action.VIEW},
    },
    "compliance_officer": {
        ResourceType.COMPLIANCE_REPORT: {Action.VIEW, Action.CREATE, Action.APPROVE, Action.EXPORT},
        ResourceType.AUDIT_LOG: {Action.VIEW},
        ResourceType.AML_ALERT: {Action.VIEW},
    },
    "soc_analyst": {
        ResourceType.SOC_DASHBOARD: {Action.VIEW, Action.INVESTIGATE},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW, Action.CREATE, Action.UPDATE, Action.INVESTIGATE, Action.RESOLVE, Action.BLOCK},
        ResourceType.AUDIT_LOG: {Action.VIEW, Action.EXPORT},
        ResourceType.SECURITY_POLICY: {Action.VIEW},
    },
    "auditor": {
        # READ ONLY ACROSS THE BOARD
        ResourceType.AUDIT_LOG: {Action.VIEW, Action.EXPORT},
        ResourceType.TRANSACTION: {Action.VIEW},
        ResourceType.BANK_ACCOUNT: {Action.VIEW},
        ResourceType.PATIENT_RECORD: {Action.VIEW},
        ResourceType.SECURITY_INCIDENT: {Action.VIEW},
        ResourceType.SECURITY_POLICY: {Action.VIEW},
    },
    "customer": {
        ResourceType.BANK_ACCOUNT: {Action.VIEW},
        ResourceType.TRANSACTION: {Action.VIEW},
    },
}

# Aliases for existing roles
ROLE_PERMISSIONS["health_operator"] = ROLE_PERMISSIONS["hospital_security"]
ROLE_PERMISSIONS["finance_investigator"] = ROLE_PERMISSIONS["fraud_analyst"]
ROLE_PERMISSIONS["emergency_commander"] = ROLE_PERMISSIONS["emergency_coordinator"]
ROLE_PERMISSIONS["analyst"] = ROLE_PERMISSIONS["soc_analyst"]


# ═══════════════════════════════════════════════════════════════════════
# RBAC + ABAC + RISK POLICY ENGINE
# ═══════════════════════════════════════════════════════════════════════

class AccessControlEngine:
    """Enterprise-grade access decision & risk evaluation engine."""

    def __init__(self):
        pass

    def check_rbac(self, role: str, resource: ResourceType, action: Action) -> bool:
        """Evaluate if user's role has static permission for resource and action."""
        perms = ROLE_PERMISSIONS.get(role, {})
        allowed_actions = perms.get(resource, set())
        return action in allowed_actions

    def evaluate_access(
        self,
        context: AccessContext,
        resource: ResourceType,
        action: Action
    ) -> PolicyEvaluationResult:
        """
        Comprehensive access evaluation:
        1. RBAC baseline check
        2. ABAC contextual risk calculation (Device, Geo, Time, Volume, Scope)
        3. Adaptive access policy decision (ALLOW, MONITOR, STEP_UP, BLOCK)
        """
        factors: List[Dict[str, Any]] = []
        base_risk = 5.0  # nominal baseline risk

        # ── Step 1: RBAC Check ───────────────────────────────────────
        has_rbac = self.check_rbac(context.role, resource, action)
        if not has_rbac:
            return PolicyEvaluationResult(
                decision=Decision.BLOCK,
                risk_score=95.0,
                risk_category="CRITICAL",
                reason=f"Access Denied by RBAC: Role '{context.role}' does not possess permission '{action.value}' on resource '{resource.value}'.",
                factors=[{
                    "factor": "RBAC Violation",
                    "points": 95,
                    "description": f"Role '{context.role}' has no {action.value} grant on {resource.value}."
                }],
                policy_triggered="STRICT_RBAC_ENFORCEMENT",
                incident_created=True
            )

        # ── Step 2: ABAC Contextual Risk Evaluation ──────────────────

        # Factor A: Device Trust & Known Device Status
        if not context.is_known_device:
            points = 25.0
            base_risk += points
            factors.append({
                "factor": "Unregistered / Unknown Device",
                "points": points,
                "description": f"Device ID '{context.device_id or 'UNKNOWN'}' is not enrolled in MDM registry."
            })
        elif context.device_trust < 50.0:
            points = 20.0
            base_risk += points
            factors.append({
                "factor": "Degraded Device Trust",
                "points": points,
                "description": f"Device trust score {context.device_trust:.1f}/100 indicates missing patches or anomalous behavior."
            })

        # Factor B: Location Anomaly / Impossible Travel
        if context.previous_geo and context.geo_location:
            if context.previous_geo != context.geo_location and context.previous_login_time:
                hours_diff = (context.timestamp - context.previous_login_time).total_seconds() / 3600.0
                if hours_diff < 1.0 and ("London" in context.geo_location or "New York" in context.geo_location or "Tokyo" in context.geo_location):
                    points = 35.0
                    base_risk += points
                    factors.append({
                        "factor": "Impossible Travel Velocity Anomaly",
                        "points": points,
                        "description": f"Location changed from '{context.previous_geo}' to '{context.geo_location}' in {hours_diff*60:.1f} minutes."
                    })
                elif context.previous_geo != context.geo_location:
                    points = 15.0
                    base_risk += points
                    factors.append({
                        "factor": "Unusual Geolocation Shift",
                        "points": points,
                        "description": f"Access initiated from uncustomary location: {context.geo_location}."
                    })

        # Factor C: Off-Hours Clinical / Financial Access
        hour = context.timestamp.hour
        if hour >= 23 or hour <= 4:
            points = 18.0
            base_risk += points
            factors.append({
                "factor": "Off-Hours Operational Access",
                "points": points,
                "description": f"Sensitive access initiated at {hour:02d}:{context.timestamp.minute:02d} outside normal operational shift."
            })

        # Factor D: Data Access Volume & Exfiltration Indicators
        if context.record_count > 500:
            points = 30.0
            base_risk += points
            factors.append({
                "factor": "Mass Data Volume / Exfiltration Spike",
                "points": points,
                "description": f"Attempting batch retrieval of {context.record_count:,} records in a single query."
            })
        elif context.record_count > 50:
            points = 15.0
            base_risk += points
            factors.append({
                "factor": "Elevated Access Volume",
                "points": points,
                "description": f"Requested batch size ({context.record_count} items) exceeds standard 25-record page threshold."
            })

        # Factor E: Clinical Patient Assignment Scope (Doctors & Nurses)
        if context.role in ("doctor", "nurse") and resource in (ResourceType.PATIENT_RECORD, ResourceType.CLINICAL_NOTE):
            if context.patient_assignment == "unassigned":
                points = 28.0
                base_risk += points
                factors.append({
                    "factor": "Unassigned Patient Scope Violation",
                    "points": points,
                    "description": f"Clinician has no active care assignment or consulting order for target patient."
                })

        # Factor F: Network Reputation / Public VPN
        if context.network_trust == "TOR_EXIT":
            points = 40.0
            base_risk += points
            factors.append({
                "factor": "Tor Exit Node / Anonymizing Proxy",
                "points": points,
                "description": f"Connection originates from confirmed Tor exit relay ({context.client_ip})."
            })
        elif context.network_trust in ("PUBLIC_VPN", "GUEST_WIFI"):
            points = 12.0
            base_risk += points
            factors.append({
                "factor": "Untrusted / Public Wi-Fi Network",
                "points": points,
                "description": f"Connection routed via non-corporate network segment ({context.network_trust})."
            })

        # Factor G: High-Value Financial Thresholds
        if resource == ResourceType.TRANSACTION and context.transaction_amount > 100_000:
            points = 22.0
            base_risk += points
            factors.append({
                "factor": "High-Value Transaction Threshold Exceeded",
                "points": points,
                "description": f"Transaction amount ₹{context.transaction_amount:,.2f} exceeds standard operational limit."
            })

        # ── Step 3: Compute Final Clamped Score & Decision ───────────
        final_risk = min(100.0, max(0.0, base_risk))

        if final_risk >= 75.0:
            category = "CRITICAL"
            decision = Decision.BLOCK
            reason = "ACCESS RESTRICTED: Request blocked by adaptive security policy due to compounded high-risk contextual anomalies."
            policy = "CRITICAL_RISK_CONTAINMENT_POLICY"
            incident_created = True
        elif final_risk >= 50.0:
            category = "HIGH"
            decision = Decision.STEP_UP_AUTH
            reason = "STEP-UP AUTHENTICATION REQUIRED: High risk context requires secondary biometric/hardware MFA challenge."
            policy = "HIGH_RISK_STEP_UP_POLICY"
            incident_created = False
        elif final_risk >= 25.0:
            category = "MEDIUM"
            decision = Decision.ALLOW_MONITORED
            reason = "ACCESS ALLOWED WITH ENHANCED AUDIT: Moderate anomaly detected; operational access logged to security audit stream."
            policy = "MONITORED_ACCESS_POLICY"
            incident_created = False
        else:
            category = "LOW"
            decision = Decision.ALLOW
            reason = "ACCESS GRANTED: Verified identity, trusted device, and nominal contextual risk indicators."
            policy = "NOMINAL_ACCESS_POLICY"
            incident_created = False

        return PolicyEvaluationResult(
            decision=decision,
            risk_score=round(final_risk, 1),
            risk_category=category,
            reason=reason,
            factors=factors,
            policy_triggered=policy,
            incident_created=incident_created
        )


# Global singleton access control engine
access_engine = AccessControlEngine()
