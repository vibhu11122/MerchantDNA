"""Build the feature store: `python -m merchantdna.features.build`.

Outputs (in artifacts/):
  features_baseline.parquet   history window (first part of the period)
  features_current.parquet    last 30 days, as of the scoring date, + peer z + history deltas
  features_snapshots.parquet  same as current, every 7 days (for trajectories and lead time)
  daily_counts.parquet        merchant x day counts and GMV (for the volume model and charts)
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from merchantdna.features import columns as C
from merchantdna.features.amount import amount_features, amount_histogram
from merchantdna.features.events import event_features
from merchantdna.features.payer import payer_city_counts, payer_features
from merchantdna.features.peer import cohort_key, cohort_stats, peer_z
from merchantdna.features.settlement import settlement_features
from merchantdna.features.volume_time import burst_features, time_features, volume_features
from merchantdna.features.windows import (FeatureContext, build_context, load_transactions,
                                          snapshot_days, window)
from merchantdna.utils.config import load_config
from merchantdna.utils.io import read_table, save_artifact, write_table
from merchantdna.utils.logging import Timer, get_logger

log = get_logger("features")


def baseline_days(cfg: dict[str, Any], n_days: int) -> int:
    """Length of the history window (days 0 .. baseline_days-1)."""
    return int(cfg["sim"]["baseline_frac"] * n_days)


def window_features(tx: pd.DataFrame, settle: pd.DataFrame, ctx: FeatureContext, end_day: int,
                    length: int, first_seen: pd.Series, roaming: pd.Series | None = None) -> pd.DataFrame:
    """All raw feature families for one window ending on `end_day` (inclusive).

    `roaming` (payer -> number of cities) defaults to this window's own population counts;
    single-merchant re-scoring passes the saved population counts instead.
    """
    w = window(tx, end_day, length)
    roaming = payer_city_counts(w) if roaming is None else roaming
    start_ts = ctx.calendar["date"].iloc[max(end_day - length + 1, 0)]
    s = settle[(settle["date"] >= start_ts) & (settle["date"] <= ctx.calendar["date"].iloc[end_day])]
    parts = [
        volume_features(w, ctx, end_day),
        time_features(w, ctx),
        burst_features(w, ctx),
        amount_features(w, ctx),
        payer_features(w, ctx, first_seen, start_ts, roaming),
        event_features(w, ctx),
        settlement_features(w, s, ctx),
        amount_histogram(w, ctx).add_prefix("a").rename(columns=lambda c: f"a{int(c[1:]):02d}"),
    ]
    feat = pd.concat(parts, axis=1).reindex(ctx.merchants["merchant_id"])
    feat.index.name = "merchant_id"
    return feat


def fill_missing(feat: pd.DataFrame) -> pd.DataFrame:
    """Merchants with no txns in a window get zeros for counts and cohort-neutral NaN elsewhere."""
    feat = feat.copy()
    for c in ["cnt_long", "gmv_long", "cnt_short", "gmv_short", "active_days"]:
        feat[c] = feat[c].fillna(0)
    return feat.fillna(feat.median(numeric_only=True))


def add_relative_views(feat: pd.DataFrame, base: pd.DataFrame, ctx: FeatureContext, length: int,
                       base_len: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add own-history ratio/deltas and peer z-scores. Returns (features, cohort stats)."""
    feat = feat.copy()
    base = base.reindex(feat.index)
    has_hist = base["active_days"] >= ctx.cfg["features"]["min_history_days"]
    base_rate = base["cnt_long"] / base_len
    ratio = (feat["cnt_long"] / length) / base_rate.clip(lower=0.5)
    feat["vol_ratio_hist"] = ratio.where(has_hist, ratio[has_hist].median())   # cold start: neutral
    for c in C.HISTORY_DELTA:
        feat[f"d_{c}"] = (feat[c] - base[c]).where(has_hist, 0.0)
    feat["has_history"] = has_hist.astype(int)
    cohorts = cohort_key(ctx.merchants.set_index("merchant_id"))
    stats = cohort_stats(feat, cohorts, C.PEER_Z)
    feat = pd.concat([feat, peer_z(feat, cohorts, stats, C.PEER_Z)], axis=1)
    return feat, stats


def daily_counts(tx: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Full merchant x day grid of txn counts and GMV (zeros included)."""
    g = tx.groupby(["merchant_id", "day_idx"], observed=False).agg(
        cnt=("amount", "size"), gmv=("amount", "sum")).reset_index()
    g["merchant_id"] = g["merchant_id"].astype(str)
    return g.merge(ctx.calendar[["day_idx", "date"]], on="day_idx")


def hour_day_cube(tx: pd.DataFrame, ctx: FeatureContext) -> dict[str, Any]:
    """[merchant, day, hour] txn counts so the dashboard never scans raw transactions."""
    ids = ctx.merchants["merchant_id"].tolist()
    n_days = len(ctx.calendar)
    g = tx.groupby(["merchant_id", "day_idx", "hour"], observed=False).size()
    cube = g.reindex(pd.MultiIndex.from_product([ids, range(n_days), range(24)]), fill_value=0)
    return {"ids": ids, "counts": cube.to_numpy().reshape(len(ids), n_days, 24).astype(np.uint16)}


def main() -> None:
    """Compute and save all feature tables."""
    cfg = load_config()
    ctx = build_context(cfg)
    with Timer(log, "load transactions"):
        tx = load_transactions(ctx)
        settle = read_table("settlements")
    n_days = len(ctx.calendar)
    b_len = baseline_days(cfg, n_days)
    length = cfg["features"]["window_long"]
    with Timer(log, "first-seen index"):
        first_seen = tx.groupby(["merchant_id", "payer_id_hash"], observed=True)["timestamp"].min()

    with Timer(log, "baseline + current windows"):
        base = fill_missing(window_features(tx, settle, ctx, b_len - 1, b_len, first_seen))
        cur_raw = fill_missing(window_features(tx, settle, ctx, n_days - 1, length, first_seen))
        cur, stats = add_relative_views(cur_raw, base, ctx, length, b_len)

    snaps = []
    with Timer(log, "weekly snapshots"):
        for d in snapshot_days(n_days, cfg["features"]["snapshot_every"], first=length - 1):
            f = fill_missing(window_features(tx, settle, ctx, d, length, first_seen))
            f, _ = add_relative_views(f, base, ctx, length, b_len)
            snaps.append(f.assign(as_of_day=d, as_of_date=ctx.calendar["date"].iloc[d]))

    last = window(tx, n_days - 1, length)
    write_table(base.reset_index(), "features_baseline", "artifacts")
    write_table(cur.reset_index(), "features_current", "artifacts")
    write_table(pd.concat(snaps).reset_index(), "features_snapshots", "artifacts")
    write_table(daily_counts(tx, ctx), "daily_counts", "artifacts")
    save_artifact(stats, "cohort_stats")
    save_artifact(hour_day_cube(tx, ctx), "hour_day_counts")
    save_artifact(payer_city_counts(last), "payer_roaming_current")
    log.info("features: %d merchants x %d columns; %d snapshots", len(cur), cur.shape[1], len(snaps))
    assert not (set(cur.columns) & C.LABEL_LIKE), "label leaked into features"


if __name__ == "__main__":
    main()
