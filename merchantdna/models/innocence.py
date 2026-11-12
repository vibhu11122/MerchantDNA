"""Innocence Engine: try to explain a deviation with legitimate reasons before flagging.

(a) Expected-volume model. Expected daily txns = own usual rate x how much the merchant's
    peers (same category, same city tier) moved that day. The band around it combines
    the spread across peers that day (some bakeries surge 10x at Diwali) with the
    merchant's own day-to-day noise (LightGBM quantile regression, conformally calibrated).
(b) Composition tests. Jensen-Shannon distance of the hourly profile, amount mix and payer
    geography against the merchant's own history and against peers in the same window.

Core rule: the engine may discount VOLUME-driven risk only. It never discounts a
composition shift (price points, night share, payer geography, network links).
"""
from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd

from merchantdna.features.columns import AMOUNT_HIST, HOURLY

MODEL_FEATURES = ["cat_code", "is_weekend", "is_other_festival", "is_diwali_window",
                  "is_diwali_peak", "ipl_match", "log_ref", "day_of_month"]
CAL_COLS = ["is_weekend", "is_other_festival", "is_diwali_window", "is_diwali_peak", "ipl_match"]


# ------------------------------------------------------------------ (a) volume
def reference_rates(daily: pd.DataFrame, cal: pd.DataFrame, end_day: int) -> pd.DataFrame:
    """Own usual daily volume from days before `end_day` (Diwali excluded, pre-onboarding excluded)."""
    first = daily[daily["cnt"] > 0].groupby("merchant_id")["day_idx"].min()
    d = daily[daily["day_idx"] < end_day]
    d = d[d["day_idx"] >= d["merchant_id"].map(first).fillna(np.inf)]
    d = d[~d["day_idx"].map(cal.set_index("day_idx")["is_diwali_window"])]
    g = d.groupby("merchant_id")["cnt"]
    return pd.DataFrame({"ref_rate": g.mean(), "ref_days": g.size(), "first_day": first}).fillna(
        {"ref_rate": 0.0, "ref_days": 0})


def peer_uplift(daily: pd.DataFrame, ref: pd.DataFrame, cohorts: pd.Series,
                band: list[float], min_days: int) -> pd.DataFrame:
    """Per cohort and day: low / median / high quantile of peers' volume vs their own usual."""
    d = daily.join(ref, on="merchant_id")
    d = d[(d["ref_days"] >= min_days) & (d["ref_rate"] > 0)]
    if d.empty:                                         # no merchant has enough history yet
        idx = pd.MultiIndex.from_arrays([[], []], names=["cohort", "day_idx"])
        return pd.DataFrame(columns=["p_lo", "p50", "p_hi"], index=idx, dtype=float)
    d = d.assign(uplift=d["cnt"] / d["ref_rate"], cohort=d["merchant_id"].map(cohorts))
    q = d.groupby(["cohort", "day_idx"])["uplift"].quantile([band[0], 0.5, band[1]]).unstack()
    q.columns = ["p_lo", "p50", "p_hi"]
    return q.clip(lower=0.05)


def _design(rows: pd.DataFrame, ref: pd.DataFrame, peers: pd.DataFrame, cal: pd.DataFrame,
            cohorts: pd.Series, cat_codes: dict[str, int]) -> pd.DataFrame:
    """Model inputs + the multiplicative baseline for merchant-day rows."""
    d = rows.join(ref, on="merchant_id")
    d["cohort"] = d["merchant_id"].map(cohorts)
    d = d.join(peers, on=["cohort", "day_idx"]).fillna({"p_lo": 1.0, "p50": 1.0, "p_hi": 1.0})
    c = cal.set_index("day_idx")
    for col in CAL_COLS:
        d[col] = d["day_idx"].map(c[col]).astype(int)
    d["day_of_month"] = d["day_idx"].map(c["date"].dt.day)
    d["cat_code"] = d["cohort"].str.split("|").str[0].map(cat_codes)
    d["log_ref"] = np.log1p(d["ref_rate"])
    d["base"] = np.log1p(d["ref_rate"] * d["p50"])
    d["y"] = np.log1p(d["cnt"]) - d["base"]
    return d


def fit_volume_model(daily: pd.DataFrame, cal: pd.DataFrame, cohorts: pd.Series,
                     cfg: dict[str, Any], window_start: int) -> dict[str, Any]:
    """Quantile LightGBM on residuals before the scoring window + conformal widening."""
    p = cfg["models"]["innocence"]
    calib_start = window_start - p["calib_days"]
    ref = reference_rates(daily, cal, calib_start)
    ok = ref.index[ref["ref_days"] >= p["min_ref_days"]]
    hist = daily[(daily["day_idx"] < window_start) & daily["merchant_id"].isin(ok)]
    hist = hist[hist["day_idx"] >= hist["merchant_id"].map(ref["first_day"])]
    cat_codes = {c: i for i, c in enumerate(sorted(cfg["sim"]["categories"]))}
    peers = peer_uplift(hist, ref, cohorts, p["peer_band"], p["min_ref_days"])
    d = _design(hist, ref, peers, cal, cohorts, cat_codes)
    train, calib = d[d["day_idx"] < calib_start], d[d["day_idx"] >= calib_start]

    models = {}
    for q in p["quantiles"]:
        models[q] = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=200,
                                      learning_rate=0.05, num_leaves=15, verbose=-1,
                                      random_state=cfg["seed"], deterministic=True,
                                      force_row_wise=True).fit(train[MODEL_FEATURES], train["y"])
    lo, hi = min(p["quantiles"]), max(p["quantiles"])
    low = models[lo].predict(calib[MODEL_FEATURES]) - np.log(calib["p50"] / calib["p_lo"])
    high = models[hi].predict(calib[MODEL_FEATURES]) + np.log(calib["p_hi"] / calib["p50"])
    nonconf = np.maximum(low - calib["y"], calib["y"] - high)       # split-conformal score
    qhat = float(np.quantile(nonconf, 1 - 2 * lo))
    return {"models": models, "qhat": qhat, "cat_codes": cat_codes, "lo": lo, "hi": hi}


def volume_bands(vm: dict[str, Any], daily: pd.DataFrame, cal: pd.DataFrame, cohorts: pd.Series,
                 cfg: dict[str, Any], as_of_day: int,
                 peers: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Expected count and [lower, upper] band for every merchant-day in the scoring window.

    Returns (band rows, peer table). Pass `peers` to re-use a population peer table
    (single-merchant re-scoring in the app).
    """
    p = cfg["models"]["innocence"]
    start = as_of_day - cfg["features"]["window_long"] + 1
    ref = reference_rates(daily, cal, start)
    win = daily[(daily["day_idx"] >= start) & (daily["day_idx"] <= as_of_day)]
    if peers is None:
        peers = peer_uplift(win, ref, cohorts, p["peer_band"], p["min_ref_days"])
    d = _design(win, ref, peers, cal, cohorts, vm["cat_codes"])
    q_lo = vm["models"][vm["lo"]].predict(d[MODEL_FEATURES])
    q_hi = vm["models"][vm["hi"]].predict(d[MODEL_FEATURES])
    d["expected"] = np.expm1(d["base"])
    d["lower"] = np.expm1(d["base"] + q_lo - np.log(d["p50"] / d["p_lo"]) - vm["qhat"]).clip(lower=0)
    d["upper"] = np.expm1(d["base"] + q_hi + np.log(d["p_hi"] / d["p50"]) + vm["qhat"])
    d["above"] = d["cnt"] > d["upper"]
    d["active"] = d["day_idx"] >= d["first_day"].fillna(np.inf)
    return d[["merchant_id", "day_idx", "date", "cnt", "expected", "lower", "upper", "above",
              "active", "p50", "p_hi", "ref_rate", "ref_days"]], peers


def volume_verdict(bands: pd.DataFrame, feats: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Per merchant: is volume up, and if so is it inside the peer/calendar band?"""
    p = cfg["models"]["innocence"]
    act = bands[bands["active"]]
    g = act.groupby("merchant_id")
    out = pd.DataFrame({
        "exceed_rate": g["above"].mean(),
        "days_above": g["above"].sum(),
        "window_days": g.size(),
        "peer_uplift_max": g["p50"].max(),
        "peer_uplift_hi_max": g["p_hi"].max(),
        "ref_days": g["ref_days"].first(),
    }).reindex(feats.index)
    out["exceed_rate"] = out["exceed_rate"].fillna(0.0)
    out["cold_start"] = out["ref_days"].fillna(0) < p["min_ref_days"]
    out["vol_ratio"] = feats["vol_ratio_hist"]
    out["volume_up"] = (out["vol_ratio"] >= p["volume_up_ratio"]) & ~out["cold_start"]
    out["volume_explained"] = (out["exceed_rate"] <= p["exceed_tolerance"]) | out["cold_start"]
    return out


# ------------------------------------------------------------------ (b) composition
def js_distance(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Row-wise Jensen-Shannon distance (base 2, in [0, 1]) between probability vectors."""
    p = p / p.sum(axis=1, keepdims=True).clip(min=1e-12)
    q = q / q.sum(axis=1, keepdims=True).clip(min=1e-12)
    m = 0.5 * (p + q)
    with np.errstate(divide="ignore", invalid="ignore"):
        kl_p = np.where(p > 0, p * np.log2(p / m), 0.0).sum(axis=1)
        kl_q = np.where(q > 0, q * np.log2(q / m), 0.0).sum(axis=1)
    return np.sqrt(np.clip(0.5 * (kl_p + kl_q), 0, None))


def payer_geo(feats: pd.DataFrame) -> np.ndarray:
    """Payer geography mix: [local, non-local, nationwide roaming] shares."""
    roam = np.minimum(feats["multi_city_payer_share"].to_numpy(), feats["nonlocal_share"].to_numpy())
    local = 1 - feats["nonlocal_share"].to_numpy()
    return np.column_stack([local, feats["nonlocal_share"].to_numpy() - roam, roam])


DIMENSIONS = {"hours": HOURLY, "amounts": AMOUNT_HIST, "payers": None}


def _dist(feats: pd.DataFrame, dim: str) -> np.ndarray:
    return payer_geo(feats) if dim == "payers" else feats[DIMENSIONS[dim]].to_numpy()


def composition_tests(cur: pd.DataFrame, base: pd.DataFrame, cohorts: pd.Series,
                      cfg: dict[str, Any], ref: dict[str, Any] | None = None
                      ) -> tuple[pd.DataFrame, dict[str, Any]]:
    """JS distance of hours / amounts / payer geography vs own history and vs peers now.

    Each distance is also z-scored within the cohort, so 'big' means big for this category.
    `ref` holds population peer profiles + z stats; pass it to score a single merchant.
    """
    p = cfg["models"]["innocence"]
    coh = cohorts.reindex(cur.index)
    has_hist = cur["has_history"].to_numpy() == 1
    out = pd.DataFrame(index=cur.index)
    new_ref: dict[str, Any] = {"peer_profile": {}, "z": {}}
    for dim in DIMENSIONS:
        now, past = _dist(cur, dim), _dist(base.reindex(cur.index), dim)
        if ref is None:
            prof = pd.DataFrame(now, index=cur.index).groupby(coh.to_numpy()).mean()
        else:
            prof = ref["peer_profile"][dim]
        new_ref["peer_profile"][dim] = prof
        out[f"js_{dim}_self"] = np.where(has_hist, js_distance(now, past), 0.0)
        out[f"js_{dim}_peer"] = js_distance(now, prof.reindex(coh.to_numpy()).to_numpy())
    for col in [c for c in out.columns if c.startswith("js_")]:
        if ref is None:
            stats = out[col].groupby(coh.to_numpy()).agg(["median", lambda s: (s - s.median()).abs().median()])
            stats.columns = ["median", "mad"]
        else:
            stats = ref["z"][col]
        new_ref["z"][col] = stats
        med = stats["median"].reindex(coh.to_numpy()).to_numpy()
        mad = 1.4826 * stats["mad"].reindex(coh.to_numpy()).to_numpy() + 0.01
        out[col.replace("js_", "comp_") + "_z"] = np.clip((out[col].to_numpy() - med) / mad, -10, 10)
    for dim in DIMENSIONS:
        fired = [(out[f"comp_{dim}_{k}_z"] > p["composition_z"]) & (out[f"js_{dim}_{k}"] > p["min_js"])
                 for k in ("self", "peer")]
        out[f"shift_{dim}"] = fired[0] | fired[1]
    return out, (ref or new_ref)


# ------------------------------------------------------------------ verdict text
def verdict(vol: pd.Series, comp: pd.Series, category: str) -> dict[str, Any]:
    """Human-readable innocence assessment for one merchant."""
    shifted = [d for d in DIMENSIONS if comp[f"shift_{d}"]]
    if vol["cold_start"]:
        vtxt = "New merchant: not enough history to judge volume, so volume is not scored."
    elif not vol["volume_up"]:
        vtxt = f"Volume is in line with its own history (x{vol['vol_ratio']:.1f})."
    elif vol["volume_explained"]:
        vtxt = (f"Volume is up x{vol['vol_ratio']:.1f} vs its own history, and {category} peers in the "
                f"same city tier rose up to x{vol['peer_uplift_hi_max']:.1f} on the same days. Only "
                f"{int(vol['days_above'])} of {int(vol['window_days'])} days were above the expected "
                f"range, so the extra volume is explained.")
    else:
        vtxt = (f"Volume is up x{vol['vol_ratio']:.1f} vs its own history, but peers moved only "
                f"x{vol['peer_uplift_max']:.1f} (typical). {int(vol['days_above'])} of "
                f"{int(vol['window_days'])} days were above the expected range, so the volume is NOT explained.")
    ctxt = ("Business mix (hours, amounts, payer geography) is unchanged."
            if not shifted else f"Business mix changed in: {', '.join(shifted)}. The Innocence "
            "Engine cannot discount this, because a festival explains more sales, not different sales.")
    if vol["volume_up"] and vol["volume_explained"] and not shifted:
        status = "Cleared"
    elif shifted:
        status = "Not cleared: business mix changed"
    elif vol["volume_up"] and not vol["volume_explained"]:
        status = "Not cleared: unexplained volume"
    else:
        status = "Nothing to explain"
    return {"status": status, "volume_text": vtxt, "composition_text": ctxt, "shifted": shifted}
