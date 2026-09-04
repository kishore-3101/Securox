"""
CAREGUARD — MIMIC-IV-ED Dataset Loader
Streams and parses real de-identified emergency department records from mimic-iv-ed-demo-2.2.zip:
- edstays (intime, outtime, arrival_transport, disposition)
- triage (temperature, heartrate, resprate, o2sat, sbp, dbp, pain, acuity ESI 1-5, chiefcomplaint)
- vitalsign (bedside vital observations)
- pyxis (automated medication dispensing cabinet transactions)
- medrecon (medication reconciliation)
- diagnosis (emergency ICD-9/10 diagnoses)
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

logger = logging.getLogger("careguard.loaders.mimic_ed")

class MimicEdLoader:
    def __init__(self, datasets_dir: Optional[str] = None):
        self.datasets_dir = datasets_dir or settings.DATASETS_DIR
        self.zip_path = os.path.join(self.datasets_dir, "mimic-iv-ed-demo-2.2.zip")
        self.is_available = os.path.exists(self.zip_path)
        
        self.edstays_sample: List[Dict[str, Any]] = []
        self.triage_sample: List[Dict[str, Any]] = []
        self.vitalsign_sample: List[Dict[str, Any]] = []
        self.pyxis_sample: List[Dict[str, Any]] = []
        self.medrecon_sample: List[Dict[str, Any]] = []
        self.diagnosis_sample: List[Dict[str, Any]] = []
        
        self.stats: Dict[str, Any] = {}
        self._loaded = False

    def load(self):
        if self._loaded or not self.is_available:
            return

        logger.info(f"Loading authentic MIMIC-IV-ED data from {self.zip_path}...")
        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                # 1. ED Stays
                if "mimic-iv-ed-demo-2.2/ed/edstays.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/edstays.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_stays = pd.read_csv(gf)
                            self.edstays_sample = sanitizer.clean_records(df_stays, 50)
                            self.stats["total_stays"] = len(df_stays)
                            self.stats["ambulance_arrivals"] = int((df_stays["arrival_transport"] == "AMBULANCE").sum())
                            self.stats["walkin_arrivals"] = int((df_stays["arrival_transport"] == "WALK IN").sum())
                            self.stats["dispositions"] = df_stays["disposition"].value_counts().to_dict()

                # 2. Triage
                if "mimic-iv-ed-demo-2.2/ed/triage.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/triage.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_triage = pd.read_csv(gf)
                            self.triage_sample = sanitizer.clean_records(df_triage, 50)
                            self.stats["total_triage"] = len(df_triage)
                            self.stats["high_acuity_esi_1_2"] = int((df_triage["acuity"] <= 2).sum())
                            self.stats["moderate_acuity_esi_3"] = int((df_triage["acuity"] == 3).sum())
                            self.stats["low_acuity_esi_4_5"] = int((df_triage["acuity"] >= 4).sum())
                            self.stats["mean_heartrate"] = float(round(df_triage["heartrate"].mean(), 1)) if not df_triage["heartrate"].isna().all() else None

                # 3. Pyxis Automated Medication Dispensing Cabinets
                if "mimic-iv-ed-demo-2.2/ed/pyxis.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/pyxis.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_pyxis = pd.read_csv(gf)
                            self.pyxis_sample = sanitizer.clean_records(df_pyxis, 50)
                            self.stats["total_pyxis_events"] = len(df_pyxis)
                            self.stats["unique_medications_dispensed"] = int(df_pyxis["name"].nunique())
                            self.stats["top_dispensed_meds"] = df_pyxis["name"].value_counts().head(5).to_dict()

                # 4. Vital Signs
                if "mimic-iv-ed-demo-2.2/ed/vitalsign.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/vitalsign.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_vitals = pd.read_csv(gf)
                            self.vitalsign_sample = sanitizer.clean_records(df_vitals, 50)
                            self.stats["total_vitalsign_observations"] = len(df_vitals)

                # 5. Medrecon
                if "mimic-iv-ed-demo-2.2/ed/medrecon.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/medrecon.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_recon = pd.read_csv(gf)
                            self.medrecon_sample = sanitizer.clean_records(df_recon, 50)
                            self.stats["total_medrecon_events"] = len(df_recon)

                # 6. Diagnosis
                if "mimic-iv-ed-demo-2.2/ed/diagnosis.csv.gz" in z.namelist():
                    with z.open("mimic-iv-ed-demo-2.2/ed/diagnosis.csv.gz") as f:
                        with gzip.open(f, "rt", encoding="utf-8") as gf:
                            df_diag = pd.read_csv(gf)
                            self.diagnosis_sample = sanitizer.clean_records(df_diag, 50)
                            self.stats["total_ed_diagnoses"] = len(df_diag)

            self._loaded = True
            logger.info("MIMIC-IV-ED loader successfully initialized with organic data.")
        except Exception as e:
            logger.error(f"Failed to load MIMIC-IV-ED: {e}")

    def get_table_records(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.load()
        mapping = {
            "edstays": self.edstays_sample,
            "mimic_ed_edstays": self.edstays_sample,
            "triage": self.triage_sample,
            "mimic_ed_triage": self.triage_sample,
            "vitalsign": self.vitalsign_sample,
            "mimic_ed_vitalsign": self.vitalsign_sample,
            "pyxis": self.pyxis_sample,
            "medrecon": self.medrecon_sample,
            "diagnosis": self.diagnosis_sample
        }
        return mapping.get(table_name, [])[:limit]

mimic_ed_loader = MimicEdLoader()

