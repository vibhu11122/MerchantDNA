"""Event alignment with cricket matches and wickets (a feature, never a stand-alone rule)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from merchantdna.features.windows import FeatureContext


def event_features(w: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Match-evening lift, correlation of daily volume with match days, post-wicket lift."""
    ev = ctx.cfg["features"]["evening_hours"]
    is_match_day = ctx.calendar["ipl_match"].to_numpy()[w["day_idx"].to_numpy()]
    evening = w["hour"].between(ev[0], ev[1]).to_numpy()
    days = w.groupby("merchant_id", observed=False)["day_idx"].agg(["min", "max"])

    df = pd.DataFrame({"merchant_id": w["merchant_id"].to_numpy(), "day": w["day_idx"].to_numpy(),
                       "match_ev": evening & is_match_day, "other_ev": evening & ~is_match_day})
    window_days = np.unique(w["day_idx"].to_numpy())
    n_match = max(int(ctx.calendar["ipl_match"].to_numpy()[window_days].sum()), 1)
    n_other = max(len(window_days) - n_match, 1)
    g = df.groupby("merchant_id", observed=False)
    out = pd.DataFrame({"ipl_evening_lift": (g["match_ev"].sum() / n_match + 0.5)
                        / (g["other_ev"].sum() / n_other + 0.5)})

    daily = df.groupby(["merchant_id", "day"], observed=False).size().unstack(fill_value=0)
    daily = daily.reindex(columns=window_days, fill_value=0)
    flag = ctx.calendar["ipl_match"].to_numpy()[window_days].astype(float)
    x = daily.to_numpy(float)
    xc = x - x.mean(axis=1, keepdims=True)
    fc = flag - flag.mean()
    denom = np.sqrt((xc ** 2).sum(axis=1) * (fc ** 2).sum()).clip(min=1e-9)
    out["ipl_corr"] = pd.Series((xc @ fc) / denom, index=daily.index)

    in_match = ctx.match_minutes[w["day_idx"].to_numpy(), w["minute"].to_numpy()]
    post = ctx.post_wicket[w["day_idx"].to_numpy(), w["minute"].to_numpy()]
    expected = max(ctx.post_wicket[window_days].sum() / max(ctx.match_minutes[window_days].sum(), 1), 1e-6)
    m = pd.DataFrame({"merchant_id": w["merchant_id"].to_numpy(), "in": in_match, "post": post & in_match})
    gm = m.groupby("merchant_id", observed=False)[["in", "post"]].sum()
    prior = ctx.cfg["features"]["post_wicket_prior_txns"]          # shrink small samples to lift 1
    observed = (gm["post"] + prior * expected) / (gm["in"] + prior)
    out["post_wicket_lift"] = observed / expected
    return out
