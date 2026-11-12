"""Re-score ONE merchant after editing its transactions (Model Lab "break it" controls).

Uses the population reference statistics saved at training time, so the edited
merchant is judged against the same peers, models and thresholds as everyone else.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from merchantdna.decision.ladder import choose_rungs, tier
from merchantdna.features import columns as C
from merchantdna.features.build import baseline_days, window_features
from merchantdna.features.peer import peer_z
from merchantdna.features.windows import FeatureContext
from merchantdna.models import fusion as F
from merchantdna.models.innocence import verdict
from merchantdna.models.scoring import Bundle, components, risk


def enrich(tx: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Add the same helper columns `features.windows.load_transactions` adds."""
    tx = tx.copy()
    start = ctx.calendar["date"].min()
    tx["date"] = tx["timestamp"].dt.normalize()
    tx["day_idx"] = (tx["date"] - start).dt.days.astype("int16")
    tx["hour"] = tx["timestamp"].dt.hour.astype("int8")
    tx["minute"] = (tx["hour"].astype("int16") * 60 + tx["timestamp"].dt.minute).astype("int16")
    city = ctx.merchants.set_index("merchant_id")["city"]
    tx["merchant_city"] = tx["merchant_id"].astype(str).map(city).astype("category")
    tx["is_local"] = tx["payer_city"].astype(str).to_numpy() == tx["merchant_city"].astype(str).to_numpy()
    return tx


def merchant_features(b: Bundle, ctx: FeatureContext, tx: pd.DataFrame, settle: pd.DataFrame,
                      cohort_stats: pd.DataFrame, roaming: pd.Series, pop: pd.DataFrame,
                      mid: str) -> pd.DataFrame:
    """Current-window features for one merchant, made relative with POPULATION statistics."""
    cfg = b.cfg
    n_days = len(ctx.calendar)
    length = cfg["features"]["window_long"]
    first_seen = tx.groupby(["merchant_id", "payer_id_hash"], observed=True)["timestamp"].min()
    payers = tx["payer_id_hash"].unique()
    roam = roaming.reindex(payers).fillna(1)               # unseen (new) payers: one city only
    f = window_features(tx, settle, ctx, n_days - 1, length, first_seen, roam).loc[[mid]]
    f = f.fillna(pop.median(numeric_only=True))
    base = b.base.loc[[mid]]
    has_hist = base["active_days"] >= cfg["features"]["min_history_days"]
    ratio = (f["cnt_long"] / length) / (base["cnt_long"] / baseline_days(cfg, n_days)).clip(lower=0.5)
    f["vol_ratio_hist"] = ratio.where(has_hist, pop["vol_ratio_hist"].median())
    for c in C.HISTORY_DELTA:
        f[f"d_{c}"] = (f[c] - base[c]).where(has_hist, 0.0)
    f["has_history"] = has_hist.astype(int)
    return pd.concat([f, peer_z(f, b.cohorts, cohort_stats, C.PEER_Z)], axis=1)


def rescore(b: Bundle, ctx: FeatureContext, tx: pd.DataFrame, settle: pd.DataFrame,
            daily: pd.DataFrame, cohort_stats: pd.DataFrame, roaming: pd.Series,
            pop: pd.DataFrame, mid: str) -> dict[str, Any]:
    """Full pipeline for one (edited) merchant -> score, tier, action, drivers, innocence verdict."""
    tx = enrich(tx, ctx)
    f = merchant_features(b, ctx, tx, settle, cohort_stats, roaming, pop, mid)
    d = tx.groupby("day_idx").size().reindex(range(len(ctx.calendar)), fill_value=0)
    new_daily = daily[daily["merchant_id"] != mid]
    mine = daily[daily["merchant_id"] == mid].set_index("day_idx").assign(cnt=d).reset_index()
    c = components(b, f, pd.concat([new_daily, mine]), len(ctx.calendar) - 1, refs=b.refs)
    score = float(risk(b, c["x"]).iloc[0])
    inn = verdict(c["volume"].loc[mid], c["composition"].loc[mid], b.declared[mid])
    return {"risk_score": score, "tier": str(tier(score, b.cfg)),
            "rung": choose_rungs(pd.Series([score / 100], index=[mid]), b.cfg)["rung"].iloc[0],
            "drivers": F.explain(b.fusion, c["x"])[mid], "innocence": inn,
            "features": f.iloc[0], "x": c["x"].iloc[0]}


# ------------------------------------------------------------------ edits for the live demo
def festival_shape(cal: pd.DataFrame, peak_factor: float, tx: pd.DataFrame) -> dict[pd.Timestamp, float]:
    """Per-day multipliers that lift each Diwali day to `peak_factor` x the merchant's USUAL
    day on peak days (40% of the extra on the other window days), like the simulator."""
    per_day = tx.groupby(tx["timestamp"].dt.normalize()).size()
    usual = per_day[~per_day.index.isin(cal.loc[cal["is_diwali_window"], "date"])].median()
    shape = {}
    for _, r in cal[cal["is_diwali_window"]].iterrows():
        target = usual * (peak_factor if r["is_diwali_peak"] else 1 + 0.4 * (peak_factor - 1))
        shape[r["date"]] = max(1.0, target / max(per_day.get(r["date"], 1), 1))
    return shape


def week_shape(cal: pd.DataFrame, start_idx: int, factor: float) -> dict[pd.Timestamp, float]:
    """The same multiplier on 7 ordinary days (a spike with no festival behind it)."""
    return {d: factor for d in cal["date"].iloc[start_idx:start_idx + 7]}


def inject_spike(tx: pd.DataFrame, factors: dict[pd.Timestamp, float],
                 rng: np.random.Generator) -> pd.DataFrame:
    """Multiply volume per day with the SAME composition: amounts, hours and payer cities
    are resampled from that day's own transactions; payers are new (fresh customers)."""
    extra = []
    for day, factor in factors.items():
        today = tx[tx["timestamp"].dt.normalize() == day]
        n = int(len(today) * (factor - 1))
        if n <= 0 or today.empty:
            continue
        s = today.sample(n, replace=True, random_state=int(rng.integers(1 << 31))).copy()
        s["timestamp"] = s["timestamp"] + pd.to_timedelta(rng.integers(-600, 600, n), unit="s")
        s["timestamp"] = s["timestamp"].clip(day, day + pd.Timedelta(hours=23, minutes=59))
        s["payer_id_hash"] = rng.integers(-(1 << 62), 1 << 62, n)
        extra.append(s)
    return pd.concat([tx, *extra], ignore_index=True) if extra else tx


def make_mimic(tx: pd.DataFrame, hourly: list[float], from_day: pd.Timestamp, jitter: float,
               rng: np.random.Generator) -> pd.DataFrame:
    """Adversarial edit: copy a bakery's hourly profile and jitter round bet amounts."""
    tx = tx.copy()
    rows = tx["timestamp"] >= from_day
    n = int(rows.sum())
    hours = rng.choice(24, size=n, p=np.asarray(hourly) / np.sum(hourly))
    day = tx.loc[rows, "timestamp"].dt.normalize()
    tx.loc[rows, "timestamp"] = day + pd.to_timedelta(hours * 3600 + rng.integers(0, 3600, n), unit="s")
    amt = tx.loc[rows, "amount"].to_numpy()
    on_point = np.isin(amt, [499, 999, 1999])
    amt[on_point] = np.round(amt[on_point] * (1 + rng.uniform(-jitter, jitter, on_point.sum())))
    tx.loc[rows, "amount"] = amt.astype("float32")
    return tx
