"""
Central path + seed configuration. Every other module imports from here so
there is exactly one place that knows where things live on disk.
"""
from pathlib import Path

# Repo root = two levels up from this file (src/config/paths.py -> repo root)
ROOT = Path(__file__).resolve().parents[2]

# --- raw (read-only, never written to by any pipeline code) ---
RAW_DIR = ROOT / "data" / "raw"
INDIAN_BANKING_RAW = RAW_DIR / "indian_banking" / "indian_banking_transactions.csv"
ULB_RAW = RAW_DIR / "ulb" / "creditcard.csv"
AMLSIM_RAW_ZIP = RAW_DIR / "amlsim" / "AMLSim-master.zip"

# Path *inside* the zip to the raw AMLSim simulator output we use.
AMLSIM_ZIP_TMP_PREFIX = "AMLSim-master/AMLSim-master/tmp/1K/"
AMLSIM_ZIP_ACCOUNTS = AMLSIM_ZIP_TMP_PREFIX + "accounts.csv"
AMLSIM_ZIP_TRANSACTIONS = AMLSIM_ZIP_TMP_PREFIX + "transactions.csv"
AMLSIM_ZIP_ALERT_MEMBERS = AMLSIM_ZIP_TMP_PREFIX + "alert_members.csv"
AMLSIM_ZIP_NORMAL_MODELS = AMLSIM_ZIP_TMP_PREFIX + "normal_models.csv"

# The pre-existing reference sub-project bundled inside the same zip.
# NEVER loaded by our pipeline for training/features — reference-only pointer.
AMLSIM_ZIP_REFERENCE_PREFIX = "AMLSim-master/AMLSim-master/aml_detection/"

# --- processed outputs ---
PROCESSED_DIR = ROOT / "data" / "processed"
INDIAN_BANKING_PROCESSED_DIR = PROCESSED_DIR / "indian_banking"
ULB_PROCESSED_DIR = PROCESSED_DIR / "ulb"
AMLSIM_PROCESSED_DIR = PROCESSED_DIR / "amlsim"

# --- artifacts ---
ARTIFACTS_DIR = ROOT / "artifacts"
PREPROCESSORS_DIR = ARTIFACTS_DIR / "preprocessors"
METRICS_DIR = ARTIFACTS_DIR / "metrics"
EDA_METRICS_DIR = METRICS_DIR / "eda"
EDA_DIR = ARTIFACTS_DIR / "eda"
FEATURE_DICTIONARY_PATH = METRICS_DIR / "feature_dictionary.json"

RANDOM_SEED = 42


def ensure_dirs() -> None:
    for d in [
        INDIAN_BANKING_PROCESSED_DIR,
        ULB_PROCESSED_DIR,
        AMLSIM_PROCESSED_DIR,
        PREPROCESSORS_DIR,
        METRICS_DIR,
        EDA_METRICS_DIR,
        EDA_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
