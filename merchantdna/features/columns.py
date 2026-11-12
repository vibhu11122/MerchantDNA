"""Named feature groups, so every model states exactly which inputs it uses."""
from __future__ import annotations

HOURLY = [f"h{h:02d}" for h in range(24)]

TIME = ["night_share", "evening_share", "weekend_share", "burst_index"]
AMOUNT = ["amt_mean", "amt_median", "amt_log_iqr", "amt_entropy", "top_price_share",
          "round_share", "pricepoint_share", "near_pricepoint_share"]
PAYER = ["payers_per_txn", "repeat_txn_share", "new_payer_rate", "payer_hhi",
         "nonlocal_share", "payer_city_entropy", "multi_city_payer_share"]
EVENT = ["ipl_evening_lift", "ipl_corr", "post_wicket_lift"]
SETTLEMENT = ["payout_delay_mean", "fast_payout_share", "refund_rate", "card_share"]
VOLUME = ["cnt_long", "gmv_long", "cnt_short", "gmv_short", "growth_short_vs_long", "daily_fano",
          "vol_ratio_hist"]

# "Shape" = how a merchant does business, independent of how much. This is the DNA.
SHAPE = HOURLY + TIME + AMOUNT + PAYER + EVENT + SETTLEMENT

# Features compared with the declared-category peer cohort (robust z-scores).
PEER_Z = TIME + AMOUNT + PAYER + EVENT + SETTLEMENT + ["cnt_short", "growth_short_vs_long",
                                                      "vol_ratio_hist", "daily_fano"]

# Change vs the merchant's own history.
HISTORY_DELTA = ["night_share", "evening_share", "pricepoint_share", "repeat_txn_share",
                 "multi_city_payer_share", "nonlocal_share", "amt_median", "burst_index"]

LABEL_LIKE = {"label", "archetype"}   # must never appear in any model input
