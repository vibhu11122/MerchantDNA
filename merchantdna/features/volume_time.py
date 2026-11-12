"""Volume, time-of-day and burstiness features."""
from __future__ import annotations

import numpy as np
import pandas as pd

from merchantdna.features.windows import FeatureContext


def volume_features(w: pd.DataFrame, ctx: FeatureContext, end_day: int) -> pd.DataFrame:
    """Txn counts / GMV over the long and short window, growth and daily dispersion."""
    long_n, short_n = ctx.cfg["features"]["window_long"], ctx.cfg["features"]["window_short"]
    short = w[w["day_idx"] > end_day - short_n]
    g = w.groupby("merchant_id", observed=False)
    out = pd.DataFrame({
        "cnt_long": g.size(),
        "gmv_long": g["amount"].sum(),
        "cnt_short": short.groupby("merchant_id", observed=False).size(),
        "gmv_short": short.groupby("merchant_id", observed=False)["amount"].sum(),
        "active_days": g["day_idx"].nunique(),
    })
    out["growth_short_vs_long"] = (out["cnt_short"] / short_n) / (out["cnt_long"] / long_n).clip(lower=1e-9)
    daily = w.groupby(["merchant_id", "day_idx"], observed=False).size().unstack(fill_value=0)
    out["daily_fano"] = daily.var(axis=1) / daily.mean(axis=1).clip(lower=1e-9)
    return out


def time_features(w: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """24-bin hourly profile, night/evening/weekend shares."""
    night = ctx.cfg["features"]["night_hours"]
    evening = ctx.cfg["features"]["evening_hours"]
    hours = w.groupby(["merchant_id", "hour"], observed=False).size().unstack(fill_value=0)
    hours = hours.reindex(columns=range(24), fill_value=0)
    prof = hours.div(hours.sum(axis=1).clip(lower=1), axis=0)
    prof.columns = [f"h{h:02d}" for h in range(24)]
    out = prof.copy()
    out["night_share"] = prof.iloc[:, night[0]:night[1]].sum(axis=1)
    out["evening_share"] = prof.iloc[:, evening[0]:evening[1] + 1].sum(axis=1)
    weekend = w["date"].dt.dayofweek >= 5
    out["weekend_share"] = weekend.groupby(w["merchant_id"], observed=False).mean()
    return out


def burst_features(w: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Within-hour burstiness: Fano factor of 10-minute bucket counts inside each active hour.

    A Poisson stream scores ~1 whatever its volume, so a festival rush stays ~1
    while bets landing right after wickets push it well above 1.
    """
    size = ctx.cfg["features"]["burst_bucket_minutes"]
    n_buckets = 60 // size
    sub = (w["minute"] % 60) // size
    cell = w.assign(sub=sub).groupby(["merchant_id", "day_idx", "hour", "sub"], observed=True).size()
    cell = cell.to_frame("n").assign(sq=lambda d: d["n"] ** 2)
    per_hour = cell.groupby(level=[0, 1, 2], observed=True)[["n", "sq"]].sum()
    mean = per_hour["n"] / n_buckets
    var = per_hour["sq"] / n_buckets - mean ** 2
    fano = (var / mean).rename("fano")
    weighted = (fano * per_hour["n"]).groupby(level=0, observed=True).sum() \
        / per_hour["n"].groupby(level=0, observed=True).sum()
    return pd.DataFrame({"burst_index": weighted})
