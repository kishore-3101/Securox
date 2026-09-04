"""
CAREGUARD — MIMIC-IV Clinical Database Loader
Streams authentic hospital, pharmacy, lab, and ICU clinical records from mimic-iv-clinical-database-demo-2.2.zip:
- hosp/poe.csv.gz & poe_detail.csv.gz (Provider Order Entry)
- hosp/emar.csv.gz & emar_detail.csv.gz (Barcode Medication Administration)
- hosp/labevents.csv.gz (Clinical Laboratory Diagnostic Tests)
- icu/chartevents.csv.gz (Bedside Physiological Telemetry)
- hosp/prescriptions.csv.gz & hosp/pharmacy.csv.gz (Inpatient Pharmacy)
- icu/icustays.csv.gz (Intensive Care Unit Admissions)
- hosp/services.csv.gz (Clinical Service Transitions)
Zero Synthetic Data Policy.
"""

import os
import gzip
import zipfile
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from healthcare_core.core.config import settings
from healthcare_core.data.normalizers.sanitizer import sanitizer

logger = logging.getLogger("careguard.loaders.mimic_clinical")

class MimicClinicalLoader:
    def __init__(self, datasets_dir: Optional[str] = None):
        self.datasets_dir = datasets_dir or settings.DATASETS_DIR
        self.zip_path = os.path.join(self.datasets_dir, "mimic-iv-clinical-database-demo-2.2.zip")
        self.is_available = os.path.exists(self.zip_path)
        
        self.poe_sample: List[Dict[str, Any]] = []
        self.emar_sample: List[Dict[str, Any]] = []
        self.emar_detail_sample: List[Dict[str, Any]] = []
        self.labevents_sample: List[Dict[str, Any]] = []
        self.chartevents_sample: List[Dict[str, Any]] = []
        self.prescriptions_sample: List[Dict[str, Any]] = []
        self.icustays_sample: List[Dict[str, Any]] = []
        self.services_sample: List[Dict[str, Any]] = []

        self.stats: Dict[str, Any] = {}
        self._loaded = False

    def load(self):
        if self._loaded or not self.is_available:
            return

        logger.info(f"Loading authentic MIMIC-IV Clinical records from {self.zip_path}...")
        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                names = z.namelist()

                # 1. Provider Order Entry (POE)
                for n in names:
                    if n.endswith("hosp/poe.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_poe = pd.read_csv(gf, nrows=5000)
                                self.poe_sample = sanitizer.clean_records(df_poe, 50)
                                self.stats["poe_order_types"] = df_poe["order_type"].value_counts().head(5).to_dict()
                                self.stats["total_poe_sampled"] = len(df_poe)

                # 2. Barcode Medication Administration (eMAR)
                for n in names:
                    if n.endswith("hosp/emar.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_emar = pd.read_csv(gf, nrows=5000)
                                self.emar_sample = sanitizer.clean_records(df_emar, 50)
                                self.stats["emar_event_types"] = df_emar["event_txt"].value_counts().head(5).to_dict()
                    if n.endswith("hosp/emar_detail.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_emar_dt = pd.read_csv(gf, nrows=5000)
                                self.emar_detail_sample = sanitizer.clean_records(df_emar_dt, 50)
                                if "reason_for_no_barcode" in df_emar_dt.columns:
                                    self.stats["unverified_barcode_reasons"] = df_emar_dt["reason_for_no_barcode"].value_counts().dropna().to_dict()

                # 3. Clinical Laboratory Diagnostic Results
                for n in names:
                    if n.endswith("hosp/labevents.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_labs = pd.read_csv(gf, nrows=5000)
                                self.labevents_sample = sanitizer.clean_records(df_labs, 50)
                                self.stats["abnormal_lab_flags"] = int((df_labs["flag"] == "abnormal").sum()) if "flag" in df_labs.columns else 0
                                self.stats["total_labs_sampled"] = len(df_labs)

                # 4. ICU Bedside Physiological Telemetry (chartevents)
                for n in names:
                    if n.endswith("icu/chartevents.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_chart = pd.read_csv(gf, nrows=5000)
                                self.chartevents_sample = sanitizer.clean_records(df_chart, 50)
                                self.stats["total_chartevents_sampled"] = len(df_chart)

                # 5. Inpatient Pharmacy & Prescriptions
                for n in names:
                    if n.endswith("hosp/prescriptions.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_rx = pd.read_csv(gf, nrows=5000)
                                self.prescriptions_sample = sanitizer.clean_records(df_rx, 50)
                                self.stats["prescription_routes"] = df_rx["route"].value_counts().head(5).to_dict() if "route" in df_rx.columns else {}

                # 6. ICU Stays
                for n in names:
                    if n.endswith("icu/icustays.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_icu = pd.read_csv(gf)
                                self.icustays_sample = sanitizer.clean_records(df_icu, 50)
                                self.stats["total_icustays"] = len(df_icu)
                                self.stats["first_careunits"] = df_icu["first_careunit"].value_counts().to_dict() if "first_careunit" in df_icu.columns else {}

                # 7. Services
                for n in names:
                    if n.endswith("hosp/services.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_svc = pd.read_csv(gf)
                                self.services_sample = sanitizer.clean_records(df_svc, 50)
                                self.stats["clinical_services"] = df_svc["curr_service"].value_counts().to_dict() if "curr_service" in df_svc.columns else {}

            self._loaded = True
            logger.info("MIMIC-IV Clinical loader successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to load MIMIC-IV Clinical: {e}")

    def get_table_records(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.load()
        mapping = {
            "poe": self.poe_sample,
            "emar": self.emar_sample,
            "emar_detail": self.emar_detail_sample,
            "labevents": self.labevents_sample,
            "chartevents": self.chartevents_sample,
            "mimic_clinical_vitals": self.chartevents_sample,
            "prescriptions": self.prescriptions_sample,
            "icustays": self.icustays_sample,
            "services": self.services_sample
        }
        return mapping.get(table_name, [])[:limit]

mimic_clinical_loader = MimicClinicalLoader()

