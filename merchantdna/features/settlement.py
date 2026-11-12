"""Settlement and payment-mix features."""
from __future__ import annotations

import pandas as pd

from merchantdna.features.windows import FeatureContext


def settlement_features(w: pd.DataFrame, s: pd.DataFrame, ctx: FeatureContext) -> pd.DataFrame:
    """Payout delay, share of fast (<12h) payouts, refund rate and card share."""
    g = s.groupby("merchant_id", observed=False)
    out = pd.DataFrame({
        "payout_delay_mean": g["payout_delay_hours"].mean(),
        "fast_payout_share": (s["payout_delay_hours"] < 12).groupby(s["merchant_id"], observed=False).mean(),
    })
    wg = w.groupby("merchant_id", observed=False)
    out["refund_rate"] = wg["is_refund"].mean()
    out["card_share"] = (w["channel"] == "card").groupby(w["merchant_id"], observed=False).mean()
    return out
