"""
CAREGUARD — Healthcare Cyber Blast Radius & Cascade Engine
Evaluates downstream cascading failure depth across clinical care pathways
if a specific digital asset fails or is attacked.
Zero Synthetic Data Policy.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from healthcare_core.healthcare.dependencies.graph import DIGITAL_HEALTHCARE_ASSETS
from healthcare_core.healthcare.pathways.engine import CARE_PATHWAYS

class BlastRadiusAssessment(BaseModel):
    target_asset_id: str
    target_asset_name: str
    compromise_scope: str
    cascading_failure_depth: int
    directly_impacted_pathways: List[str]
    critical_services_at_risk: List[str]
    prescribed_continuity_action: str
    cascade_propagation_severity: str

class BlastRadiusEngine:
    @staticmethod
    def evaluate_asset(asset_id: str) -> Optional[Dict[str, Any]]:
        asset = DIGITAL_HEALTHCARE_ASSETS.get(asset_id)
        if not asset:
            return None

        # Find directly impacted pathways
        impacted_pathways = []
        for p_id in asset.associated_pathways:
            pathway = CARE_PATHWAYS.get(p_id)
            if pathway:
                impacted_pathways.append(pathway.name)

        # Map continuity safeguard actions
        continuity_map = {
            "EHR_CORE_GATEWAY": (
                "Engage Read-Only FHIR Throttle & Local Station Cache. Do NOT disconnect emergency room triage lookups.",
                "CRITICAL_CASCADE"
            ),
            "EMAR_BCMA_SERVER": (
                "Authorize Offline Pyxis Override Mode. Shift to two-nurse manual double-check for high-alert IV vasoactive meds.",
                "HIGH_CASCADE"
            ),
            "ICU_BEDSIDE_TELEMETRY_GW": (
                "Isolate Bedside Monitor LAN Gateway while maintaining local hardwire acoustic alarms at central nursing consoles.",
                "CRITICAL_CASCADE"
            ),
            "LAB_ANALYZER_LIS": (
                "Engage Telephone STAT Panic Lab Protocol. Lab technicians telephone critical blood gas/troponin values directly.",
                "HIGH_CASCADE"
            ),
            "ED_TRIAGE_TERMINAL": (
                "Activate Paper Disaster Triage Tagging (START/ESI) & Local Disaster Intake Log.",
                "MODERATE_CASCADE"
            ),
            "SMART_INFUSION_PUMP_GW": (
                "Maintain manual pump keypad programming using printed certified drug library binders.",
                "HIGH_CASCADE"
            ),
            "VENTILATOR_TELEMETRY_SERVER": (
                "Preserve standalone pneumatic ventilation. Disconnect network telemetry while maintaining local bedside audible alarms.",
                "CRITICAL_CASCADE"
            )
        }

        action, severity = continuity_map.get(
            asset_id,
            ("Initiate hospital-wide cyber downtime protocol and manual patient safety verification.", "HIGH_CASCADE")
        )

        return BlastRadiusAssessment(
            target_asset_id=asset.id,
            target_asset_name=asset.name,
            compromise_scope=f"Digital failure of {asset.name} ({asset.protocol})",
            cascading_failure_depth=len(impacted_pathways),
            directly_impacted_pathways=impacted_pathways,
            critical_services_at_risk=asset.critical_dependencies,
            prescribed_continuity_action=action,
            cascade_propagation_severity=severity
        ).model_dump()

blast_radius_engine = BlastRadiusEngine()

