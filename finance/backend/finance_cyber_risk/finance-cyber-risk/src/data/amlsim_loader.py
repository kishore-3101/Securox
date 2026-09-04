"""
Loader for the IBM AMLSim dataset.

We only ever read the *raw simulator output* (tmp/1K/*.csv) directly from
the untouched zip archive. The `aml_detection/` sub-project also bundled in
that zip (its processed features, trained .pkl models, and reports) is
reference material from a prior, separate effort and is deliberately never
opened by this loader — see AMLSIM_ZIP_REFERENCE_PREFIX in
src/config/paths.py, which exists only so we can *name* that we're avoiding
it, not to load it.

This loader preserves the account <-> transaction <-> alert <-> label
relationships as separate, joinable tables rather than flattening them
prematurely.
"""
import io
import zipfile
from dataclasses import dataclass

import pandas as pd

from src.config.paths import (
    AMLSIM_RAW_ZIP,
    AMLSIM_ZIP_ACCOUNTS,
    AMLSIM_ZIP_ALERT_MEMBERS,
    AMLSIM_ZIP_NORMAL_MODELS,
    AMLSIM_ZIP_REFERENCE_PREFIX,
    AMLSIM_ZIP_TRANSACTIONS,
)
from src.data.schemas import (
    AMLSIM_ACCOUNTS_COLUMNS,
    AMLSIM_ALERT_MEMBERS_COLUMNS,
    AMLSIM_NORMAL_MODELS_COLUMNS,
    AMLSIM_TRANSACTIONS_COLUMNS,
    validate_columns,
)


@dataclass
class AMLSimData:
    accounts: pd.DataFrame          # one row per account, includes IS_SAR label
    transactions: pd.DataFrame      # one row per edge: id, src, dst, ttype
    alert_members: pd.DataFrame     # accounts implicated in a specific alert pattern
    normal_models: pd.DataFrame     # accounts assigned to normal (non-alert) behavior models
    account_labels: pd.DataFrame    # ACCOUNT_ID, is_sar (bool) — label table, kept separate
    account_typology: pd.DataFrame  # ACCOUNT_ID, alert_reason (typology name or None) — metadata only
    validation_report: dict         # orphan-edge / duplicate-relationship counts found at load time


def _read_csv_from_zip(zf: zipfile.ZipFile, member: str) -> pd.DataFrame:
    with zf.open(member) as f:
        return pd.read_csv(io.TextIOWrapper(f, encoding="utf-8"))


def load_amlsim(zip_path=AMLSIM_RAW_ZIP) -> AMLSimData:
    if not zip_path.exists():
        raise FileNotFoundError(
            f"AMLSim raw zip not found at {zip_path}. Raw data must not be "
            "moved from data/raw/amlsim/."
        )

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        for required in [
            AMLSIM_ZIP_ACCOUNTS,
            AMLSIM_ZIP_TRANSACTIONS,
            AMLSIM_ZIP_ALERT_MEMBERS,
            AMLSIM_ZIP_NORMAL_MODELS,
        ]:
            if required not in names:
                raise RuntimeError(
                    f"Expected AMLSim raw simulator file not found inside "
                    f"zip: {required}"
                )

        accounts = _read_csv_from_zip(zf, AMLSIM_ZIP_ACCOUNTS)
        transactions = _read_csv_from_zip(zf, AMLSIM_ZIP_TRANSACTIONS)
        alert_members = _read_csv_from_zip(zf, AMLSIM_ZIP_ALERT_MEMBERS)
        normal_models = _read_csv_from_zip(zf, AMLSIM_ZIP_NORMAL_MODELS)

        reference_files = [n for n in names if n.startswith(AMLSIM_ZIP_REFERENCE_PREFIX)]

    validate_columns(accounts.columns, AMLSIM_ACCOUNTS_COLUMNS, "AMLSim accounts")
    validate_columns(transactions.columns, AMLSIM_TRANSACTIONS_COLUMNS, "AMLSim transactions")
    validate_columns(alert_members.columns, AMLSIM_ALERT_MEMBERS_COLUMNS, "AMLSim alert_members")
    validate_columns(normal_models.columns, AMLSIM_NORMAL_MODELS_COLUMNS, "AMLSim normal_models")

    print(
        f"[AMLSim loader] Ignoring {len(reference_files)} file(s) under "
        f"'{AMLSIM_ZIP_REFERENCE_PREFIX}' (pre-existing reference "
        "sub-project — not used as ground truth or reused as features)."
    )

    accounts = accounts.copy()
    accounts["ACCOUNT_ID"] = accounts["ACCOUNT_ID"].astype(int)
    # IS_SAR arrives as the strings "true"/"false"
    accounts["IS_SAR"] = (
        accounts["IS_SAR"].astype(str).str.strip().str.lower().map({"true": True, "false": False})
    )
    if accounts["IS_SAR"].isna().any():
        raise RuntimeError(
            "AMLSim accounts.IS_SAR contained a value other than true/false "
            "— refusing to guess its meaning."
        )

    transactions = transactions.copy()
    for col in ["id", "src", "dst"]:
        transactions[col] = transactions[col].astype(int)

    account_labels = accounts[["ACCOUNT_ID", "IS_SAR"]].rename(
        columns={"IS_SAR": "is_sar"}
    )

    # Sanity check the relationships actually join (no orphan edges).
    known_accounts = set(accounts["ACCOUNT_ID"])
    orphan_src = set(transactions["src"]) - known_accounts
    orphan_dst = set(transactions["dst"]) - known_accounts
    if orphan_src or orphan_dst:
        print(
            "[AMLSim loader] WARNING: transactions reference account IDs "
            f"not present in accounts.csv (src orphans={len(orphan_src)}, "
            f"dst orphans={len(orphan_dst)}). These will be handled at the "
            "feature-engineering stage, not silently dropped here."
        )

    # Duplicate relationships: the same (src, dst, ttype) edge appearing more
    # than once. Not necessarily an error (repeat transfers between the same
    # pair are plausible) but surfaced so it's a known, not hidden, property
    # of the data.
    dup_edges_mask = transactions.duplicated(subset=["src", "dst", "ttype"], keep=False)
    n_duplicate_edge_rows = int(dup_edges_mask.sum())
    n_duplicate_edge_groups = int(
        transactions.loc[dup_edges_mask, ["src", "dst", "ttype"]].drop_duplicates().shape[0]
    )

    # Duplicate alert_members rows (same account flagged twice in the same alert).
    n_duplicate_alert_rows = int(
        alert_members.duplicated(subset=["alertID", "accountID"]).sum()
    )

    validation_report = {
        "n_accounts": int(len(accounts)),
        "n_transactions": int(len(transactions)),
        "n_orphan_src_accounts": len(orphan_src),
        "n_orphan_dst_accounts": len(orphan_dst),
        "n_duplicate_edge_rows": n_duplicate_edge_rows,
        "n_duplicate_edge_groups": n_duplicate_edge_groups,
        "n_duplicate_alert_member_rows": n_duplicate_alert_rows,
    }
    if n_duplicate_edge_rows:
        print(
            f"[AMLSim loader] NOTE: found {n_duplicate_edge_rows} transaction "
            f"rows sharing an identical (src, dst, ttype) triple across "
            f"{n_duplicate_edge_groups} distinct pairs — kept as separate "
            "graph edges (a MultiDiGraph), not deduplicated, since each row "
            "is a real distinct transaction id."
        )

    # Account-level typology metadata (which alert pattern, if any, an
    # account was assigned to). Metadata only — see leakage note in
    # src/features/amlsim_features.py; never used as a model feature.
    account_typology = (
        alert_members.groupby("accountID")["reason"]
        .agg(lambda x: x.mode().iat[0] if not x.mode().empty else None)
        .rename("alert_reason")
        .reset_index()
        .rename(columns={"accountID": "ACCOUNT_ID"})
    )

    return AMLSimData(
        accounts=accounts,
        transactions=transactions,
        alert_members=alert_members,
        normal_models=normal_models,
        account_labels=account_labels,
        account_typology=account_typology,
        validation_report=validation_report,
    )
