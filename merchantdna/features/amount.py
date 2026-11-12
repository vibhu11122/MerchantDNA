"""Amount-distribution features (ticket size, price-point clustering, entropy)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from merchantdna.features.windows import FeatureContext


def _entropy(p: np.ndarray) -> float:
    """Shannon entropy (bits) of a probability vector."""
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def amount_histogram(w: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Share of each merchant's txns falling in each configured amount bin."""
    bins = ctx.cfg["features"]["amount_bins"]
    b = np.clip(np.digitize(w["amount"].to_numpy(), bins) - 1, 0, len(bins) - 2)
    h = pd.crosstab(w["merchant_id"], b).reindex(columns=range(len(bins) - 1), fill_value=0)
    return h.div(h.sum(axis=1).clip(lower=1), axis=0)


def amount_features(w: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Mean/median/IQR, entropy, top-price share, round share and 499/999/1999 shares."""
    points = np.array(ctx.cfg["features"]["price_points"], dtype=float)
    a = w["amount"].to_numpy()
    df = pd.DataFrame({
        "merchant_id": w["merchant_id"].to_numpy(),
        "log_amt": np.log1p(a),
        "on_point": np.isin(a, points),
        "near_point": (np.abs(a[:, None] / points[None, :] - 1) < 0.1).any(axis=1),
        "round": (a % 50 == 0) | (a % 100 == 99),
    })
    g = df.groupby("merchant_id", observed=False)
    out = pd.DataFrame({
        "amt_mean": g["log_amt"].mean().pipe(np.expm1),
        "amt_median": g["log_amt"].median().pipe(np.expm1),
        "amt_log_iqr": g["log_amt"].quantile(0.75) - g["log_amt"].quantile(0.25),
        "pricepoint_share": g["on_point"].mean(),
        "near_pricepoint_share": g["near_point"].mean(),
        "round_share": g["round"].mean(),
    })
    counts = w.groupby(["merchant_id", "amount"], observed=True).size()
    out["top_price_share"] = counts.groupby(level=0, observed=False).max() \
        / counts.groupby(level=0, observed=False).sum()
    hist = amount_histogram(w, ctx)
    out["amt_entropy"] = hist.apply(lambda r: _entropy(r.to_numpy()), axis=1)
    return out
