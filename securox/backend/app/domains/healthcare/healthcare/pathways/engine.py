"""
CAREGUARD — Care Pathway Shadows Engine
Defines the 5 authentic clinical care pathways with grounded clinical milestones
derived from MIMIC-IV and eICU database tables.
Zero Synthetic Data Policy.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class PathwayMilestone(BaseModel):
    id: str
    name: str
    clinical_purpose: str
    underlying_digital_dependency: str
    observed_table_field: str
    dependency_derivation: str = "STATIC_REFERENCE"
    observation_derivation: str = "DATA_DERIVED"

class CarePathwayShadow(BaseModel):
    id: str
    name: str
    description: str
    clinical_acuity_weight: float
    source_dataset: str
    observed_volume_metric: str
    milestones: List[PathwayMilestone]
    primary_assets: List[str]
    derivation: str = "DATA_DERIVED"
    provenance_chain: Dict[str, str] = {
        "cyber_event": "DATA_DERIVED (Statistical anomalies computed from source dataset)",
        "digital_asset": "STATIC_REFERENCE (NIST SP 800-207 Zero Trust Architecture Node)",
        "healthcare_dependency": "STATIC_REFERENCE (Reference Clinical Systems Topology)",
        "care_service": "STATIC_REFERENCE (Hospital Departmental Organizational Model)",
        "care_pathway": "DATA_DERIVED (Clinical workflows grounded in MIMIC-IV / eICU records)",
        "operational_exposure": "DATA_DERIVED (NIST SP 800-30 Probabilistic Cascade Model)"
    }

CARE_PATHWAYS: Dict[str, CarePathwayShadow] = {
    "PATHWAY_ED": CarePathwayShadow(
        id="PATHWAY_ED",
        name="Emergency Intake & Acute Resuscitation",
        description="Ambulance arrival, ESI acuity triage assessment, vital sign stabilization, and urgent bedside medication release.",
        clinical_acuity_weight=1.0,
        source_dataset="MIMIC-IV-ED Demo v2.2 (edstays.csv.gz, triage.csv.gz, pyxis.csv.gz)",
        observed_volume_metric="222 real ED stays, 1,082 Pyxis dispense transactions observed",
        primary_assets=["ED_TRIAGE_TERMINAL", "EHR_CORE_GATEWAY"],
        milestones=[
            PathwayMilestone(
                id="MS_ED_01",
                name="Inbound Transport & Triage Acuity Assessment",
                clinical_purpose="Assign Emergency Severity Index (ESI 1-5) and capture initial physiological baseline",
                underlying_digital_dependency="ED Triage Workstation & Core EHR Sync (Generic Class)",
                observed_table_field="mimic-iv-ed: triage.csv.gz (acuity, chiefcomplaint, o2sat)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_ED_02",
                name="STAT Emergency Medication Retrieval",
                clinical_purpose="Access rapid-sequence intubation or resuscitation medications via automated dispensing cabinet",
                underlying_digital_dependency="Automated Dispensing Cabinet Interface (Generic Class)",
                observed_table_field="mimic-iv-ed: pyxis.csv.gz (name, gsn, charttime)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_ED_03",
                name="Clinical Service Disposition Transfer",
                clinical_purpose="Transition stabilized patient to Inpatient Floor, ICU, or Operating Room",
                underlying_digital_dependency="Core EHR Patient Tracking System (Generic Class)",
                observed_table_field="mimic-iv-ed: edstays.csv.gz (disposition, outtime)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            )
        ]
    ),
    "PATHWAY_ICU": CarePathwayShadow(
        id="PATHWAY_ICU",
        name="Critical Care / Intensive Care Unit",
        description="Continuous life-support monitoring, mechanical ventilator titration, and vasoactive smart pump drug infusions.",
        clinical_acuity_weight=1.0,
        source_dataset="eICU CRD Demo v2.0.1 (vitalPeriodic.csv.gz, respiratoryCharting.csv.gz, infusiondrug.csv.gz)",
        observed_volume_metric="2,520 multicenter ICU stays, 1.63M vital parameter records observed",
        primary_assets=["ICU_BEDSIDE_TELEMETRY_GW", "VENTILATOR_TELEMETRY_SERVER", "SMART_INFUSION_PUMP_GW"],
        milestones=[
            PathwayMilestone(
                id="MS_ICU_01",
                name="Continuous Hemodynamic & Oxygenation Telemetry",
                clinical_purpose="Second-by-second ECG, MAP, and SaO2 monitoring with central station alarm annunciation",
                underlying_digital_dependency="Bedside Physiological Telemetry Gateway (Generic Class)",
                observed_table_field="eicu: vitalPeriodic.csv.gz (heartrate, sao2, systemicmean)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_ICU_02",
                name="Life-Critical Mechanical Ventilation Titration",
                clinical_purpose="Continuous delivery of delivered oxygen (FiO2) and positive end-expiratory pressure (PEEP)",
                underlying_digital_dependency="ICU Mechanical Ventilator Telemetry Server (Generic Class)",
                observed_table_field="eicu: respiratoryCharting.csv.gz (respchartvaluelabel, respchartvalue)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_ICU_03",
                name="Vasoactive Smart Infusion Pump Titration",
                clinical_purpose="Closed-loop rate titrations for norepinephrine, dopamine, or propofol",
                underlying_digital_dependency="Smart IV Infusion Pump Wireless Gateway (Generic Class)",
                observed_table_field="eicu: infusiondrug.csv.gz (drugname, drugrate, infusionrate)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            )
        ]
    ),
    "PATHWAY_LAB": CarePathwayShadow(
        id="PATHWAY_LAB",
        name="Clinical Diagnostics & Laboratory",
        description="STAT specimen accessioning, blood gas analysis, troponin testing, and panic value broadcast alerting.",
        clinical_acuity_weight=0.85,
        source_dataset="MIMIC-IV Clinical Demo v2.2 (hosp/labevents.csv.gz)",
        observed_volume_metric="107,727 real lab observations, 17,219 abnormal flags observed",
        primary_assets=["LAB_ANALYZER_LIS", "EHR_CORE_GATEWAY"],
        milestones=[
            PathwayMilestone(
                id="MS_LAB_01",
                name="Automated Specimen Barcode Accessioning",
                clinical_purpose="Match drawn specimen tube to computerized physician order",
                underlying_digital_dependency="Laboratory Information System (LIS) Interface (Generic Class)",
                observed_table_field="mimic-iv: hosp/labevents.csv.gz (specimen_id, itemid)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_LAB_02",
                name="Analyzer Result Processing & Abnormal Flagging",
                clinical_purpose="Chemistry and hematology automated value calculation",
                underlying_digital_dependency="Clinical Chemistry & Hematology Analyzer Interface (Generic Class)",
                observed_table_field="mimic-iv: hosp/labevents.csv.gz (valuenum, valueuom, flag)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_LAB_03",
                name="STAT Critical Panic Value Broadcast",
                clinical_purpose="Immediate alert transmission to attending clinician for life-threatening lab values",
                underlying_digital_dependency="LIS-to-EHR Notification Bus (Generic Class)",
                observed_table_field="mimic-iv: hosp/labevents.csv.gz (priority, charttime)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            )
        ]
    ),
    "PATHWAY_PHARM": CarePathwayShadow(
        id="PATHWAY_PHARM",
        name="Inpatient Pharmacy & Closed-Loop eMAR",
        description="Computerized provider order verification, automated cabinet release, and bedside five-rights barcode scanning.",
        clinical_acuity_weight=0.90,
        source_dataset="MIMIC-IV Clinical Demo v2.2 (hosp/poe.csv.gz, hosp/emar.csv.gz, hosp/emar_detail.csv.gz)",
        observed_volume_metric="45,154 POE orders, 35,835 eMAR administrations observed",
        primary_assets=["EMAR_BCMA_SERVER", "EHR_CORE_GATEWAY"],
        milestones=[
            PathwayMilestone(
                id="MS_PHARM_01",
                name="Computerized Physician Order Verification",
                clinical_purpose="Pharmacist review of dose, route, drug-drug interactions, and clinical indication",
                underlying_digital_dependency="Provider Order Entry (POE) Module (Generic Class)",
                observed_table_field="mimic-iv: hosp/poe.csv.gz (order_type, order_subtype)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_PHARM_02",
                name="Automated Dispensing Cabinet Drawer Release",
                clinical_purpose="Electronic release of unit-dose medications at patient ward unit",
                underlying_digital_dependency="Automated Dispensing Cabinet Interface (Generic Class)",
                observed_table_field="mimic-iv-ed: pyxis.csv.gz (name, charttime)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_PHARM_03",
                name="Bedside Five-Rights Barcode Verification (BCMA)",
                clinical_purpose="Scan patient wristband and medication packet to prevent administration errors",
                underlying_digital_dependency="Closed-Loop Barcode Server (eMAR) (Generic Class)",
                observed_table_field="mimic-iv: hosp/emar_detail.csv.gz (reason_for_no_barcode)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            )
        ]
    ),
    "PATHWAY_SURG": CarePathwayShadow(
        id="PATHWAY_SURG",
        name="Surgical & Perioperative Services",
        description="Pre-operative checklist validation, intraoperative physiological telemetry, and post-anesthesia care tracking.",
        clinical_acuity_weight=0.95,
        source_dataset="MIMIC-IV Clinical (hosp/services.csv.gz, icu/chartevents.csv.gz)",
        observed_volume_metric="319 clinical service transfers, operative service profiles observed",
        primary_assets=["ICU_BEDSIDE_TELEMETRY_GW", "EHR_CORE_GATEWAY"],
        milestones=[
            PathwayMilestone(
                id="MS_SURG_01",
                name="Pre-Operative Anesthesia Readiness Sign-Off",
                clinical_purpose="Verify lab clearance, cardiac evaluation, and blood bank cross-match",
                underlying_digital_dependency="Core EHR Surgical Scheduling & Labs Module (Generic Class)",
                observed_table_field="mimic-iv: hosp/services.csv.gz (curr_service)",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_SURG_02",
                name="Intraoperative Anesthesia Telemetry Streaming",
                clinical_purpose="Continuous monitoring of end-tidal CO2, depth of anesthesia, and arterial blood pressure",
                underlying_digital_dependency="Operating Room Medical Device Bus (Generic Class)",
                observed_table_field="eicu: vitalPeriodic.csv.gz & chartevents.csv.gz",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            ),
            PathwayMilestone(
                id="MS_SURG_03",
                name="Post-Anesthesia Care Unit (PACU) Recovery Tracking",
                clinical_purpose="Monitor extubation parameters and hemodynamic stabilization prior to ward admission",
                underlying_digital_dependency="PACU Bedside Telemetry Station (Generic Class)",
                observed_table_field="mimic-iv: icu/chartevents.csv.gz",
                dependency_derivation="STATIC_REFERENCE",
                observation_derivation="DATA_DERIVED"
            )
        ]
    )
}

class CarePathwayService:
    @staticmethod
    def get_all_pathways() -> List[Dict[str, Any]]:
        return [p.model_dump() for p in CARE_PATHWAYS.values()]

    @staticmethod
    def get_pathway(pathway_id: str) -> Optional[Dict[str, Any]]:
        p = CARE_PATHWAYS.get(pathway_id)
        return p.model_dump() if p else None

care_pathway_service = CarePathwayService()

