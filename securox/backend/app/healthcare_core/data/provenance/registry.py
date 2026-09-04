"""
CAREGUARD — Dataset Provenance & Evidence Registry
Enforces transparency and data lineage across all ingested organic datasets.
Zero Synthetic Data Policy.
"""

from typing import Dict, Any, List, Optional

DATASET_PROVENANCE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "MIMIC_IV_ED": {
        "id": "MIMIC_IV_ED",
        "name": "MIMIC-IV Emergency Department Demo (v2.2)",
        "file_name": "mimic-iv-ed-demo-2.2.zip",
        "source": "Beth Israel Deaconess Medical Center / PhysioNet",
        "provenance_type": "Real Clinical Hospital Emergency Telemetry",
        "is_organic": True,
        "is_synthetic": False,
        "license": "PhysioNet Credentialed / Open Demo License",
        "collection_years": "2011–2019",
        "primary_domain": "Emergency Intake, Acuity Triage & Pyxis Medication Dispensing",
        "record_counts": {
            "edstays": 222,
            "triage": 222,
            "vitalsign": 1038,
            "pyxis": 1082,
            "medrecon": 2764,
            "diagnosis": 545
        },
        "careguard_role": "Primary evidence source for Emergency Intake Care Pathway Shadow & Pyxis cabinet access profiling."
    },
    "MIMIC_IV_CLINICAL": {
        "id": "MIMIC_IV_CLINICAL",
        "name": "MIMIC-IV Clinical Database Demo (v2.2)",
        "file_name": "mimic-iv-clinical-database-demo-2.2.zip",
        "source": "Beth Israel Deaconess Medical Center / MIT LCP",
        "provenance_type": "Real Inpatient, POE, eMAR & ICU Clinical Records",
        "is_organic": True,
        "is_synthetic": False,
        "license": "PhysioNet Open Access Research Demo",
        "collection_years": "2008–2019",
        "primary_domain": "Inpatient, Provider Order Entry (POE), Barcode Verification (eMAR) & ICU Telemetry",
        "record_counts": {
            "chartevents": 668862,
            "labevents": 107727,
            "emar": 35835,
            "emar_detail": 72018,
            "poe": 45154,
            "prescriptions": 18087,
            "pharmacy": 15306,
            "icustays": 140,
            "transfers": 1190,
            "services": 319,
            "admissions": 275
        },
        "careguard_role": "Primary evidence source for Critical Care ICU, Inpatient Pharmacy, and Lab Diagnostics pathways."
    },
    "EICU_CRD": {
        "id": "EICU_CRD",
        "name": "eICU Collaborative Research Database Demo (v2.0.1)",
        "file_name": "eicu-collaborative-research-database-demo-2.0.1.zip",
        "source": "Philips Healthcare & MIT Laboratory for Computational Physiology",
        "provenance_type": "Real Multicenter Critical Care Telehealth Telemetry (20 US Hospitals)",
        "is_organic": True,
        "is_synthetic": False,
        "license": "PhysioNet Open Research Demo",
        "collection_years": "2014–2015",
        "primary_domain": "Multicenter ICU Telehealth, Mechanical Ventilation & Connected Bedside Devices",
        "record_counts": {
            "patient": 2520,
            "vitalPeriodic": 1634960,
            "nurseCharting": 1477163,
            "lab": 434660,
            "vitalAperiodic": 274088,
            "respiratoryCharting": 176089,
            "medication": 75604,
            "infusiondrug": 38256
        },
        "careguard_role": "Multicenter ICU baseline, mechanical ventilator telemetry, and continuous smart IV infusion pump delivery."
    },
    "ONC_HEALTH_IT": {
        "id": "ONC_HEALTH_IT",
        "name": "U.S. ONC Health IT Certified Infrastructure & API Ecosystem Datasets",
        "file_name": "hospital-promoting-interoperability-chpl-linkage.csv & ecosystem-apps-software-marketplace-history.csv",
        "source": "U.S. Office of the National Coordinator for Health IT (healthit.gov) / CMS",
        "provenance_type": "Real Public-Sector Health-IT Infrastructure & API Certification Records",
        "is_organic": True,
        "is_synthetic": False,
        "license": "U.S. Federal Government Open Data (Public Use Files)",
        "collection_years": "2015–2024",
        "primary_domain": "Hospital Certified EHR Infrastructure, SMART-on-FHIR APIs & Electronic Clinical Information Exchange",
        "record_counts": {
            "chpl_linkage": 68447,
            "ecosystem_apps": 8089,
            "ehr_vendors": 4258,
            "aha_interoperability": 625,
            "mu_report": 1934820
        },
        "careguard_role": "Defines digital healthcare infrastructure, certified EHR vendor profiles (Epic, Cerner), and FHIR API attack surface."
    }
}

DATA_COVERAGE_MATRIX = {
    "clinical_workflows": {
        "status": "AVAILABLE",
        "coverage": "FULL",
        "derivation": "DATA_DERIVED",
        "source": "MIMIC-IV Clinical Database v2.2 & MIMIC-IV-ED v2.2",
        "description": "Provider orders (POE), medication administration (eMAR/BCMA), ED triage, and Pyxis dispensing transactions."
    },
    "icu_physiological_telemetry": {
        "status": "AVAILABLE",
        "coverage": "FULL",
        "derivation": "DATA_DERIVED",
        "source": "eICU Collaborative Research Database v2.0.1",
        "description": "High-frequency periodic vital signs (HR, SaO2, NIBP), mechanical ventilator parameters, and infusion rates across multicenter ICU units."
    },
    "health_it_infrastructure": {
        "status": "AVAILABLE",
        "coverage": "FULL",
        "derivation": "DATA_DERIVED",
        "source": "U.S. ONC Health IT Certified Technology & API Marketplace Datasets",
        "description": "Certified EHR developer profiles, SMART-on-FHIR public endpoint linkages, and hospital interoperability metrics."
    },
    "network_packet_telemetry": {
        "status": "NOT_AVAILABLE",
        "coverage": "NONE",
        "derivation": "NOT_AVAILABLE",
        "source": None,
        "description": "Raw PCAP network traces, NetFlow/IPFIX, and switch port spans are absent in public HIPAA-deidentified clinical repositories.",
        "impact": "Network compromise and packet-level intrusions cannot be directly observed; anomalies are inferred from operational time-series deviations."
    },
    "iomt_physical_hardware_inventory": {
        "status": "NOT_AVAILABLE",
        "coverage": "NONE",
        "derivation": "NOT_AVAILABLE",
        "source": None,
        "description": "Physical MAC addresses, device serial numbers, and switch VLAN assignments are excluded from deidentified medical records.",
        "impact": "Telemetry is monitored at the clinical stream level; physical asset counts are not fabricated."
    }
}

class ProvenanceLedger:
    @staticmethod
    def wrap_field(value: Any, derivation: str, source: Optional[str] = None, note: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates a defensible field-level provenance descriptor.
        Derivations: DATA_DERIVED | INFERRED | REFERENCE | NOT_AVAILABLE
        """
        return {
            "value": value,
            "derivation": derivation,
            "source": source,
            "note": note
        }

    @staticmethod
    def get_provenance_summary() -> Dict[str, Any]:
        return {
            "policy": "VERIFIED_CLINICAL_DATA_POLICY",
            "guarantee": "All operational metrics, telemetry, and pathways are derived strictly from authentic healthcare records.",
            "data_coverage": DATA_COVERAGE_MATRIX,
            "overall_observability_confidence": "MEDIUM",
            "confidence_rationale": "Clinical and ICU parameters are fully authentic; network-level packet capture telemetry is not available.",
            "registered_datasets": DATASET_PROVENANCE_REGISTRY
        }

    @staticmethod
    def get_dataset(dataset_id: str) -> Dict[str, Any]:
        return DATASET_PROVENANCE_REGISTRY.get(dataset_id, {})

    @staticmethod
    def get_data_coverage() -> Dict[str, Any]:
        return DATA_COVERAGE_MATRIX

provenance_ledger = ProvenanceLedger()

