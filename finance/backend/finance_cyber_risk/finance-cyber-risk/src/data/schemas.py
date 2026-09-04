"""
Expected raw schemas, taken verbatim from the dataset inspection already
performed (see README.md section 1 and scripts/validate_datasets.py output).
Nothing here is guessed — every column name matches what was found on disk.
"""

INDIAN_BANKING_COLUMNS = [
    "transaction_id",
    "customer_id",
    "transaction_date",
    "transaction_time",
    "account_type",
    "transaction_type",
    "transaction_amount",
    "transaction_direction",
    "account_balance",
    "merchant_category",
    "state",
    "credit_score",
    "has_loan",
    "loan_type",
    "emi_amount",
    "transaction_status",
    "channel",
    "kyc_status",
    "is_fraud",
    "transaction_hour",
]
INDIAN_BANKING_TARGET = "is_fraud"
INDIAN_BANKING_ID_COLS = ["transaction_id", "customer_id"]

ULB_COLUMNS = [f"V{i}" for i in range(1, 29)]
ULB_COLUMNS = ["Time"] + ULB_COLUMNS + ["Amount", "Class"]
ULB_TARGET = "Class"

AMLSIM_ACCOUNTS_COLUMNS = [
    "ACCOUNT_ID",
    "CUSTOMER_ID",
    "INIT_BALANCE",
    "COUNTRY",
    "ACCOUNT_TYPE",
    "IS_SAR",
    "BANK_ID",
]
AMLSIM_TRANSACTIONS_COLUMNS = ["id", "src", "dst", "ttype"]
AMLSIM_ALERT_MEMBERS_COLUMNS = [
    "alertID",
    "reason",
    "accountID",
    "isMain",
    "isSAR",
    "modelID",
    "minAmount",
    "maxAmount",
    "startStep",
    "endStep",
    "scheduleID",
    "bankID",
]
AMLSIM_NORMAL_MODELS_COLUMNS = [
    "modelID",
    "type",
    "accountID",
    "isMain",
    "isSAR",
    "scheduleID",
]
AMLSIM_TARGET = "IS_SAR"  # account-level label, lives in accounts.csv


class SchemaValidationError(ValueError):
    pass


def validate_columns(df_columns, expected_columns, dataset_name: str) -> None:
    df_cols = list(df_columns)
    missing = [c for c in expected_columns if c not in df_cols]
    extra = [c for c in df_cols if c not in expected_columns]
    if missing:
        raise SchemaValidationError(
            f"[{dataset_name}] missing expected column(s): {missing}. "
            f"Found columns: {df_cols}"
        )
    if extra:
        # Not fatal — the raw file grew/shrank vs. what we inspected — but
        # surfaced loudly so nobody silently trains on a changed schema.
        print(
            f"[{dataset_name}] WARNING: unexpected extra column(s) found "
            f"that were not in the original inspection: {extra}"
        )
