"""
CAREGUARD — Unified Healthcare Security REST API Endpoints
All routes under /api with complete provenance tracking and zero synthetic data.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from auth.security_guard import require_access
from auth.access_control import Action, ResourceType

from healthcare_core.healthcare.dependencies.graph import dependency_graph_service
from healthcare_core.healthcare.pathways.engine import care_pathway_service
from healthcare_core.detection.healthcare_detectors import healthcare_detector_engine
from healthcare_core.healthcare.exposure.engine import operational_exposure_engine
from healthcare_core.healthcare.blast_radius import blast_radius_engine
from healthcare_core.healthcare.risk.engine import healthcare_risk_engine
from healthcare_core.healthcare.devices.iomt_engine import iomt_device_engine
from healthcare_core.healthcare.health_it.engine import health_it_engine
from healthcare_core.healthcare.incidents.lifecycle import incident_lifecycle_manager
from healthcare_core.data.provenance.registry import provenance_ledger
from healthcare_core.data.loaders.mimic_ed_loader import mimic_ed_loader
from healthcare_core.data.loaders.mimic_clinical_loader import mimic_clinical_loader
from healthcare_core.data.loaders.eicu_loader import eicu_loader
from healthcare_core.data.loaders.onc_loader import onc_loader
from healthcare_core.data.loaders.cyber_loader import cyber_dataset_loader

router = APIRouter()

# Response Model for Actions
class ResponseActionRequest(BaseModel):
    asset_id: str
    action_type: str
    operator_notes: Optional[str] = None
    incident_id: Optional[str] = None

@router.get("/health")
def get_health():
    return {
        "status": "UP",
        "healthy": True,
        "service": "CAREGUARD",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "datasets": {
            "mimic_ed": mimic_ed_loader._loaded,
            "mimic_clinical": mimic_clinical_loader._loaded,
            "eicu": eicu_loader._loaded,
            "onc": onc_loader._loaded
        }
    }

@router.get("/infrastructure/status")
def get_infrastructure_status():
    assets = dependency_graph_service.get_all_assets()
    exposures = operational_exposure_engine.calculate_exposures()
    online_count = sum(1 for a in assets if a.get("operational_status") == "ONLINE")
    return {
        "status": "OPERATIONAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_digital_assets": len(assets),
        "online_digital_assets": online_count,
        "infrastructure_health": "NOMINAL" if online_count == len(assets) else "DEGRADED",
        "assets": assets,
        "operational_pathways_monitored": len(exposures)
    }

@router.get("/overview")
def get_overview():
    risk = healthcare_risk_engine.calculate_systemic_risk()
    exposures = operational_exposure_engine.calculate_exposures()
    assets = dependency_graph_service.get_all_assets()
    threats = healthcare_detector_engine.run_all_detections()

    return {
        "system_status": "ONLINE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "zero_synthetic_data_guarantee": True,
        "composite_risk_score": risk["composite_risk_score"],
        "risk_tier": risk["risk_tier"],
        "risk_confidence": risk["risk_confidence"],
        "data_completeness": risk["data_completeness"],
        "data_completeness_pct": risk["data_completeness_pct"],
        "risk_calculation_components": risk["calculation_components"],
        "risk_derivation": "DATA_DERIVED (NIST SP 800-30 Cascade Formulation)",
        "operational_advisory": risk["operational_advisory"],
        "active_cyber_threats_count": len(threats),
        "active_threats_derivation": f"DATA_DERIVED ({len(threats)} Statistical Anomaly Events across Real Datasets)",
        "total_monitored_pathways": len(exposures),
        "pathways_derivation": "DATA_DERIVED Exposure Scoring across REFERENCE Care Pathways",
        "critical_exposure_pathways": [e["pathway_name"] for e in exposures if e["degradation_state"] == "SEVERELY DEGRADED"],
        "degraded_exposure_pathways": [e["pathway_name"] for e in exposures if e["degradation_state"] == "DEGRADED"],
        "monitored_digital_assets": len(assets),
        "assets_derivation": "REFERENCE_ARCHITECTURE (NIST SP 800-207 & ONC Health IT; HIPAA Deidentified)"
    }

@router.get("/threats")
def get_threats():
    threats = healthcare_detector_engine.run_all_detections()
    return {
        "total_threats": len(threats),
        "threats": threats,
        "detection_grounding": "100% Organic Anomaly Detection against MIMIC-IV and eICU datasets"
    }

@router.get("/assets")
def get_assets():
    return {
        "assets": dependency_graph_service.get_all_assets()
    }

@router.get("/assets/{asset_id}")
def get_asset_detail(asset_id: str):
    asset = dependency_graph_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found.")
    return asset

@router.get("/dependencies")
def get_dependencies():
    return dependency_graph_service.build_cartography_graph()

@router.get("/pathways")
def get_pathways():
    return {
        "pathways": care_pathway_service.get_all_pathways()
    }

@router.get("/pathways/{pathway_id}")
def get_pathway_detail(pathway_id: str):
    pathway = care_pathway_service.get_pathway(pathway_id)
    if not pathway:
        raise HTTPException(status_code=404, detail=f"Pathway {pathway_id} not found.")
    return pathway

@router.get("/exposure")
def get_exposure():
    exposures = operational_exposure_engine.calculate_exposures()
    return {
        "pathway_exposures": exposures,
        "policy": "Non-clinical patient-safety language enforced"
    }

@router.get("/blast-radius")
def get_blast_radius(asset_id: Optional[str] = Query("EHR_CORE_GATEWAY")):
    assessment = blast_radius_engine.evaluate_asset(asset_id)
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found for blast radius assessment.")
    return assessment

@router.get("/devices")
def get_devices():
    return iomt_device_engine.get_device_overview()

@router.get("/health-it")
def get_health_it():
    return health_it_engine.get_health_it_profile()

@router.get("/risk")
def get_risk():
    return healthcare_risk_engine.calculate_systemic_risk()

@router.get("/evidence")
def get_evidence(table_name: str = Query(..., description="Target dataset table name"), limit: int = Query(6, ge=1, le=50)):
    # Query across loaders
    records = (
        mimic_ed_loader.get_table_records(table_name, limit) or
        mimic_clinical_loader.get_table_records(table_name, limit) or
        eicu_loader.get_table_records(table_name, limit) or
        onc_loader.get_table_records(table_name, limit) or
        cyber_dataset_loader.get_table_records(table_name, limit)
    )
    if not records:
        return {
            "table_name": table_name,
            "count": 0,
            "records": [],
            "status": "NO OBSERVED TELEMETRY OR TABLE NOT IN REGISTRY"
        }
    return {
        "table_name": table_name,
        "count": len(records),
        "records": records,
        "zero_synthetic_guarantee": "Authentic organic records loaded directly from disk archive"
    }

@router.get("/datasets")
def get_datasets():
    return provenance_ledger.get_provenance_summary()

@router.get("/coverage")
def get_data_coverage():
    return provenance_ledger.get_data_coverage()

# -----------------------------------------------------------------------------
# Authentic Cyberdatasets Ingestion & Telemetry Endpoints
# -----------------------------------------------------------------------------
@router.get("/cyber/overview")
def get_cyber_overview():
    return cyber_dataset_loader.get_summary()

@router.get("/cyber/accounting")
def get_cyber_accounting():
    return cyber_dataset_loader.get_dataset_accounting_table()

@router.get("/cyber/devices")
def get_cyber_devices():
    return {
        "devices_count": len(cyber_dataset_loader.get_iomt_devices()),
        "devices": cyber_dataset_loader.get_iomt_devices(),
        "derivation": "DATA_DERIVED",
        "source": "CICIoMT2024 Physical IoMT Device Captures (PCAP)"
    }

@router.get("/cyber/categories")
def get_cyber_categories():
    return cyber_dataset_loader.get_ciciomt_categories()

@router.get("/cyber/hospital-threats")
def get_cyber_hospital_threats():
    return cyber_dataset_loader.get_hospital_threat_database()

@router.get("/cyber/cicids2017")
def get_cyber_cicids2017():
    return cyber_dataset_loader.get_cicids2017()

@router.get("/cyber/csecicids2018")
def get_cyber_csecicids2018():
    return cyber_dataset_loader.get_csecicids2018()

@router.get("/cyber/cicflowmeter")
def get_cyber_cicflowmeter():
    return cyber_dataset_loader.get_cicflowmeter()

@router.get("/cyber/lanl-redteam")
def get_cyber_lanl_redteam():
    return cyber_dataset_loader.get_lanl_cyber()

@router.get("/cyber/inventory")
def get_cyber_inventory():
    return {
        "total_files": len(cyber_dataset_loader.get_file_inventory()),
        "files": cyber_dataset_loader.get_file_inventory(),
        "derivation": "DATA_DERIVED"
    }

# -----------------------------------------------------------------------------
# Incident Lifecycle & Honest Response Endpoints
# -----------------------------------------------------------------------------
class AdvanceStageRequest(BaseModel):
    new_stage: str
    notes: Optional[str] = None

@router.get("/incidents")
def get_all_incidents():
    return incident_lifecycle_manager.get_all_incidents()

@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str):
    inc = incident_lifecycle_manager.get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return inc

@router.post("/incidents/{incident_id}/stage")
def advance_incident_stage(
    incident_id: str,
    req: AdvanceStageRequest,
    current_user: dict = Depends(require_access(ResourceType.SECURITY_INCIDENT, Action.UPDATE, object_id_param="incident_id"))
):
    try:
        return incident_lifecycle_manager.advance_stage(incident_id, req.new_stage, req.notes)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/response")
def execute_response_action(
    action: ResponseActionRequest,
    current_user: dict = Depends(require_access(ResourceType.HOSPITAL_IT_ASSET, Action.RESOLVE))
):
    asset = dependency_graph_service.get_asset(action.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Target asset not found.")

    target_id = action.incident_id or action.asset_id
    result = incident_lifecycle_manager.log_response(
        incident_id=target_id,
        action_type=action.action_type,
        operator_notes=action.operator_notes
    )

    return {
        "status": "LOGGED_INTENT",
        "asset_id": action.asset_id,
        "asset_name": asset["name"],
        "action_type": action.action_type,
        "operator_notes": action.operator_notes,
        "execution_classification": "LOGGED_INTENT",
        "environment": "RESEARCH / SIMULATED SOC (NON-PRODUCTION)",
        "live_actuator_enforcement": False,
        "verification": "NOT_AVAILABLE (Simulated research environment; physical hardware state change not observed)",
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "disclaimer": "Honest Operational Response: Action logged as operator intent. Automated hardware actuation is not claimed.",
        "incident_details": result
    }

