"""Payer-side features: repeat behaviour, concentration and geography (the hard-to-fake side)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from merchantdna.features.windows import FeatureContext


def payer_city_counts(w: pd.DataFrame) -> pd.Series:
    """For every payer in the window: number of distinct merchant cities they paid in."""
    return w.groupby("payer_id_hash")["merchant_city"].nunique()


def payer_features(w: pd.DataFrame, ctx: FeatureContext, first_seen: pd.Series,
                   start_ts: pd.Timestamp, roaming: pd.Series) -> pd.DataFrame:
    """Repeat/new rates, HHI, non-local share, city entropy and multi-city (roaming) payer share.

    first_seen: (merchant_id, payer) -> first timestamp ever seen at that merchant (past only).
    roaming:    payer -> number of distinct merchant cities paid in this window.
    """
    pm = w.groupby(["merchant_id", "payer_id_hash"], observed=True).size().rename("n").reset_index()
    pm["repeat"] = pm["n"] >= 2
    fs = first_seen.reindex(pd.MultiIndex.from_frame(pm[["merchant_id", "payer_id_hash"]]))
    pm["is_new"] = fs.to_numpy() >= np.datetime64(start_ts)
    pm["roams"] = pm["payer_id_hash"].map(roaming).to_numpy() >= 3
    g = pm.groupby("merchant_id", observed=False)
    total = g["n"].sum().clip(lower=1)
    out = pd.DataFrame({
        "unique_payers": g.size(),
        "payers_per_txn": g.size() / total,
        "repeat_txn_share": pm[pm["repeat"]].groupby("merchant_id", observed=False)["n"].sum() / total,
        "new_payer_rate": g["is_new"].mean(),
        "payer_hhi": pm.assign(s2=pm["n"] ** 2).groupby("merchant_id", observed=False)["s2"].sum() / total ** 2,
        "multi_city_payer_share": g["roams"].mean(),
    })
    out["nonlocal_share"] = 1 - w.groupby("merchant_id", observed=False)["is_local"].mean()
    cities = w.groupby(["merchant_id", "payer_city"], observed=True).size().unstack(fill_value=0)
    p = cities.div(cities.sum(axis=1).clip(lower=1), axis=0).to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -np.nansum(np.where(p > 0, p * np.log2(p), 0.0), axis=1)
    out["payer_city_entropy"] = pd.Series(ent, index=cities.index)
    return out
