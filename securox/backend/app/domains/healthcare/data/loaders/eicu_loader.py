"""
CAREGUARD — eICU Collaborative Research Database Loader
Streams real multicenter critical care and connected medical device telemetry from eicu-collaborative-research-database-demo-2.0.1.zip:
- vitalPeriodic.csv.gz (Continuous bedside monitor vital parameters)
- respiratoryCharting.csv.gz (Mechanical ventilator telemetry, FiO2, PEEP)
- infusiondrug.csv.gz (Smart IV Infusion Pump delivery rates and vasoactive titrations)
- patient.csv.gz (Multicenter ICU stays across 20 US hospital centers)
- lab.csv.gz (Clinical laboratory tests)
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

logger = logging.getLogger("careguard.loaders.eicu")

class EicuLoader:
    def __init__(self, datasets_dir: Optional[str] = None):
        self.datasets_dir = datasets_dir or settings.DATASETS_DIR
        self.zip_path = os.path.join(self.datasets_dir, "eicu-collaborative-research-database-demo-2.0.1.zip")
        self.is_available = os.path.exists(self.zip_path)
        
        self.vital_periodic_sample: List[Dict[str, Any]] = []
        self.respiratory_sample: List[Dict[str, Any]] = []
        self.infusion_sample: List[Dict[str, Any]] = []
        self.patient_sample: List[Dict[str, Any]] = []
        self.lab_sample: List[Dict[str, Any]] = []

        self.stats: Dict[str, Any] = {}
        self._loaded = False

    def load(self):
        if self._loaded or not self.is_available:
            return

        logger.info(f"Loading authentic eICU multicenter critical care data from {self.zip_path}...")
        try:
            with zipfile.ZipFile(self.zip_path, "r") as z:
                names = z.namelist()

                # 1. Continuous Bedside Monitor Telemetry (vitalPeriodic)
                for n in names:
                    if n.endswith("vitalPeriodic.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_vit = pd.read_csv(gf, nrows=5000)
                                self.vital_periodic_sample = sanitizer.clean_records(df_vit, 50)
                                self.stats["bedside_monitor_features"] = [c for c in df_vit.columns if c not in ["patientunitstayid", "observationoffset"]]
                                self.stats["mean_icu_heartrate"] = float(round(df_vit["heartrate"].mean(), 1)) if "heartrate" in df_vit.columns and not df_vit["heartrate"].isna().all() else None
                                self.stats["mean_sao2"] = float(round(df_vit["sao2"].mean(), 1)) if "sao2" in df_vit.columns and not df_vit["sao2"].isna().all() else None

                # 2. Mechanical Ventilator Telemetry (respiratoryCharting)
                for n in names:
                    if n.endswith("respiratoryCharting.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_resp = pd.read_csv(gf, nrows=5000)
                                self.respiratory_sample = sanitizer.clean_records(df_resp, 50)
                                if "respchartvaluelabel" in df_resp.columns:
                                    self.stats["ventilator_parameters"] = df_resp["respchartvaluelabel"].value_counts().head(8).to_dict()

                # 3. Smart IV Infusion Pump Telemetry (infusiondrug)
                for n in names:
                    if n.endswith("infusiondrug.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_inf = pd.read_csv(gf, nrows=5000)
                                self.infusion_sample = sanitizer.clean_records(df_inf, 50)
                                if "drugname" in df_inf.columns:
                                    self.stats["top_smart_pump_drugs"] = df_inf["drugname"].value_counts().head(5).to_dict()

                # 4. Multicenter Patient ICU Stays
                for n in names:
                    if n.endswith("patient.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_pat = pd.read_csv(gf)
                                self.patient_sample = sanitizer.clean_records(df_pat, 50)
                                self.stats["total_multicenter_stays"] = len(df_pat)
                                if "hospitalid" in df_pat.columns:
                                    self.stats["unique_hospital_centers"] = int(df_pat["hospitalid"].nunique())
                                if "hospitaladmitsource" in df_pat.columns:
                                    self.stats["hospital_admit_sources"] = df_pat["hospitaladmitsource"].value_counts().head(5).to_dict()

                # 5. Labs
                for n in names:
                    if n.endswith("lab.csv.gz"):
                        with z.open(n) as f:
                            with gzip.open(f, "rt", encoding="utf-8") as gf:
                                df_lab = pd.read_csv(gf, nrows=5000)
                                self.lab_sample = sanitizer.clean_records(df_lab, 50)

            self._loaded = True
            logger.info("eICU loader successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to load eICU: {e}")

    def get_table_records(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.load()
        mapping = {
            "vitalPeriodic": self.vital_periodic_sample,
            "respiratoryCharting": self.respiratory_sample,
            "infusiondrug": self.infusion_sample,
            "patient": self.patient_sample,
            "eicu_patient": self.patient_sample,
            "lab": self.lab_sample,
            "eicu_lab": self.lab_sample
        }
        return mapping.get(table_name, [])[:limit]

eicu_loader = EicuLoader()

