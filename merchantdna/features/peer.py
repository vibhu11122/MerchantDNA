"""Peer-relative view: robust z-score against the declared-category x city-tier cohort."""
from __future__ import annotations

import numpy as np
import pandas as pd

MAD_TO_SD = 1.4826   # scales the median absolute deviation to a standard deviation


def cohort_key(merchants: pd.DataFrame) -> pd.Series:
    """'bakery|1' style key per merchant."""
    return merchants["declared_category"] + "|" + merchants["tier"].astype(str)


def cohort_stats(feat: pd.DataFrame, cohorts: pd.Series, cols: list[str]) -> pd.DataFrame:
    """Median and scaled MAD of each feature inside each cohort (same window)."""
    df = feat[cols].assign(cohort=cohorts.reindex(feat.index).to_numpy())
    med = df.groupby("cohort").median()
    mad = df.groupby("cohort").agg(lambda s: MAD_TO_SD * (s - s.median()).abs().median())
    global_sd = feat[cols].std()
    mad = mad.clip(lower=0.1 * global_sd + 1e-6, axis=1)   # avoid divide-by-~0 for flat features
    return pd.concat({"median": med, "mad": mad}, axis=1)


def peer_z(feat: pd.DataFrame, cohorts: pd.Series, stats: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """z_<col> = (x - cohort median) / cohort MAD, clipped to +/-10."""
    key = cohorts.reindex(feat.index).to_numpy()
    med = stats["median"].reindex(key)[cols].to_numpy()
    mad = stats["mad"].reindex(key)[cols].to_numpy()
    z = np.clip((feat[cols].to_numpy() - med) / mad, -10, 10)
    return pd.DataFrame(z, index=feat.index, columns=[f"z_{c}" for c in cols])
