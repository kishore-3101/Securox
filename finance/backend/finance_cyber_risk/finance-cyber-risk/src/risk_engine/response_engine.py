"""
Deterministic Response Recommendation Engine.

Produces RECOMMENDATIONS ONLY — this module never calls out to any banking
or security system, freezes an account, blocks a transaction, or performs
any other autonomous action. Every recommendation is a plain data structure
for a human to review and act on; `human_approval_required` is True for
every single action returned, without exception, by construction.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Recommendation:
    action: str
    priority: str
    reason: str
    human_approval_required: bool = True

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "priority": self.priority,
            "reason": self.reason,
            "human_approval_required": self.human_approval_required,
        }


def recommend_response(
    risk_level: str,
    fraud_probability: Optional[float] = None,
    aml_probability: Optional[float] = None,
    anomaly_score_normalized: Optional[float] = None,
    graph_risk_score: Optional[float] = None,
    propagation_risk: Optional[float] = None,
    criticality: Optional[float] = None,
    incident_severity: Optional[str] = None,
) -> list:
    """
    Returns a list of Recommendation dicts. The base action set is driven by
    `risk_level`; additional targeted recommendations are appended when a
    specific signal is both available and elevated, so the reasoning behind
    each extra recommendation is traceable to a real number, not a level
    label alone.
    """
    recs = []

    if risk_level == "LOW":
        recs.append(Recommendation(
            action="monitor",
            priority="LOW",
            reason="Overall risk score falls in the LOW band; no elevated signals require immediate action.",
        ))

    elif risk_level == "MEDIUM":
        recs.append(Recommendation(
            action="increase_monitoring",
            priority="MEDIUM",
            reason="Overall risk score falls in the MEDIUM band; warrants closer observation.",
        ))
        recs.append(Recommendation(
            action="additional_verification",
            priority="MEDIUM",
            reason="MEDIUM risk level — a lightweight secondary check (e.g. re-verify recent account activity) is proportionate.",
        ))

    elif risk_level == "HIGH":
        recs.append(Recommendation(
            action="step_up_authentication",
            priority="HIGH",
            reason="Overall risk score falls in the HIGH band; require stronger authentication for further activity on this entity.",
        ))
        recs.append(Recommendation(
            action="temporary_transaction_hold_review",
            priority="HIGH",
            reason="HIGH risk level — hold the transaction/account pending a manual review before proceeding.",
        ))
        recs.append(Recommendation(
            action="investigate_account_entity",
            priority="HIGH",
            reason="HIGH risk level warrants a focused investigation of this specific account/entity's recent activity.",
        ))
        if graph_risk_score is not None and graph_risk_score >= 50:
            recs.append(Recommendation(
                action="inspect_connected_entities",
                priority="HIGH",
                reason=f"graph_risk_score={graph_risk_score:.1f} indicates unusual network structure (e.g. fan-in/fan-out); connected entities warrant inspection.",
            ))

    elif risk_level == "CRITICAL":
        recs.append(Recommendation(
            action="recommend_containment",
            priority="CRITICAL",
            reason="Overall risk score falls in the CRITICAL band; containment of further activity on this entity is recommended pending review.",
        ))
        recs.append(Recommendation(
            action="escalate_to_soc",
            priority="CRITICAL",
            reason="CRITICAL risk level requires escalation to the Security Operations Center / fraud investigation team.",
        ))
        recs.append(Recommendation(
            action="investigate_connected_entities",
            priority="CRITICAL",
            reason="CRITICAL risk level — connected entities must be investigated given the possibility of coordinated activity.",
        ))
        recs.append(Recommendation(
            action="preserve_evidence",
            priority="CRITICAL",
            reason="CRITICAL risk level — preserve transaction/account records and logs in case of a subsequent formal investigation.",
        ))
        recs.append(Recommendation(
            action="initiate_recovery_workflow",
            priority="CRITICAL",
            reason="CRITICAL risk level — begin the (human-led) recovery workflow planning in parallel with investigation.",
        ))

    else:
        recs.append(Recommendation(
            action="monitor",
            priority="LOW",
            reason=f"Unrecognized risk_level '{risk_level}'; defaulting to the safest (monitor-only) recommendation.",
        ))

    # cross-cutting, signal-specific additions regardless of level
    if fraud_probability is not None and fraud_probability >= 0.8:
        recs.append(Recommendation(
            action="flag_for_fraud_team_priority_review",
            priority="HIGH",
            reason=f"fraud_probability={fraud_probability:.2f} is very high; route to the fraud team ahead of the standard queue.",
        ))
    if aml_probability is not None and aml_probability >= 0.5:
        recs.append(Recommendation(
            action="file_sar_review",
            priority="HIGH",
            reason=f"aml_probability={aml_probability:.2f} exceeds the review threshold; a human should assess whether a Suspicious Activity Report is warranted.",
        ))
    if propagation_risk is not None and propagation_risk >= 50:
        recs.append(Recommendation(
            action="expand_investigation_scope",
            priority="HIGH",
            reason=f"propagation simulation estimates meaningfully elevated risk (avg downstream risk={propagation_risk:.1f}) reaching connected entities.",
        ))
    if criticality is not None and criticality >= 0.8 and risk_level in ("HIGH", "CRITICAL"):
        recs.append(Recommendation(
            action="notify_account_owner_relationship_manager",
            priority="HIGH",
            reason=f"entity criticality={criticality:.2f} is high alongside an elevated risk level; the relationship owner should be informed.",
        ))

    return [r.to_dict() for r in recs]
