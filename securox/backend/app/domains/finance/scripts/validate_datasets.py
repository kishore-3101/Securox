"""
validate_datasets.py

Read-only validation pass over the three raw FINANCE-subsystem datasets.
This script does NOT train anything and does NOT mutate any raw file.
It only prints back what is actually present in each dataset so we have a
ground-truth reference before any feature engineering happens.

Run:
    python scripts/validate_datasets.py
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def validate_indian_banking() -> None:
    path = RAW / "indian_banking" / "indian_banking_transactions.csv"
    section(f"INDIAN BANKING TRANSACTIONS  ({path})")
    if not path.exists():
        print("MISSING FILE")
        return

    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("\ndtypes:\n", df.dtypes)
    print("\nnull counts (non-zero only):")
    nulls = df.isna().sum()
    print(nulls[nulls > 0])
    if "is_fraud" in df.columns:
        print("\ntarget column 'is_fraud' value counts:")
        print(df["is_fraud"].value_counts())
    if "transaction_date" in df.columns:
        print(
            "\ndate range:",
            df["transaction_date"].min(),
            "to",
            df["transaction_date"].max(),
        )
    print("\nduplicate transaction_id count:", df["transaction_id"].duplicated().sum()
          if "transaction_id" in df.columns else "n/a")


def validate_ulb() -> None:
    path = RAW / "ulb" / "creditcard.csv"
    section(f"ULB CREDIT CARD FRAUD  ({path})")
    if not path.exists():
        print("MISSING FILE")
        return

    df = pd.read_csv(path)
    print("shape:", df.shape)
    print("\ndtypes:\n", df.dtypes)
    print("\nnull counts (non-zero only):")
    nulls = df.isna().sum()
    print(nulls[nulls > 0] if nulls.sum() else "none")
    if "Class" in df.columns:
        print("\ntarget column 'Class' value counts:")
        print(df["Class"].value_counts())
    print(
        "\nNOTE: columns V1-V28 are PCA-anonymized by the original dataset "
        "publisher. No semantic meaning is assumed or inferred for them "
        "anywhere in this codebase."
    )


def validate_amlsim() -> None:
    zip_path = RAW / "amlsim" / "AMLSim-master.zip"
    section(f"AMLSIM ZIP  ({zip_path})")
    if not zip_path.exists():
        print("MISSING FILE")
        return

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        print("total entries in zip:", len(names))

        # Locate the raw simulator outputs (graph-generation stage) under tmp/<scale>/
        tmp_csvs = sorted(n for n in names if "/tmp/" in n and n.endswith(".csv"))
        print("\nraw simulator CSVs found under tmp/:")
        for n in tmp_csvs:
            print(" -", n)

        # Locate any pre-existing processed/model artifacts already bundled in the zip
        prebuilt = sorted(
            n
            for n in names
            if "/aml_detection/" in n
            and (n.endswith(".csv") or n.endswith(".pkl") or n.endswith(".html"))
        )
        print("\nNOTE: this zip also ships a pre-existing 'aml_detection/' "
              "sub-project with its own processed data, trained .pkl models, "
              "and metrics/report outputs already computed by someone else. "
              "These are NOT produced by this pipeline and are treated as "
              "reference-only, not as ground truth for our system:")
        for n in prebuilt:
            print(" -", n)

        for csv_name in tmp_csvs:
            with zf.open(csv_name) as f:
                df = pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"))
            print(f"\n--- {csv_name} ---")
            print("shape:", df.shape)
            print("columns:", list(df.columns))


def main() -> None:
    validate_indian_banking()
    validate_ulb()
    validate_amlsim()
    section("VALIDATION COMPLETE — no models trained, no raw files modified.")


if __name__ == "__main__":
    main()
