"""
Leakage-safe feature engineering for Indian Banking Transactions.

Hard rule enforced throughout: every "historical" / "rolling" / "baseline"
feature for a transaction is computed using ONLY transactions from the same
customer that happened strictly BEFORE it in time. This is done with
vectorized pandas groupby operations (cumsum/cumcount/shift/rolling) rather
than per-group Python loops, both for correctness-by-construction and so it
runs in reasonable time on 550k rows / ~80k customers.
"""
import numpy as np
import pandas as pd


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Combine transaction_date + transaction_time into one sortable datetime."""
    df = df.copy()
    df["transaction_datetime"] = pd.to_datetime(
        df["transaction_date"].astype(str) + " " + df["transaction_time"].astype(str),
        errors="raise",
    )
    return df


def add_time_of_day_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    hour = df["transaction_hour"]
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    def bucket(h):
        if 5 <= h < 12:
            return "morning"
        if 12 <= h < 17:
            return "afternoon"
        if 17 <= h < 21:
            return "evening"
        return "night"

    df["time_of_day_bucket"] = hour.apply(bucket)
    df["day_of_week"] = df["transaction_datetime"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    return df


def add_customer_history_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vectorized, past-only customer history features. `df` must already have
    `transaction_datetime`. Sorts by (customer_id, transaction_datetime) so
    every cumulative/shift operation walks forward in time per customer.
    """
    df = df.sort_values(["customer_id", "transaction_datetime"]).reset_index(drop=True)
    grp = df.groupby("customer_id", sort=False)

    amount = df["transaction_amount"]
    is_fraud = df["is_fraud"] if "is_fraud" in df.columns else pd.Series(0, index=df.index)

    # --- count of prior txns for this customer (0 for the first) ---
    n_so_far = grp.cumcount()
    df["cust_txn_count_so_far"] = n_so_far

    # --- velocity: seconds since this customer's previous transaction ---
    prev_dt = grp["transaction_datetime"].shift(1)
    df["seconds_since_prev_txn"] = (df["transaction_datetime"] - prev_dt).dt.total_seconds()
    df["seconds_since_prev_txn"] = df["seconds_since_prev_txn"].fillna(-1)

    # --- expanding mean/std/max of PAST amounts only, via cumulative sums ---
    # cumsum *including* current row, then subtract current row's own value
    # to get the sum/sumsq/count of everything strictly before it.
    cum_sum = grp["transaction_amount"].cumsum()
    cum_sumsq = (amount ** 2).groupby(df["customer_id"]).cumsum()

    past_sum = cum_sum - amount
    past_sumsq = cum_sumsq - amount ** 2
    n_safe = n_so_far.replace(0, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_so_far = past_sum / n_safe
        var_so_far = (past_sumsq / n_safe) - mean_so_far ** 2
    df["cust_amount_mean_so_far"] = mean_so_far
    df["cust_amount_std_so_far"] = np.sqrt(var_so_far.clip(lower=0))

    cum_max_incl = grp["transaction_amount"].cummax()
    past_max = cum_max_incl.groupby(df["customer_id"]).shift(1)
    df["cust_amount_max_so_far"] = past_max

    # --- rolling count / sum within trailing time windows, PAST-ONLY ---
    # shift(1) excludes the current transaction from its own window, then a
    # time-indexed rolling window (grouped) sums/counts the rest.
    amt_shifted = grp["transaction_amount"].shift(1)
    tmp = pd.DataFrame(
        {
            "customer_id": df["customer_id"].values,
            "transaction_datetime": df["transaction_datetime"].values,
            "amt_shifted": amt_shifted.values,
        }
    ).set_index("transaction_datetime")

    roll = tmp.groupby("customer_id")["amt_shifted"]
    count_24h = roll.rolling("1D", min_periods=0).count().reset_index(level=0, drop=True)
    sum_24h = roll.rolling("1D", min_periods=0).sum().reset_index(level=0, drop=True)
    count_7d = roll.rolling("7D", min_periods=0).count().reset_index(level=0, drop=True)

    df["cust_txn_count_past_24h"] = count_24h.to_numpy()
    df["cust_amount_sum_past_24h"] = np.nan_to_num(sum_24h.to_numpy(), nan=0.0)
    df["cust_txn_count_past_7d"] = count_7d.to_numpy()

    # --- amount deviation from customer's own past baseline ---
    baseline_mean = df["cust_amount_mean_so_far"]
    baseline_std = df["cust_amount_std_so_far"].replace(0, np.nan)
    df["amount_zscore_vs_history"] = ((amount - baseline_mean) / baseline_std).fillna(0)
    df["amount_ratio_vs_history_mean"] = (amount / baseline_mean.replace(0, np.nan)).fillna(1)

    # --- categorical behavior: prior count / share of this category value
    #     within this customer's history (vectorized via cumcount) ---
    for col, out_prefix in [
        ("channel", "cust_channel"),
        ("transaction_type", "cust_txn_type"),
        ("merchant_category", "cust_merchant_cat"),
    ]:
        prior_count = df.groupby(["customer_id", col], sort=False).cumcount()
        df[f"{out_prefix}_prior_count"] = prior_count
        df[f"{out_prefix}_prior_share"] = (prior_count / n_safe).fillna(0.0)

    # --- account balance behavior ---
    prev_balance = grp["account_balance"].shift(1)
    df["balance_change_vs_prev"] = (df["account_balance"] - prev_balance).fillna(0)
    df["amount_to_balance_ratio"] = (amount / df["account_balance"].replace(0, np.nan)).fillna(0)

    # --- historical fraud signal: PAST-only, via the same cumsum-minus-self trick ---
    fraud_cumsum_incl = is_fraud.groupby(df["customer_id"]).cumsum()
    past_fraud_count = fraud_cumsum_incl - is_fraud
    df["cust_past_fraud_count"] = past_fraud_count
    df["cust_past_fraud_rate"] = (past_fraud_count / n_safe).fillna(0)

    # fill remaining NaNs created intentionally for "no history yet" rows
    fill_zero_cols = [
        "cust_amount_mean_so_far",
        "cust_amount_std_so_far",
        "cust_amount_max_so_far",
    ]
    df[fill_zero_cols] = df[fill_zero_cols].fillna(0)

    return df


def engineer_indian_banking_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    raw_df: the *full* loaded Indian Banking dataframe (features + ids +
    is_fraud all together). is_fraud is used ONLY inside the past-only
    cumsum-minus-self construction of cust_past_fraud_count/rate above — the
    current row's own is_fraud value never contributes to its own features,
    which is verified by tests/test_leakage.py.
    """
    df = parse_datetime(raw_df)
    df = add_time_of_day_features(df)
    df = add_customer_history_features(df)
    return df
