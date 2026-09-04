import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from src.data.amlsim_loader import load_amlsim
from src.features.amlsim_features import (
    AMLSIM_FEATURE_COLUMNS,
    AMLSIM_METADATA_COLUMNS,
    engineer_amlsim_account_features,
)


@pytest.fixture(scope="module")
def amlsim_data():
    return load_amlsim()


def test_amlsim_validation_report_present_and_consistent(amlsim_data):
    report = amlsim_data.validation_report
    assert report["n_accounts"] == len(amlsim_data.accounts)
    assert report["n_transactions"] == len(amlsim_data.transactions)
    assert report["n_orphan_src_accounts"] >= 0
    assert report["n_orphan_dst_accounts"] >= 0
    assert report["n_duplicate_edge_rows"] >= 0


def test_amlsim_account_typology_is_metadata_only(amlsim_data):
    typ = amlsim_data.account_typology
    assert set(typ.columns) == {"ACCOUNT_ID", "alert_reason"}
    # every typology row's account must actually exist in accounts.csv
    assert set(typ["ACCOUNT_ID"]).issubset(set(amlsim_data.accounts["ACCOUNT_ID"]))


def test_amlsim_account_labels_match_accounts_table(amlsim_data):
    merged = amlsim_data.accounts.merge(
        amlsim_data.account_labels, on="ACCOUNT_ID", suffixes=("", "_dup")
    )
    assert (merged["IS_SAR"] == merged["is_sar"]).all()


def test_orphan_edge_detection_on_synthetic_data():
    accounts = pd.DataFrame(
        {
            "ACCOUNT_ID": [1, 2, 3],
            "CUSTOMER_ID": ["C1", "C2", "C3"],
            "INIT_BALANCE": [100.0, 200.0, 300.0],
            "COUNTRY": ["US", "US", "US"],
            "ACCOUNT_TYPE": ["I", "I", "I"],
            "IS_SAR": ["false", "false", "true"],
            "BANK_ID": ["bank"] * 3,
        }
    )
    transactions = pd.DataFrame(
        {"id": [0, 1], "src": [1, 999], "dst": [2, 3], "ttype": ["TRANSFER", "TRANSFER"]}
    )
    known = set(accounts["ACCOUNT_ID"])
    orphan_src = set(transactions["src"]) - known
    assert orphan_src == {999}


def test_duplicate_relationship_detection_on_synthetic_data():
    transactions = pd.DataFrame(
        {
            "id": [0, 1, 2],
            "src": [1, 1, 2],
            "dst": [2, 2, 3],
            "ttype": ["TRANSFER", "TRANSFER", "TRANSFER"],
        }
    )
    dup_mask = transactions.duplicated(subset=["src", "dst", "ttype"], keep=False)
    assert dup_mask.sum() == 2  # rows 0 and 1 share the same (src,dst,ttype)


def test_aml_feature_columns_exclude_leakage_fields(amlsim_data):
    features = engineer_amlsim_account_features(
        amlsim_data.accounts, amlsim_data.transactions, amlsim_data.alert_members
    )
    for leaky_col in ["is_alert_member", "alert_reason", "is_sar"]:
        assert leaky_col not in AMLSIM_FEATURE_COLUMNS
        assert leaky_col in AMLSIM_METADATA_COLUMNS
        assert leaky_col in features.columns  # present for reference, not as a feature
    assert set(AMLSIM_FEATURE_COLUMNS).isdisjoint(set(AMLSIM_METADATA_COLUMNS))
