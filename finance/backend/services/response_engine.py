"""
Securox — Autonomous Response Engine
Generates and (optionally) simulates execution of mitigation actions
based on risk assessment output.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("securox.response")


# ── playbook definitions ──────────────────────────────────────────────────────
PLAYBOOKS: dict[str, list[dict]] = {
    "FINANCIAL_FRAUD": [
        {"action": "Revoke active session tokens", "reason": "Account takeover & suspicious velocity burst", "expected_impact": "Immediate session termination for suspect user", "rollback": "Re-authenticate user via out-of-band identity verification", "approval_required": False, "target": "iam"},
        {"action": "Lock suspicious session & account", "reason": "Prevent further unauthorized transaction submissions", "expected_impact": "Account placed in frozen quarantine state", "rollback": "Unlock via admin portal upon compliance clearance", "approval_required": True, "target": "core_banking"},
        {"action": "Block source IP address", "reason": "High-risk IP prefix engaged in automated abuse", "expected_impact": "Drop ingress traffic at perimeter firewall (60m TTL)", "rollback": "Remove IP from perimeter drop list", "approval_required": False, "target": "firewall"},
        {"action": "Require Mandatory step-up MFA", "reason": "High transaction risk score (>70/100)", "expected_impact": "Enforce biometric or SMS OTP challenge on next login", "rollback": "Disable step-up enforcement", "approval_required": False, "target": "identity_provider"},
        {"action": "Freeze high-value outbound transfers", "reason": "Potential money mule exfiltration attempt", "expected_impact": "Hold transfers > ₹50,000 for manual review", "rollback": "Release transaction hold", "approval_required": True, "target": "payment_gateway"},
        {"action": "Notify SOC & Financial Crime Analyst", "reason": "Trigger high-priority alert in Security Operations Center", "expected_impact": "Alert ticket generated for compliance investigation", "rollback": "Close incident ticket", "approval_required": False, "target": "security_ops"},
        {"action": "Increase telemetry monitoring level", "reason": "Monitor surrounding asset nodes for blast radius", "expected_impact": "Set SIEM logging to DEBUG verbosity for 120 mins", "rollback": "Restore default INFO logging level", "approval_required": False, "target": "siem"}
    ],
    "FASTAG_CLONING": [
        {"action": "Suspend suspect FASTag RFID credentials", "reason": "Impossible travel speed (>300 km/h) cloning detected", "expected_impact": "Blacklist RFID tag at toll barrier gateways", "rollback": "Re-activate tag after vehicle verification", "approval_required": True, "target": "fastag_infra"},
        {"action": "Block source IP & toll gateway node", "reason": "Spoofed toll telemetry injection", "expected_impact": "Isolate compromised toll reader controller", "rollback": "Re-commission reader node", "approval_required": True, "target": "network"},
        {"action": "Alert highway patrol & ANPR cameras", "reason": "Vehicle plate duplication suspect", "expected_impact": "Trigger automatic license plate recognition alert", "rollback": "Clear ANPR flag", "approval_required": False, "target": "traffic_system"}
    ],
    "TREASURY_ATTACK": [
        {"action": "Isolate Municipal Treasury API Gateway", "reason": "Unauthorized tax ledger alteration attempt", "expected_impact": "Cut API access between Tax Portal & Treasury Vault", "rollback": "Restore API bridge after security patch", "approval_required": True, "target": "tax_portal"},
        {"action": "Revoke all admin session credentials", "reason": "Privilege escalation detected on revenue servers", "expected_impact": "Force logoff of all municipal admin users", "rollback": "Re-issue secure tokens", "approval_required": True, "target": "iam"},
        {"action": "Enable immutable database transaction log", "reason": "Prevent tampering of municipal revenue records", "expected_impact": "Enforce WORM storage mode on tax DB", "rollback": "Restore standard DB mode", "approval_required": True, "target": "core_banking"}
    ],
    "DDoS": [
        {"action": "Rate-limit ingress traffic", "reason": "Volumetric traffic burst exceeding threshold", "expected_impact": "Cap incoming requests to 100 req/s", "rollback": "Restore normal ingress limit", "approval_required": False, "target": "ingress"},
        {"action": "Block attacker IP subnet", "reason": "Correlated botnet SYN flood attack", "expected_impact": "Drop subnet traffic at perimeter", "rollback": "Unblock subnet", "approval_required": False, "target": "firewall"},
        {"action": "Activate CDN Under-Attack Shield", "reason": "Protect origin banking & municipal portals", "expected_impact": "Enforce JS challenge on edge nodes", "rollback": "Disable CDN shield mode", "approval_required": False, "target": "edge_layer"}
    ],
    "GENERIC": [
        {"action": "Revoke active session tokens", "reason": "Precautionary containment for elevated risk score", "expected_impact": "User session invalidated", "rollback": "Re-authenticate", "approval_required": False, "target": "iam"},
        {"action": "Block source IP address", "reason": "Suspicious request vector", "expected_impact": "Temporary IP ban", "rollback": "Unblock IP", "approval_required": False, "target": "firewall"},
        {"action": "Require Mandatory step-up MFA", "reason": "Risk threshold exceeded", "expected_impact": "MFA challenge issued", "rollback": "Disable MFA prompt", "approval_required": False, "target": "iam"},
        {"action": "Notify SOC & Security Ops", "reason": "Incident logging", "expected_impact": "P2 alert created", "rollback": "Close ticket", "approval_required": False, "target": "security_ops"}
    ],
}

RISK_THRESHOLDS = {
    "CATASTROPHIC": {"auto_execute": True,  "notify_levels": ["SOC", "CISO", "Mayor", "Financial Controller"]},
    "CRITICAL":     {"auto_execute": True,  "notify_levels": ["SOC", "CISO", "Management"]},
    "HIGH":         {"auto_execute": False, "notify_levels": ["SOC", "CISO"]},
    "MODERATE":     {"auto_execute": False, "notify_levels": ["SOC"]},
    "LOW":          {"auto_execute": False, "notify_levels": []},
    "NORMAL":       {"auto_execute": False, "notify_levels": []},
    "NOMINAL":      {"auto_execute": False, "notify_levels": []},
}


class ResponseEngine:
    """Generates response playbooks and simulates their execution."""

    def generate_response(
        self,
        risk_assessment: dict,
        attack_type: str = "GENERIC",
    ) -> dict:
        """
        Given a risk assessment dict, produce a structured response plan.
        """
        category    = risk_assessment.get("risk_category", "NORMAL")
        risk_score  = risk_assessment.get("risk_score", 0)
        asset       = risk_assessment.get("asset", "unknown")
        flags       = risk_assessment.get("active_threat_flags", [])

        # Select playbook
        playbook_key = "GENERIC"
        for flag in flags:
            if flag.upper() in PLAYBOOKS:
                playbook_key = flag.upper()
                break
        if attack_type.upper() in PLAYBOOKS:
            playbook_key = attack_type.upper()

        actions     = PLAYBOOKS.get(playbook_key, PLAYBOOKS["GENERIC"])
        threshold   = RISK_THRESHOLDS.get(category, RISK_THRESHOLDS.get("NORMAL", {"auto_execute": False, "notify_levels": []}))

        # Priority actions (first 2) vs secondary
        primary     = actions[:2]
        secondary   = actions[2:]

        plan = {
            "id":               str(uuid.uuid4()),
            "timestamp":        datetime.now(timezone.utc).isoformat(),
            "asset":            asset,
            "risk_score":       risk_score,
            "risk_category":    category,
            "playbook":         playbook_key,
            "auto_execute":     threshold["auto_execute"],
            "notify":           threshold["notify_levels"],
            "primary_actions":  primary,
            "secondary_actions": secondary,
            "estimated_containment_minutes": self._estimate_containment(risk_score),
            "confidence":       risk_assessment.get("confidence", 0.5),
        }
        return plan

    async def simulate_execution(self, plan: dict) -> list[dict]:
        """
        Walk through actions and emit timestamped execution events.
        (Simulation only — no real infrastructure calls.)
        """
        results = []
        all_actions = plan["primary_actions"] + plan["secondary_actions"]
        for i, action in enumerate(all_actions):
            await asyncio.sleep(0.1)   # simulate execution latency
            result = {
                "step":      i + 1,
                "action":    action["action"],
                "target":    action["target"],
                "status":    "executed" if plan["auto_execute"] else "queued",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message":   f"[SIM] {action['action']} on {action['target']} — "
                             f"params={action['params']}",
            }
            results.append(result)
            logger.info("Response step %d: %s", i + 1, result["message"])
        return results

    @staticmethod
    def _estimate_containment(risk_score: float) -> int:
        """Rough estimate in minutes."""
        if risk_score >= 80:  return 45
        if risk_score >= 60:  return 20
        if risk_score >= 40:  return 10
        return 5


# ── singleton ─────────────────────────────────────────────────────────────────
response_engine = ResponseEngine()
