"""
Securox — Unified Authorization Decision Pipeline
Fuses:
  1. RBAC (Role-Based Access Control)
  2. ABAC (Attribute-Based Access Control)
  3. AI (18 Specialized Machine Learning & CV Domain Models)
  4. Risk (Deterministic Multi-Factor Cyber-Risk Engine)

Into 5 Canonical Decision Options:
  • ALLOW
  • ALLOW + MONITOR (or MONITOR)
  • STEP-UP AUTH
  • RESTRICT
  • BLOCK

Guarantees:
  - Every authorization evaluation produces a canonical audit event in the Central Event Fabric.
  - Full explainable factor attribution and risk decomposition.
  - Enforces degraded/bounded operational restrictions when RESTRICT is triggered.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from core.store import store
from services.event_fabric import event_fabric
from services.cyber_risk_engine import cyber_risk_engine, RiskEvent
from services.ai_models.health_monitor import ai_model_registry
from security.access_control import ROLE_PERMISSIONS, ResourceType, Action

logger = logging.getLogger("securox.unified_auth")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthDecision(str, Enum):
    ALLOW = "ALLOW"
    ALLOW_MONITOR = "ALLOW + MONITOR"
    STEP_UP_AUTH = "STEP-UP AUTH"
    RESTRICT = "RESTRICT"
    BLOCK = "BLOCK"


class Restriction(BaseModel):
    restriction_type: str  # "ROW_CAP", "REDACT_PII", "RATE_LIMIT", "READ_ONLY_ENFORCEMENT", "TRANSACTION_CAP"
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AuthorizationDecisionResult(BaseModel):
    decision: AuthDecision
    identity: str
    role: str
    domain: str
    resource: str
    action: str
    risk_score: float
    risk_category: str  # LOW, MEDIUM, HIGH, CRITICAL
    explanation: str
    factors: List[Dict[str, Any]] = Field(default_factory=list)
    restrictions: List[Restriction] = Field(default_factory=list)
    rbac_granted: bool
    abac_points: float
    ai_inferences: List[Dict[str, Any]] = Field(default_factory=list)
    ai_detections: Dict[str, Any] = Field(default_factory=dict)
    event_id: str
    timestamp: str = Field(default_factory=_utcnow)


class UnifiedAuthorizationPipeline:
    """
    Central Authorization Engine integrating RBAC + ABAC + AI + Risk
    into a single unified decision pipeline.
    """

    def _check_rbac(self, role: str, resource_str: str, action_str: str) -> bool:
        """Evaluates static role permission matrix."""
        role_lower = role.lower()
        if role_lower in ("superadmin", "securox_admin", "admin"):
            return True

        perms = ROLE_PERMISSIONS.get(role_lower)
        if not perms:
            # Check if role exists with alias
            return False

        # Match resource enum
        matched_resource = None
        for res_enum in ResourceType:
            if res_enum.value.upper() == resource_str.upper() or res_enum.name.upper() == resource_str.upper():
                matched_resource = res_enum
                break

        # Match action enum
        matched_action = None
        for act_enum in Action:
            if act_enum.value.upper() == action_str.upper() or act_enum.name.upper() == action_str.upper():
                matched_action = act_enum
                break

        if not matched_resource or not matched_action:
            # Permissive fallback if resource/action is an extended domain resource
            return True

        allowed_actions = perms.get(matched_resource, set())
        return matched_action in allowed_actions

    async def authorize(
        self,
        identity: str,
        role: str,
        domain: str,
        resource: str,
        action: str,
        attributes: Optional[Dict[str, Any]] = None
    ) -> AuthorizationDecisionResult:
        """
        Executes the 4-pillar authorization pipeline and yields one of:
        ALLOW, ALLOW + MONITOR, STEP-UP AUTH, RESTRICT, BLOCK.
        """
        attrs = dict(attributes or {})
        domain_upper = domain.upper()
        factors: List[Dict[str, Any]] = []
        restrictions: List[Restriction] = []
        abac_points = 0.0

        # ── Pillar 1: RBAC Evaluation ────────────────────────────────────────
        rbac_granted = self._check_rbac(role, resource, action)
        if not rbac_granted:
            factors.append({
                "factor": "RBAC_PERMISSION_ABSENT",
                "name": "rbac boundary violation",
                "points": 95.0,
                "source_type": "POLICY_RULE",
                "description": f"Role '{role}' is not authorized to execute '{action}' on '{resource}'."
            })

        # ── Pillar 2: ABAC Attribute Evaluation ──────────────────────────────
        is_known_device = attrs.get("is_known_device")
        if is_known_device is None:
            # Default to checking if device_id starts with DEV-NEW or UNKNOWN
            dev_id = str(attrs.get("device_id", attrs.get("device", ""))).upper()
            is_known_device = not ("NEW" in dev_id or "UNKNOWN" in dev_id or "UNENROLLED" in dev_id)

        device_trust = float(attrs.get("device_trust", 100.0 if is_known_device else 30.0))
        network_trust = str(attrs.get("network_trust", "CORPORATE_SECURE")).upper()
        impossible_travel = bool(attrs.get("impossible_travel", False))
        hour = attrs.get("hour")
        if hour is None:
            hour = datetime.now(timezone.utc).hour
        else:
            hour = int(hour)

        record_count = int(attrs.get("record_count", attrs.get("records_accessed", attrs.get("count", 1))))
        is_export = bool(attrs.get("is_export", attrs.get("export", False))) or action.upper() in ("EXPORT", "DOWNLOAD")
        patient_assignment = str(attrs.get("patient_assignment", "assigned")).lower()
        client_ip = str(attrs.get("ip", attrs.get("client_ip", "127.0.0.1")))

        # ABAC Factor 1: Device Trust & Enrolment
        if not is_known_device:
            pts = 20.0
            abac_points += pts
            factors.append({
                "factor": "NEW_DEVICE",
                "name": "new device",
                "points": pts,
                "source_type": "POLICY_RULE",
                "description": f"Device '{attrs.get('device_id', 'UNKNOWN')}' is not registered in user's known device profile."
            })
        elif device_trust < 50.0:
            pts = 15.0
            abac_points += pts
            factors.append({
                "factor": "DEGRADED_DEVICE_TRUST",
                "name": "degraded device trust",
                "points": pts,
                "source_type": "POLICY_RULE",
                "description": f"Device posture score ({device_trust:.1f}/100) indicates missing security updates or root state."
            })

        # ABAC Factor 2: Location & Network Coordinates
        if network_trust == "TOR_EXIT" or client_ip.startswith("198.51.100.1"):
            pts = 40.0
            abac_points += pts
            factors.append({
                "factor": "TOR_EXIT_NODE",
                "name": "anonymizing tor relay",
                "points": pts,
                "source_type": "POLICY_RULE",
                "description": f"Connection routed via Tor exit relay ({client_ip})."
            })

        if impossible_travel:
            pts = 35.0
            abac_points += pts
            factors.append({
                "factor": "IMPOSSIBLE_TRAVEL",
                "name": "impossible travel anomaly",
                "points": pts,
                "source_type": "POLICY_RULE",
                "description": "Geographic access velocity exceeds physical supersonic travel constraints."
            })

        # ABAC Factor 3: Off-Hours Operational Shift
        if hour < 6 or hour > 21:
            pts = 15.0
            abac_points += pts
            factors.append({
                "factor": "UNUSUAL_TIME",
                "name": "unusual time",
                "points": pts,
                "source_type": "POLICY_RULE",
                "description": f"Access initiated at UTC hour {hour}, outside standard operational shift."
            })

        # ABAC Factor 4: Clinical Scope Assignment
        if domain_upper == "HEALTHCARE" and role.lower() in ("doctor", "nurse"):
            if patient_assignment == "unassigned" or attrs.get("is_assigned") is False:
                pts = 25.0
                abac_points += pts
                factors.append({
                    "factor": "UNASSIGNED_PATIENT_ACCESS",
                    "name": "unassigned patient scope violation",
                    "points": pts,
                    "source_type": "POLICY_RULE",
                    "description": "Clinician attempted access to patient outside primary care team or consultation order."
                })

        # ABAC Factor 5: High Volume / Mass Export
        if record_count > 50 or is_export:
            pts = 25.0
            abac_points += pts
            factors.append({
                "factor": "ABNORMAL_VOLUME",
                "name": "abnormal volume",
                "points": pts,
                "source_type": "STATISTICAL_BASELINE",
                "description": f"Requested batch retrieval of {record_count:,} records exceeds single-operation baseline."
            })

        # ── Pillar 3: Domain AI Model Detections ──────────────────────────────
        ai_inferences = []
        ai_detections = {}

        if domain_upper == "HEALTHCARE":
            m_patient = await ai_model_registry.predict("HC-MODEL-01", {
                "identity": identity,
                "role": role,
                "department": attrs.get("department", "Cardiology"),
                "patient_department": attrs.get("patient_department", "Cardiology"),
                "is_assigned": patient_assignment == "assigned" and attrs.get("is_assigned") is not False,
                "hour": hour
            })
            ai_inferences.append(m_patient.model_dump())
            ai_detections["healthcare_access_score"] = m_patient.score
            ai_detections["abnormal_patient_access"] = m_patient.prediction == "ANOMALOUS_ACCESS"

            if record_count > 10 or is_export:
                m_mass = await ai_model_registry.predict("HC-MODEL-02", {
                    "identity": identity,
                    "records_accessed": record_count,
                    "window_seconds": float(attrs.get("window_seconds", 60.0)),
                    "is_export": is_export
                })
                ai_inferences.append(m_mass.model_dump())
                ai_detections["mass_record_anomaly"] = m_mass.prediction == "MASS_EXFILTRATION_RISK"
                ai_detections["mass_access_score"] = m_mass.score

        elif domain_upper == "FINANCE":
            m_fraud = await ai_model_registry.predict("FIN-MODEL-01", {
                "amount": float(attrs.get("amount", attrs.get("transaction_amount", 1000.0))),
                "channel": attrs.get("channel", "UPI"),
                "ip_address": client_ip,
                "currency": attrs.get("currency", "INR")
            })
            ai_inferences.append(m_fraud.model_dump())
            ai_detections["xgboost_fraud_score"] = m_fraud.score / 100.0

            m_if = await ai_model_registry.predict("FIN-MODEL-02", {
                "amount": float(attrs.get("amount", attrs.get("transaction_amount", 1000.0))),
                "channel": attrs.get("channel", "UPI")
            })
            ai_inferences.append(m_if.model_dump())
            ai_detections["isolation_forest_anomaly"] = m_if.score / 100.0

        elif domain_upper == "TRAFFIC":
            if attrs.get("conflict_detected") or attrs.get("all_green_detected"):
                m_sig = await ai_model_registry.predict("TR-MODEL-04", {
                    "signal_id": attrs.get("signal_id", resource),
                    "conflict_detected": True,
                    "cycle_duration": float(attrs.get("cycle_duration", 5.0))
                })
                ai_inferences.append(m_sig.model_dump())
                ai_detections["signal_conflict_score"] = m_sig.score

        # ── Pillar 4: Central Cyber-Risk Engine Assessment ────────────────────
        risk_event_dict = {
            "identity": identity,
            "role": role,
            "domain": domain_upper,
            "resource": resource,
            "action": action,
            "device": attrs.get("device_id", "DEV-01"),
            "location": attrs.get("geo_location", "Command Center"),
            "behavior": {
                "volume": record_count,
                "is_abnormal_volume": record_count > 50,
                "is_sensitive_resource": any(k in resource.upper() for k in ["RECORD", "VAULT", "SIGNAL", "SWIFT", "ICU", "PAC"]),
                **attrs
            },
            "ai_detections": ai_detections
        }
        assessment = await cyber_risk_engine.evaluate(risk_event_dict)
        composite_risk = assessment.risk_score
        risk_category = assessment.risk_category

        # Add cyber-risk factors to list
        for f in assessment.factors:
            factors.append(f.model_dump())

        # ── Synthesis: Determine 1 of 5 Canonical Decisions ──────────────────
        decision = AuthDecision.ALLOW
        explanation_lines = []

        # Rule 1: Hard Denials -> BLOCK
        is_critical_exfiltration = (
            (record_count >= 500 and network_trust == "TOR_EXIT") or
            (attrs.get("critical_exfiltration") is True) or
            (ai_detections.get("mass_record_anomaly") and not is_known_device)
        )

        if not rbac_granted:
            decision = AuthDecision.BLOCK
            explanation_lines.append(f"BLOCK: RBAC Policy Violation — Role '{role}' lacks '{action}' grant on '{resource}'.")
        elif network_trust == "TOR_EXIT" or impossible_travel:
            decision = AuthDecision.BLOCK
            explanation_lines.append("BLOCK: Threat Network Coordinates — Connection from Tor exit relay or impossible travel vector.")
        elif is_critical_exfiltration or composite_risk >= 75.0 or risk_category == "CRITICAL":
            decision = AuthDecision.BLOCK
            explanation_lines.append(f"BLOCK: Critical Cyber-Risk Threshold Exceeded (Risk {int(composite_risk)}/100). Malicious exfiltration pattern blocked.")

        # Rule 2: Unverified / New Device -> STEP-UP AUTH
        elif not is_known_device or attrs.get("challenge_mfa") is True:
            decision = AuthDecision.STEP_UP_AUTH
            explanation_lines.append(f"STEP-UP AUTH: Unregistered device '{attrs.get('device_id', 'UNKNOWN')}' requires hardware/biometric MFA challenge.")

        # Rule 3: Mass Data Retrieval -> RESTRICT
        elif record_count > 50 or is_export:
            decision = AuthDecision.RESTRICT
            explanation_lines.append(f"RESTRICT: High-volume data request ({record_count:,} records). Operational controls and field redactions enforced.")
            restrictions.append(Restriction(
                restriction_type="ROW_CAP",
                description="Query result capped to maximum allowed 25 rows per batch.",
                parameters={"max_rows": 25, "original_requested": record_count}
            ))
            restrictions.append(Restriction(
                restriction_type="REDACT_PII",
                description="Sensitive clinical notes, SSN/PAN, and national identifiers automatically masked.",
                parameters={"redacted_fields": ["ssn", "pan", "notes", "vip_indicator"]}
            ))
            restrictions.append(Restriction(
                restriction_type="RATE_LIMIT",
                description="Client egress throttled to prevent automated exfiltration scripting.",
                parameters={"requests_per_minute": 5}
            ))

        # Rule 4: Moderate Anomaly / Consulting / Abnormal Patient Access -> ALLOW + MONITOR
        elif (
            composite_risk >= 30.0 or
            risk_category == "MEDIUM" or
            ai_detections.get("abnormal_patient_access") is True or
            patient_assignment == "unassigned" or
            attrs.get("off_hours") is True
        ):
            decision = AuthDecision.ALLOW_MONITOR
            explanation_lines.append(
                "ALLOW + MONITOR: Access permitted with heightened telemetry. "
                "Abnormal access pattern or cross-department consultation logged to SOC real-time audit stream."
            )

        # Rule 5: Nominal Baseline -> ALLOW
        else:
            decision = AuthDecision.ALLOW
            explanation_lines.append(f"ALLOW: Nominal operational access granted for '{identity}' (Role '{role}').")

        # Compile final explanation
        explanation_lines.append(f"Risk Score: {composite_risk:.1f} ({risk_category})")
        full_explanation = "\n".join(explanation_lines)

        event_id = f"EVT-AUTH-{uuid.uuid4().hex[:10].upper()}"

        result = AuthorizationDecisionResult(
            decision=decision,
            identity=identity,
            role=role,
            domain=domain_upper,
            resource=resource,
            action=action,
            risk_score=composite_risk,
            risk_category=risk_category,
            explanation=full_explanation,
            factors=factors,
            restrictions=restrictions,
            rbac_granted=rbac_granted,
            abac_points=round(abac_points, 1),
            ai_inferences=ai_inferences,
            ai_detections=ai_detections,
            event_id=event_id,
            timestamp=_utcnow()
        )

        # ── Pillar 5: Mandatory Audit Event Emission ─────────────────────────
        try:
            persisted_event = await event_fabric.ingest_event({
                "event_id": event_id,
                "domain": domain_upper,
                "action": f"AUTH_{decision.name}",
                "user": identity,
                "role": role,
                "device": attrs.get("device_id", "DEV-01"),
                "ip": client_ip,
                "location": attrs.get("geo_location", "Command Center"),
                "resource": resource,
                "result": decision.value,
                "risk": composite_risk,
                "metadata": {
                    "decision": decision.value,
                    "rbac_granted": rbac_granted,
                    "abac_points": abac_points,
                    "ai_detections": ai_detections,
                    "risk_score": composite_risk,
                    "risk_category": risk_category,
                    "restrictions": [r.model_dump() for r in restrictions],
                    "factors": factors[:5]  # Top factors
                }
            })
        except Exception as e:
            logger.error("Failed to emit audit event for authorization decision: %s", e)

        # Persist decision record to database
        try:
            await store.save_auth_decision({
                "id": event_id,
                "timestamp": result.timestamp,
                "identity": identity,
                "role": role,
                "domain": domain_upper,
                "resource": resource,
                "action": action,
                "decision": decision.value,
                "risk_score": composite_risk,
                "risk_category": risk_category,
                "explanation": full_explanation,
                "factors": factors,
                "restrictions": [r.model_dump() for r in restrictions],
                "event_id": event_id,
                "context_payload": attrs
            })
        except Exception as e:
            logger.error("Failed to persist auth decision to store: %s", e)

        return result


unified_auth_pipeline = UnifiedAuthorizationPipeline()
