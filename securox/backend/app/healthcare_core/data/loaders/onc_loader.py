"""
CAREGUARD — ONC Health IT & FHIR Ecosystem Dataset Loader
Parses real public-sector Health IT infrastructure and API certification records:
- hospital-promoting-interoperability-chpl-linkage.csv (68,447 hospital facility to EHR product linkages)
- ecosystem-apps-software-marketplace-history.csv (8,089 SMART-on-FHIR software apps and API marketplace integrations)
- EHR-vendors-count-dataset.csv (EHR vendor market shares and certification editions)
- aha.csv (American Hospital Association interoperability survey)
Zero Synthetic Data Policy.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

from healthcare_core.core.config import settings
from healthcare_core.data.normalizers.sanitizer import sanitizer

logger = logging.getLogger("careguard.loaders.onc")

class OncLoader:
    def __init__(self, datasets_dir: Optional[str] = None):
        self.datasets_dir = datasets_dir or settings.DATASETS_DIR
        
        self.chpl_path = os.path.join(self.datasets_dir, "hospital-promoting-interoperability-chpl-linkage.csv")
        self.apps_path = os.path.join(self.datasets_dir, "ecosystem-apps-software-marketplace-history.csv")
        self.vendors_path = os.path.join(self.datasets_dir, "EHR-vendors-count-dataset.csv")
        self.aha_path = os.path.join(self.datasets_dir, "aha.csv")
        
        self.chpl_sample: List[Dict[str, Any]] = []
        self.apps_sample: List[Dict[str, Any]] = []
        self.vendors_sample: List[Dict[str, Any]] = []
        self.aha_sample: List[Dict[str, Any]] = []

        self.stats: Dict[str, Any] = {}
        self._loaded = False

    def load(self):
        if self._loaded:
            return

        logger.info("Loading authentic ONC Health-IT infrastructure datasets...")
        try:
            # 1. Hospital CHPL Linkage
            if os.path.exists(self.chpl_path):
                df_chpl = pd.read_csv(self.chpl_path, nrows=5000, encoding="latin-1")
                self.chpl_sample = sanitizer.clean_records(df_chpl, 50)
                if "Vendor_Name" in df_chpl.columns:
                    self.stats["top_ehr_vendors"] = df_chpl["Vendor_Name"].value_counts().head(5).to_dict()
                self.stats["total_chpl_facilities_sampled"] = len(df_chpl)

            # 2. Ecosystem Apps & SMART-on-FHIR Marketplace
            if os.path.exists(self.apps_path):
                df_apps = pd.read_csv(self.apps_path, nrows=5000, encoding="latin-1")
                self.apps_sample = sanitizer.clean_records(df_apps, 50)
                self.stats["total_fhir_apps_sampled"] = len(df_apps)
                if "App_Category" in df_apps.columns:
                    self.stats["app_categories"] = df_apps["App_Category"].value_counts().head(5).to_dict()

            # 3. EHR Vendors
            if os.path.exists(self.vendors_path):
                df_ven = pd.read_csv(self.vendors_path, nrows=1000, encoding="latin-1")
                self.vendors_sample = sanitizer.clean_records(df_ven, 50)

            # 4. AHA Interoperability Survey
            if os.path.exists(self.aha_path):
                df_aha = pd.read_csv(self.aha_path, encoding="latin-1")
                self.aha_sample = sanitizer.clean_records(df_aha, 50)
                self.stats["aha_respondents"] = len(df_aha)

            self._loaded = True
            logger.info("ONC Health-IT loader successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to load ONC datasets: {e}")

    def get_table_records(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        self.load()
        mapping = {
            "chpl_linkage": self.chpl_sample,
            "ecosystem_apps": self.apps_sample,
            "ehr_vendors": self.vendors_sample,
            "aha": self.aha_sample
        }
        return mapping.get(table_name, [])[:limit]

onc_loader = OncLoader()

