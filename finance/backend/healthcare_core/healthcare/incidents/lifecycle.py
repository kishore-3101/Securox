"""
CAREGUARD — Incident Lifecycle & Operational Response Manager
Manages security incidents through a defensible 7-stage lifecycle:
  DETECTED -> TRIAGED -> ACKNOWLEDGED -> CONTAINMENT_PLANNED -> ACTION_LOGGED -> VERIFICATION -> RESOLVED
Records response actions honestly as LOGGED_INTENT within a research/demo environment.
Does NOT claim automated actuator live enforcement or false guarantees.
Zero Synthetic Data Policy.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from healthcare_core.detection.healthcare_detectors import healthcare_detector_engine
from healthcare_core.healthcare.dependencies.graph import dependency_graph_service

LIFECYCLE_STAGES = [
    "DETECTED",
    "TRIAGED",
    "ACKNOWLEDGED",
    "CONTAINMENT_PLANNED",
    "ACTION_LOGGED",
    "VERIFICATION",
    "RESOLVED"
]

RECOMMENDED_SAFEGUARDS = {
    "RESTRICT_FHIR_API": {
        "title": "Throttle External SMART-on-FHIR Queries",
        "description": "Applies rate limiting on public-facing FHIR endpoints while exempting emergency room and bedside clinical queries.",
        "target_asset": "EHR_CORE_GATEWAY"
    },
    "OFFLINE_PYXIS_OVERRIDE": {
        "title": "Enforce Pyxis Cabinet Offline Dual-Nurse Verification",
        "description": "Enforces mandatory dual-nurse badge verification for high-risk medication drawer overrides at automated dispensing stations.",
        "target_asset": "EMAR_BCMA_SERVER"
    },
    "ISOLATE_BEDSIDE_GATEWAY": {
        "title": "Segment Bedside Monitor LAN Gateway",
        "description": "Quarantines suspicious medical device LAN gateway traffic while ensuring local hardwired acoustic alarms remain active at the bed.",
        "target_asset": "ICU_BEDSIDE_TELEMETRY_GW"
    },
    "TELEPHONE_PANIC_PROTOCOL": {
        "title": "Activate Manual STAT Lab Telephone Panics",
        "description": "Directs laboratory personnel to transmit critical panic-range laboratory values via direct telephone callback to charge nurses.",
        "target_asset": "LIS_LAB_CORE"
    },
    "ISOLATE_PACS_STORAGE": {
        "title": "Isolate Non-Critical Imaging Archive Ingestion",
        "description": "Suspends batch imaging transfers while keeping emergency trauma DICOM viewers available in operating suites.",
        "target_asset": "PACS_IMAGING_STORAGE"
    }
}


class IncidentLifecycleManager:
    def __init__(self):
        self._incidents: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    def _sync_with_detectors(self):
        """
        Seeds incidents from currently observed statistical threat anomalies.
        """
        threats = healthcare_detector_engine.run_all_detections()
        for th in threats:
            event_id = th["event_id"]
            if event_id not in self._incidents:
                asset_id = th.get("targeted_asset_id", "EHR_CORE_GATEWAY")
                asset = dependency_graph_service.get_asset(asset_id)
                stat = th.get("statistical_evidence", {})
                impact = th.get("impact_path", {})

                # Default recommended safeguard based on asset
                rec_action = "RESTRICT_FHIR_API"
                if "BEDSIDE" in asset_id:
                    rec_action = "ISOLATE_BEDSIDE_GATEWAY"
                elif "EMAR" in asset_id or "PYXIS" in th.get("title", "").upper():
                    rec_action = "OFFLINE_PYXIS_OVERRIDE"
                elif "LIS" in asset_id:
                    rec_action = "TELEPHONE_PANIC_PROTOCOL"
                elif "PACS" in asset_id:
                    rec_action = "ISOLATE_PACS_STORAGE"

                self._incidents[event_id] = {
                    "incident_id": f"INC-{event_id}",
                    "threat_event_id": event_id,
                    "title": th["title"],
                    "state": "DETECTED",
                    "lifecycle_stage": "DETECTED",
                    "created_at": th.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "severity": th["severity"],
                    "targeted_asset_id": asset_id,
                    "targeted_asset_name": asset.get("name") if asset else asset_id,
                    "detected_evidence": {
                        "dataset": th.get("evidence_dataset"),
                        "metric": th.get("observed_metric"),
                        "z_score": stat.get("z_score"),
                        "sample_size": stat.get("sample_size"),
                        "derivation": th.get("derivation", "DATA_DERIVED")
                    },
                    "clinical_pathways_impacted": impact.get("pathways_exposed", []),
                    "recommended_action": {
                        "action_type": rec_action,
                        "title": RECOMMENDED_SAFEGUARDS.get(rec_action, {}).get("title"),
                        "description": RECOMMENDED_SAFEGUARDS.get(rec_action, {}).get("description")
                    },
                    "response_history": [],
                    "current_operational_state": {
                        "asset_status": asset.get("operational_status", "ONLINE") if asset else "ONLINE",
                        "enforcement_mode": "LOGGED_INTENT_ONLY",
                        "live_actuation": False,
                        "verification_status": "NOT_AVAILABLE"
                    }
                }
        self._initialized = True

    def get_all_incidents(self) -> List[Dict[str, Any]]:
        self._sync_with_detectors()
        return list(self._incidents.values())

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        self._sync_with_detectors()
        # Search by INC-xxx or raw event_id
        for inc in self._incidents.values():
            if inc["incident_id"] == incident_id or inc["threat_event_id"] == incident_id:
                return inc
        return None

    def log_response(self, incident_id: str, action_type: str, operator_notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Applies a response action with honest, defensible telemetry tracking.
        Records response as LOGGED_INTENT.
        """
        inc = self.get_incident(incident_id)
        if not inc:
            # Create transient incident container if targeted directly by asset_id
            event_id = f"CYB_EVT_{str(uuid.uuid4())[:6].upper()}"
            inc = {
                "incident_id": f"INC-{event_id}",
                "threat_event_id": event_id,
                "title": f"Manual Operator Intervention on {incident_id}",
                "state": "ACTION_LOGGED",
                "lifecycle_stage": "ACTION_LOGGED",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "severity": "HIGH",
                "targeted_asset_id": incident_id,
                "targeted_asset_name": incident_id,
                "detected_evidence": {
                    "dataset": "Manual SOC Dispatch",
                    "metric": "Operator manual override",
                    "derivation": "OPERATOR_DISPATCH"
                },
                "clinical_pathways_impacted": ["Emergency Intake", "Critical Care / ICU"],
                "recommended_action": {
                    "action_type": action_type,
                    "title": RECOMMENDED_SAFEGUARDS.get(action_type, {}).get("title", action_type),
                    "description": RECOMMENDED_SAFEGUARDS.get(action_type, {}).get("description", "")
                },
                "response_history": [],
                "current_operational_state": {
                    "asset_status": "MANUAL_SAFEGUARD_LOGGED",
                    "enforcement_mode": "LOGGED_INTENT_ONLY",
                    "live_actuation": False,
                    "verification_status": "NOT_AVAILABLE"
                }
            }
            self._incidents[event_id] = inc

        safeguard = RECOMMENDED_SAFEGUARDS.get(action_type, {
            "title": action_type,
            "description": "Manual clinical continuity safeguard protocol."
        })

        before_state = inc["current_operational_state"].copy()
        
        # Advance lifecycle state
        new_stage = "ACTION_LOGGED"
        inc["lifecycle_stage"] = new_stage
        inc["state"] = new_stage
        inc["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Update after state
        after_state = {
            "asset_status": "CONTINUITY_PROTOCOL_LOGGED",
            "enforcement_mode": "LOGGED_INTENT_ONLY",
            "live_actuation": False,
            "verification_status": "NOT_AVAILABLE (No live actuator connected to research platform)"
        }
        inc["current_operational_state"] = after_state

        log_entry = {
            "action_id": f"ACT-{str(uuid.uuid4())[:8].upper()}",
            "logged_at": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "title": safeguard.get("title"),
            "description": safeguard.get("description"),
            "operator_notes": operator_notes or "Continuity protocol logged by healthcare security operator.",
            "execution_classification": "LOGGED_INTENT",
            "environment": "RESEARCH / SIMULATED SOC (NON-PRODUCTION)",
            "live_actuator_enforcement": False,
            "verification": "NOT_AVAILABLE (requires genuine physical telemetry change)",
            "before_state": before_state,
            "after_state": after_state
        }

        inc["response_history"].append(log_entry)

        return {
            "status": "INTENT_LOGGED",
            "incident_id": inc["incident_id"],
            "lifecycle_stage": inc["lifecycle_stage"],
            "action": log_entry,
            "disclaimer": "Simulated Research Console: This action records operator intent. Live physical enforcement is NOT performed against hospital hardware."
        }

    def advance_stage(self, incident_id: str, new_stage: str, notes: Optional[str] = None) -> Dict[str, Any]:
        if new_stage not in LIFECYCLE_STAGES:
            raise ValueError(f"Invalid lifecycle stage: {new_stage}. Must be one of {LIFECYCLE_STAGES}")

        inc = self.get_incident(incident_id)
        if not inc:
            raise KeyError(f"Incident {incident_id} not found.")

        old_stage = inc["lifecycle_stage"]
        inc["lifecycle_stage"] = new_stage
        inc["state"] = new_stage
        inc["updated_at"] = datetime.now(timezone.utc).isoformat()

        return {
            "incident_id": inc["incident_id"],
            "previous_stage": old_stage,
            "current_stage": new_stage,
            "updated_at": inc["updated_at"],
            "notes": notes
        }


incident_lifecycle_manager = IncidentLifecycleManager()

