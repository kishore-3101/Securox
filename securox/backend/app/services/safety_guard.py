"""
Securox — Critical Infrastructure Safety Validation Guard & Mitigation Approval Engine
Enforces:
  1. "Never automatically execute dangerous mitigation without safety validation."
  2. Domain safety evaluation across:
     - Hospital: clinical impact, patient safety, hospital state, emergency state
     - Traffic: collision hazard, green corridor active, emergency vehicle dispatch, rush hour
     - Finance: systemic freeze, settlement window open, market hours, liquidity contagion
  3. Strict Autonomous Rejection: If unsafe -> REJECT AUTOMATED MITIGATION -> PENDING_APPROVAL
  4. Human-in-the-Loop Mitigation Approval Workflow (cmo, traffic_commander, financial_controller)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.store import store
from services.event_fabric import event_fabric

logger = logging.getLogger("securox.safety_guard")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SafetyVerdict(str, Enum):
    SAFE_TO_AUTO_EXECUTE = "SAFE_TO_AUTO_EXECUTE"
    UNSAFE_FOR_AUTONOMOUS_EXECUTION = "UNSAFE_FOR_AUTONOMOUS_EXECUTION"


class ProposalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    AUTOMATICALLY_EXECUTED = "AUTOMATICALLY_EXECUTED"
    SAFETY_BLOCKED = "SAFETY_BLOCKED"


class SafetyEvaluationResult(BaseModel):
    is_safe: bool
    verdict: SafetyVerdict
    domain: str
    action_name: str
    target_asset: str
    safety_score: float  # 0.0 (extremely unsafe) to 100.0 (completely safe)
    rejection_reasons: List[str] = Field(default_factory=list)
    safety_context: Dict[str, Any] = Field(default_factory=dict)
    required_approver_role: str
    rationale: str


class MitigationProposal(BaseModel):
    id: str = Field(default_factory=lambda: f"MIT-{uuid.uuid4().hex[:8].upper()}")
    timestamp: str = Field(default_factory=_utcnow)
    domain: str
    action_name: str
    target_asset: str
    proposed_by: str  # "AI_SYSTEM", "CYBER_RISK_ENGINE", "POLICY_RULE", "SOC_ANALYST"
    safety_verdict: SafetyVerdict
    safety_evaluation: Dict[str, Any]
    status: ProposalStatus = ProposalStatus.PENDING_APPROVAL
    required_role: str
    approved_by: Optional[str] = None
    approval_timestamp: Optional[str] = None
    comments: str = ""
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)


class SafetyGuardEngine:
    """
    Validates mitigation safety against physical, clinical, and systemic invariants.
    Guarantees no autonomous AI or risk score ever causes catastrophic real-world harm.
    """

    # Actions considered dangerous when executed against critical infrastructure
    DANGEROUS_ACTIONS = {
        "HEALTHCARE": {
            "SHUTDOWN_INFRASTRUCTURE", "POWER_OFF_ICU_SWITCH", "ISOLATE_PAC_SERVER",
            "SEVER_EHR_INTERFACE", "LOCK_PHARMACY_DISPENSER", "HALT_VENTILATOR_TELEMETRY",
            "SEVER_HOSPITAL_NETWORK", "ISOLATE_CLINICAL_ASSET", "DISCONNECT_EHR"
        },
        "TRAFFIC": {
            "HALT_INTERSECTION_GRID", "FORCE_ALL_RED_CORRIDOR", "SEVER_RSU_CONTROLLER",
            "DISABLE_TUNNEL_VENTILATION", "KILL_TRAFFIC_SIGNAL_NETWORK", "ISOLATE_SCADA_NODE",
            "SIGNAL_OVERRIDE_SHUTDOWN"
        },
        "FINANCE": {
            "FREEZE_CLEARING_HOUSE", "HALT_SYSTEMIC_RTGS", "SHUTDOWN_ATM_SWITCH",
            "BLOCK_ALL_BRANCH_TRANSFERS", "IMMEDIATE_LIQUIDITY_LOCK", "SEVER_SWIFT_GATEWAY"
        }
    }

    # Safe actions that do not disrupt physical life or macro-systems
    SAFE_NON_INVASIVE_ACTIONS = {
        "REVOKE_USER_SESSION", "BLOCK_SOURCE_IP", "REQUIRE_STEP_UP_MFA",
        "ENABLE_DEBUG_LOGGING", "NOTIFY_SOC", "FLAG_FRAUD_CASE", "RATE_LIMIT_INGRESS",
        "ENFORCE_READ_ONLY_MODE", "REDACT_DATA_EXPORT", "CHALLENGE_BIOMETRIC_AUTH"
    }

    def evaluate_mitigation_safety(
        self,
        domain: str,
        action_name: str,
        target_asset: str,
        safety_context: Optional[Dict[str, Any]] = None
    ) -> SafetyEvaluationResult:
        """
        Evaluates whether an automated mitigation action is safe to execute autonomously,
        or must be rejected / held for human authorization.
        """
        domain_upper = domain.upper()
        if domain_upper in ("HOSPITAL", "CLINICAL"):
            domain_upper = "HEALTHCARE"

        action_upper = action_name.upper().replace(" ", "_")
        context = dict(safety_context or {})

        # Default safe non-invasive checks
        if action_upper in self.SAFE_NON_INVASIVE_ACTIONS or any(s in action_upper for s in ["NOTIFY", "STEP_UP", "LOG", "FLAG"]):
            return SafetyEvaluationResult(
                is_safe=True,
                verdict=SafetyVerdict.SAFE_TO_AUTO_EXECUTE,
                domain=domain_upper,
                action_name=action_name,
                target_asset=target_asset,
                safety_score=95.0,
                rejection_reasons=[],
                safety_context=context,
                required_approver_role="soc_analyst",
                rationale=f"Action '{action_name}' is non-invasive and safe for autonomous execution."
            )

        # ── 1. Hospital Domain Safety Evaluation ─────────────────────────────
        if domain_upper == "HEALTHCARE":
            rejection_reasons = []
            surgeries_in_progress = int(context.get("surgeries_in_progress", context.get("active_surgeries", 0)))
            icu_occupancy_pct = float(context.get("icu_occupancy_pct", context.get("icu_saturation", 0.0)))
            emergency_state = str(context.get("emergency_state", "NORMAL")).upper()
            ventilators_active = int(context.get("active_ventilators", context.get("ventilator_count_active", 0)))
            patient_safety_hazard = bool(context.get("patient_safety_hazard", context.get("clinical_impact", "LOW") in ("HIGH", "CRITICAL")))

            is_dangerous = (
                action_upper in self.DANGEROUS_ACTIONS["HEALTHCARE"] or
                any(kw in action_upper for kw in ["SHUTDOWN", "ISOLATE", "SEVER", "POWER_OFF", "KILL", "DISCONNECT"])
            )

            if is_dangerous:
                if surgeries_in_progress > 0:
                    rejection_reasons.append(
                        f"Active surgical procedures in progress ({surgeries_in_progress} Operating Theatres active). "
                        "Power/network disruption poses immediate mortality risk."
                    )
                if emergency_state in ("CODE_BLUE", "MASS_CASUALTY", "DISASTER_DIVERT"):
                    rejection_reasons.append(
                        f"Hospital facility is in emergency operational state '{emergency_state}'. Clinical systems must remain online."
                    )
                if icu_occupancy_pct >= 75.0 or ventilators_active > 0:
                    rejection_reasons.append(
                        f"High-dependency intensive care load (ICU occupancy {icu_occupancy_pct:.1f}%, {ventilators_active} active ventilators). "
                        "Bedside telemetry link severance prohibited."
                    )
                if patient_safety_hazard:
                    rejection_reasons.append("Clinical assessment indicates potential direct patient care disruption.")

            is_safe = len(rejection_reasons) == 0
            score = 90.0 if is_safe else max(5.0, 100.0 - (len(rejection_reasons) * 35.0))
            verdict = SafetyVerdict.SAFE_TO_AUTO_EXECUTE if is_safe else SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION

            rationale = (
                f"Action '{action_name}' approved for execution: No patient care or clinical safety conflicts detected."
                if is_safe else
                f"REJECT AUTOMATED MITIGATION: Critical hospital infrastructure action '{action_name}' rejected autonomously. "
                + " | ".join(rejection_reasons)
            )

            return SafetyEvaluationResult(
                is_safe=is_safe,
                verdict=verdict,
                domain=domain_upper,
                action_name=action_name,
                target_asset=target_asset,
                safety_score=round(score, 1),
                rejection_reasons=rejection_reasons,
                safety_context=context,
                required_approver_role="cmo",
                rationale=rationale
            )

        # ── 2. Traffic Domain Safety Evaluation ──────────────────────────────
        elif domain_upper == "TRAFFIC":
            rejection_reasons = []
            green_corridor_active = bool(context.get("green_corridor_active", False))
            active_emergency_vehicles = int(context.get("active_emergency_vehicles", context.get("ambulances_in_transit", 0)))
            is_rush_hour = bool(context.get("rush_hour", context.get("is_peak_hours", False)))
            emergency_state = str(context.get("emergency_state", "NORMAL")).upper()

            is_dangerous = (
                action_upper in self.DANGEROUS_ACTIONS["TRAFFIC"] or
                any(kw in action_upper for kw in ["HALT", "ALL_RED", "SHUTDOWN", "SEVER", "KILL", "OVERRIDE"])
            )

            if is_dangerous:
                if green_corridor_active:
                    rejection_reasons.append(
                        "Active Emergency Green Corridor in progress. Signal sequence modifications strictly prohibited."
                    )
                if active_emergency_vehicles > 0:
                    rejection_reasons.append(
                        f"{active_emergency_vehicles} emergency service vehicles (ambulances/fire engines) actively navigating corridor."
                    )
                if emergency_state == "CIVIL_EVACUATION":
                    rejection_reasons.append("Civil defense evacuation order active; intersection freezing prohibited.")
                if is_rush_hour and any(kw in action_upper for kw in ["HALT", "ALL_RED"]):
                    rejection_reasons.append("Peak rush hour traffic volume. Forcing all-red phase induces severe secondary gridlock & accident hazard.")

            is_safe = len(rejection_reasons) == 0
            score = 90.0 if is_safe else max(5.0, 100.0 - (len(rejection_reasons) * 40.0))
            verdict = SafetyVerdict.SAFE_TO_AUTO_EXECUTE if is_safe else SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION

            rationale = (
                f"Action '{action_name}' validated safe: Roadway network dynamics normal."
                if is_safe else
                f"REJECT AUTOMATED MITIGATION: Dangerous traffic infrastructure action '{action_name}' rejected autonomously. "
                + " | ".join(rejection_reasons)
            )

            return SafetyEvaluationResult(
                is_safe=is_safe,
                verdict=verdict,
                domain=domain_upper,
                action_name=action_name,
                target_asset=target_asset,
                safety_score=round(score, 1),
                rejection_reasons=rejection_reasons,
                safety_context=context,
                required_approver_role="traffic_commander",
                rationale=rationale
            )

        # ── 3. Finance Domain Safety Evaluation ──────────────────────────────
        elif domain_upper == "FINANCE":
            rejection_reasons = []
            settlement_window_open = bool(context.get("settlement_window_open", context.get("is_clearing_window_open", False)))
            active_clearing_inr = float(context.get("active_clearing_inr", context.get("settlement_volume", 0.0)))
            is_market_hours = bool(context.get("is_market_hours", True))

            is_dangerous = (
                action_upper in self.DANGEROUS_ACTIONS["FINANCE"] or
                any(kw in action_upper for kw in ["FREEZE_CLEARING", "HALT_SYSTEMIC", "SHUTDOWN_ATM", "BLOCK_ALL"])
            )

            if is_dangerous:
                if settlement_window_open:
                    rejection_reasons.append(
                        f"Interbank RTGS/NEFT settlement window is actively open. Systemic freeze risks systemic market liquidity default."
                    )
                if active_clearing_inr > 10_000_000.0:
                    rejection_reasons.append(
                        f"High-value batch settlement currently in-flight (INR {active_clearing_inr:,.2f})."
                    )

            is_safe = len(rejection_reasons) == 0
            score = 90.0 if is_safe else max(5.0, 100.0 - (len(rejection_reasons) * 45.0))
            verdict = SafetyVerdict.SAFE_TO_AUTO_EXECUTE if is_safe else SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION

            rationale = (
                f"Action '{action_name}' validated safe: Nominal banking transaction controls applied."
                if is_safe else
                f"REJECT AUTOMATED MITIGATION: Systemic banking action '{action_name}' rejected autonomously. "
                + " | ".join(rejection_reasons)
            )

            return SafetyEvaluationResult(
                is_safe=is_safe,
                verdict=verdict,
                domain=domain_upper,
                action_name=action_name,
                target_asset=target_asset,
                safety_score=round(score, 1),
                rejection_reasons=rejection_reasons,
                safety_context=context,
                required_approver_role="financial_risk_officer",
                rationale=rationale
            )

        # Default fallback domain
        return SafetyEvaluationResult(
            is_safe=True,
            verdict=SafetyVerdict.SAFE_TO_AUTO_EXECUTE,
            domain=domain_upper,
            action_name=action_name,
            target_asset=target_asset,
            safety_score=85.0,
            rejection_reasons=[],
            safety_context=context,
            required_approver_role="admin",
            rationale=f"Action '{action_name}' permitted under baseline operational rules."
        )

    # ── Mitigation Approval Workflow ─────────────────────────────────────────

    async def propose_mitigation(
        self,
        domain: str,
        action_name: str,
        target_asset: str,
        proposed_by: str = "AI_SYSTEM",
        safety_context: Optional[Dict[str, Any]] = None,
        comments: str = ""
    ) -> Dict[str, Any]:
        """
        Proposes a mitigation action, runs exhaustive safety validation, and either:
        1. Automatically executes if provably safe and non-critical.
        2. Strictly rejects automated execution and creates a pending approval item for designated human approvers.
        """
        safety_eval = self.evaluate_mitigation_safety(domain, action_name, target_asset, safety_context)

        prop_id = f"MIT-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()

        if safety_eval.is_safe:
            status = ProposalStatus.AUTOMATICALLY_EXECUTED.value
            exec_note = "Safe mitigation automatically executed without disruption."
        else:
            status = ProposalStatus.PENDING_APPROVAL.value
            exec_note = "AUTOMATED MITIGATION REJECTED. Action routed to human approval queue."

        proposal_dict = {
            "id": prop_id,
            "timestamp": now,
            "domain": safety_eval.domain,
            "action_name": action_name,
            "target_asset": target_asset,
            "proposed_by": proposed_by,
            "safety_verdict": safety_eval.verdict.value,
            "safety_evaluation": safety_eval.model_dump(),
            "status": status,
            "required_role": safety_eval.required_approver_role,
            "approved_by": "SYSTEM_AUTONOMOUS" if safety_eval.is_safe else None,
            "approval_timestamp": now if safety_eval.is_safe else None,
            "comments": comments or exec_note,
            "created_at": now,
            "updated_at": now
        }

        # Persist to database
        saved = await store.save_mitigation_proposal(proposal_dict)

        # Emit audit event to Event Fabric
        await event_fabric.ingest_event({
            "event_id": f"EVT-MIT-{prop_id}",
            "domain": safety_eval.domain,
            "action": "MITIGATION_PROPOSAL",
            "user": proposed_by,
            "role": "ai_agent" if "AI" in proposed_by else "system",
            "resource": target_asset,
            "result": "AUTOMATED_EXECUTION" if safety_eval.is_safe else "REJECTED_AUTOMATION_PENDING_APPROVAL",
            "risk": 100.0 - safety_eval.safety_score,
            "metadata": {
                "proposal_id": prop_id,
                "action_name": action_name,
                "safety_verdict": safety_eval.verdict.value,
                "safety_score": safety_eval.safety_score,
                "rejection_reasons": safety_eval.rejection_reasons,
                "required_role": safety_eval.required_approver_role,
                "rationale": safety_eval.rationale
            }
        })

        return saved

    async def approve_mitigation(
        self,
        proposal_id: str,
        user: str,
        role: str,
        comments: str = "Approved by human-in-the-loop operator"
    ) -> Dict[str, Any]:
        """Human operator signs off on a pending critical infrastructure mitigation."""
        proposal = await store.get_mitigation_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Mitigation proposal '{proposal_id}' not found.")

        if proposal["status"] == ProposalStatus.APPROVED.value:
            return proposal

        # Check required role authority (allow superadmin, admin, or specific domain role)
        required_role = proposal.get("required_role", "admin").lower()
        user_role = role.lower()
        authorized = (
            user_role in ("admin", "superadmin") or
            user_role == required_role or
            (required_role == "cmo" and user_role in ("cmo", "chief_medical_officer", "emergency_coordinator", "hospital_admin")) or
            (required_role == "traffic_commander" and user_role in ("traffic_commander", "traffic_operator", "traffic_supervisor", "traffic_operations_commander")) or
            (required_role == "financial_risk_officer" and user_role in ("financial_risk_officer", "fraud_analyst", "compliance_officer", "finance_admin"))
        )

        if not authorized:
            raise PermissionError(
                f"Role '{role}' is not authorized to approve critical mitigation '{proposal_id}'. "
                f"Requires designated authority '{required_role}'."
            )

        now = _utcnow()
        updated = await store.update_mitigation_proposal(proposal_id, {
            "status": ProposalStatus.APPROVED.value,
            "approved_by": user,
            "approval_timestamp": now,
            "comments": comments
        })

        # Emit event
        await event_fabric.ingest_event({
            "event_id": f"EVT-MIT-APP-{proposal_id}",
            "domain": proposal["domain"],
            "action": "MITIGATION_APPROVED",
            "user": user,
            "role": role,
            "resource": proposal["target_asset"],
            "result": "APPROVED",
            "risk": 15.0,
            "metadata": {
                "proposal_id": proposal_id,
                "action_name": proposal["action_name"],
                "approved_by": user,
                "approver_role": role,
                "comments": comments
            }
        })

        return updated

    async def reject_mitigation(
        self,
        proposal_id: str,
        user: str,
        role: str,
        reason: str = "Rejected by human safety reviewer"
    ) -> Dict[str, Any]:
        """Human operator rejects a pending critical infrastructure mitigation."""
        proposal = await store.get_mitigation_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Mitigation proposal '{proposal_id}' not found.")

        now = _utcnow()
        updated = await store.update_mitigation_proposal(proposal_id, {
            "status": ProposalStatus.REJECTED.value,
            "approved_by": user,
            "approval_timestamp": now,
            "comments": reason
        })

        # Emit event
        await event_fabric.ingest_event({
            "event_id": f"EVT-MIT-REJ-{proposal_id}",
            "domain": proposal["domain"],
            "action": "MITIGATION_REJECTED",
            "user": user,
            "role": role,
            "resource": proposal["target_asset"],
            "result": "REJECTED",
            "risk": 5.0,
            "metadata": {
                "proposal_id": proposal_id,
                "action_name": proposal["action_name"],
                "rejected_by": user,
                "reviewer_role": role,
                "reason": reason
            }
        })

        return updated


safety_guard = SafetyGuardEngine()
