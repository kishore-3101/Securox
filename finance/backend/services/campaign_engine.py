"""
Securox — Attack Campaign Detection Engine (SH-FIN-05 Section 12)
Correlates disparate alerts across assets, IPs, and protocols into unified
multi-stage Attack Campaigns with temporal tracking, stage progression,
blast-radius aggregation, and persistent state.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from database.store import store

logger = logging.getLogger("securox.campaign_engine")

STAGE_HIERARCHY = {
    "PORT_SCAN": ("Reconnaissance", 1),
    "PROBE": ("Reconnaissance", 1),
    "BRUTE_FORCE": ("Credential Access", 2),
    "WEB_ATTACK": ("Initial Access", 3),
    "INFILTRATION": ("Lateral Movement", 4),
    "BOTNET": ("Command & Control", 4),
    "DOS": ("Service Degradation", 5),
    "DDOS": ("Infrastructure Disruption", 5),
    "SCADA_MANIPULATION": ("Physical Cyber Sabotage", 6),
    "OTHER": ("Exploitation Activity", 3),
}


class CampaignEngine:
    """
    Groups correlated security alerts into coordinated attack campaigns.
    Prevents alert fatigue and exposes the full attack chain to operators.
    """

    def __init__(self):
        self._active_campaigns: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def _determine_stage(self, attack_type: str) -> tuple[str, int]:
        return STAGE_HIERARCHY.get(attack_type.upper(), ("Exploitation Activity", 3))

    async def correlate_alert(self, alert: dict) -> dict:
        """
        Evaluates a newly triggered alert and associates it with an existing
        campaign or generates a new campaign if it represents coordinated activity.
        """
        async with self._lock:
            asset_id = alert.get("asset_id", "UNKNOWN")
            src_ip = alert.get("source_ip", "UNKNOWN")
            attack_type = alert.get("attack_type", "BENIGN")
            risk_score = float(alert.get("risk_score", 0.0))
            ts = alert.get("timestamp") or datetime.now(timezone.utc).isoformat()
            stage_name, stage_rank = self._determine_stage(attack_type)

            # Match criteria: explicit campaign tag, identical source IP, or active multi-stage attack
            matched_id = alert.get("campaign_id")
            if not matched_id:
                for cid, camp in self._active_campaigns.items():
                    if camp.get("status") != "ACTIVE":
                        continue
                    # Match if identical source IP, or asset shares dependency
                    if src_ip in camp.get("source_ips", []) or asset_id in camp.get("affected_assets", []):
                        matched_id = cid
                        break

            if not matched_id:
                # Create a new campaign for high-risk / severe alerts
                matched_id = f"CAMPAIGN-SEC-2026-{uuid.uuid4().hex[:4].upper()}"
                camp = {
                    "id": matched_id,
                    "title": f"Coordinated Campaign against {alert.get('asset_name', asset_id)}",
                    "status": "ACTIVE",
                    "first_seen": ts,
                    "last_seen": ts,
                    "risk_score": risk_score,
                    "confidence": round(float(alert.get("attack_confidence", 0.85)), 2),
                    "current_stage": stage_name,
                    "stage_rank": stage_rank,
                    "stages": [],
                    "affected_assets": [asset_id],
                    "source_ips": [src_ip] if src_ip != "UNKNOWN" else [],
                    "alert_ids": [alert.get("alert_id") or alert.get("id")],
                    "primary_attack": attack_type,
                    "narrative": f"Initiated via {attack_type} against {asset_id} from {src_ip}."
                }
                self._active_campaigns[matched_id] = camp
            else:
                camp = self._active_campaigns.get(matched_id)
                if not camp:
                    camp = await store.get_campaign(matched_id) or {
                        "id": matched_id,
                        "title": f"Coordinated Multi-Asset Campaign ({matched_id})",
                        "status": "ACTIVE",
                        "first_seen": ts,
                        "last_seen": ts,
                        "risk_score": risk_score,
                        "confidence": 0.88,
                        "current_stage": stage_name,
                        "stage_rank": stage_rank,
                        "stages": [],
                        "affected_assets": [],
                        "source_ips": [],
                        "alert_ids": [],
                        "primary_attack": attack_type,
                        "narrative": ""
                    }
                    self._active_campaigns[matched_id] = camp

            # Update campaign metrics
            camp["last_seen"] = ts
            if asset_id not in camp["affected_assets"]:
                camp["affected_assets"].append(asset_id)
            if src_ip != "UNKNOWN" and src_ip not in camp["source_ips"]:
                camp["source_ips"].append(src_ip)
            alert_id = alert.get("alert_id") or alert.get("id")
            if alert_id and alert_id not in camp["alert_ids"]:
                camp["alert_ids"].append(alert_id)

            # Advance stage if current stage is higher rank
            if stage_rank >= camp.get("stage_rank", 1):
                camp["current_stage"] = stage_name
                camp["stage_rank"] = stage_rank

            # Append stage checkpoint
            stage_entry = {
                "timestamp": ts,
                "stage": stage_name,
                "asset": asset_id,
                "attack": attack_type,
                "risk": risk_score,
                "summary": f"{stage_name} detected targeting {asset_id} ({attack_type})."
            }
            camp["stages"].append(stage_entry)

            # Recalculate campaign risk: max individual risk + spread bonus + stage depth bonus
            asset_spread_bonus = min(15.0, (len(camp["affected_assets"]) - 1) * 3.0)
            stage_depth_bonus = min(10.0, camp["stage_rank"] * 1.8)
            camp["risk_score"] = min(99.0, round(max(camp["risk_score"], risk_score) + asset_spread_bonus + stage_depth_bonus, 1))
            camp["confidence"] = min(0.98, round(0.80 + len(camp["stages"]) * 0.03, 2))

            # Persist to database
            await store.add_campaign(camp)
            logger.info("Updated campaign %s -> Stage: %s | Assets: %d | Risk: %.1f",
                        matched_id, camp["current_stage"], len(camp["affected_assets"]), camp["risk_score"])
            return camp

    async def get_active_campaigns(self) -> List[dict]:
        db_camps = await store.get_campaigns(limit=50)
        return db_camps

    async def get_campaign(self, campaign_id: str) -> Optional[dict]:
        if campaign_id in self._active_campaigns:
            return self._active_campaigns[campaign_id]
        return await store.get_campaign(campaign_id)

    async def close_campaign(self, campaign_id: str, status: str = "RESOLVED") -> Optional[dict]:
        camp = await self.get_campaign(campaign_id)
        if not camp:
            return None
        camp["status"] = status
        camp["last_seen"] = datetime.now(timezone.utc).isoformat()
        await store.add_campaign(camp)
        if campaign_id in self._active_campaigns:
            self._active_campaigns[campaign_id]["status"] = status
        return camp


campaign_engine = CampaignEngine()
