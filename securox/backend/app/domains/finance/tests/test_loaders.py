import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import pytest

from src.data.amlsim_loader import load_amlsim
from src.data.indian_banking_loader import load_indian_banking
from src.data.schemas import SchemaValidationError, validate_columns
from src.data.ulb_loader import load_ulb


def test_indian_banking_loader_shapes_and_split():
    data = load_indian_banking()
    assert data.full.shape[0] == data.ids.shape[0] == data.target.shape[0]
    assert "is_fraud" not in data.features.columns
    assert "transaction_id" not in data.features.columns
    assert "customer_id" not in data.features.columns
    assert set(data.target.unique()).issubset({0, 1})


def test_indian_banking_no_duplicate_ids():
    data = load_indian_banking()
    assert data.ids["transaction_id"].duplicated().sum() == 0


def test_ulb_loader_shapes():
    data = load_ulb()
    assert data.features.shape[0] == data.target.shape[0]
    assert "Class" not in data.features.columns
    assert set(data.target.unique()).issubset({0, 1})
    assert data.features.isna().sum().sum() == 0


def test_amlsim_loader_relationships():
    data = load_amlsim()
    assert set(data.account_labels.columns) == {"ACCOUNT_ID", "is_sar"}
    assert data.account_labels["is_sar"].dtype == bool
    # every transaction endpoint should resolve mostly to known accounts
    known = set(data.accounts["ACCOUNT_ID"])
    src_known_ratio = data.transactions["src"].isin(known).mean()
    dst_known_ratio = data.transactions["dst"].isin(known).mean()
    assert src_known_ratio > 0.9
    assert dst_known_ratio > 0.9


def test_schema_validation_raises_on_missing_column():
    df = pd.DataFrame({"a": [1], "b": [2]})
    with pytest.raises(SchemaValidationError):
        validate_columns(df.columns, ["a", "b", "c"], "test")


def test_schema_validation_passes_on_exact_match():
    df = pd.DataFrame({"a": [1], "b": [2]})
    validate_columns(df.columns, ["a", "b"], "test")  # should not raise
