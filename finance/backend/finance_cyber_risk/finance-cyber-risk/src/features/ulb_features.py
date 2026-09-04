"""
Feature engineering for the ULB Credit Card Fraud dataset.

`Time` in this dataset is documented (by the original publisher) as seconds
elapsed since the first transaction in the dataset — it is NOT a wall-clock
timestamp. We only derive features that are valid under that definition:
a within-day cyclical hour and a day index (the dataset spans ~2 days).

V1-V28 are left completely untouched (no re-scaling, no re-PCA, no assumed
meaning). Amount gets a log1p transform to tame its heavy skew/outliers;
the log transform is reversible and does not use the label.
"""
import numpy as np
import pandas as pd

SECONDS_PER_DAY = 86400


def engineer_ulb_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    seconds_into_day = df["Time"] % SECONDS_PER_DAY
    hour_of_day = seconds_into_day / 3600.0

    df["time_day_index"] = (df["Time"] // SECONDS_PER_DAY).astype(int)
    df["time_hour_of_day"] = hour_of_day
    df["time_hour_sin"] = np.sin(2 * np.pi * hour_of_day / 24)
    df["time_hour_cos"] = np.cos(2 * np.pi * hour_of_day / 24)

    df["amount_log1p"] = np.log1p(df["Amount"])

    return df
