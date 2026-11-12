"""Load transactions once, add helper columns, and slice time windows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from merchantdna.utils.io import read_merchants_for_models, read_table


@dataclass
class FeatureContext:
    """Everything feature functions need besides the window's transactions."""
    cfg: dict[str, Any]
    merchants: pd.DataFrame          # merchant_id, city, tier, declared_category (no labels!)
    calendar: pd.DataFrame
    post_wicket: np.ndarray          # [n_days, 1440] True if minute is <=N min after a wicket
    match_minutes: np.ndarray        # [n_days, 1440] True during a match


def city_tiers(cfg: dict[str, Any]) -> dict[str, int]:
    """City name -> tier (1 = metro, 2 = smaller city)."""
    return {c[0]: c[2] for c in cfg["sim"]["cities"]}


def build_context(cfg: dict[str, Any]) -> FeatureContext:
    """Merchant reference data + minute-level match/wicket masks."""
    m = read_merchants_for_models()[["merchant_id", "declared_category", "city", "onboard_date"]]
    m = m.assign(tier=m["city"].map(city_tiers(cfg)))
    cal = read_table("calendar")
    n_days = len(cal)
    post = np.zeros((n_days, 1440), bool)
    match = np.zeros((n_days, 1440), bool)
    span = cfg["sim"]["betting"]["post_wicket_minutes"]
    start = int(cfg["sim"]["match_start_hour"] * 60)
    end = int(cfg["sim"]["match_end_hour"] * 60)
    for d, (is_match, wickets) in enumerate(zip(cal["ipl_match"], cal["wicket_minutes"])):
        if is_match:
            match[d, start:end] = True
            for w in wickets:
                post[d, w:w + span] = True
    return FeatureContext(cfg, m, cal, post, match)


def load_transactions(ctx: FeatureContext) -> pd.DataFrame:
    """All transactions with the derived columns used by every feature family."""
    tx = read_table("transactions")
    start = ctx.calendar["date"].min()
    tx["date"] = tx["timestamp"].dt.normalize()
    tx["day_idx"] = ((tx["date"] - start).dt.days).astype("int16")
    tx["hour"] = tx["timestamp"].dt.hour.astype("int8")
    tx["minute"] = (tx["hour"].astype("int16") * 60 + tx["timestamp"].dt.minute).astype("int16")
    city_of = ctx.merchants.set_index("merchant_id")["city"]
    tx["merchant_city"] = tx["merchant_id"].map(city_of).astype("category")
    tx["is_local"] = tx["payer_city"].astype(str).to_numpy() == tx["merchant_city"].astype(str).to_numpy()
    return tx


def window(tx: pd.DataFrame, end_day: int, length: int) -> pd.DataFrame:
    """Transactions with day_idx in [end_day - length + 1, end_day]."""
    return tx[(tx["day_idx"] > end_day - length) & (tx["day_idx"] <= end_day)]


def snapshot_days(n_days: int, every: int, first: int) -> list[int]:
    """Weekly as-of days, always ending on the last simulated day."""
    days = list(range(n_days - 1, first - 1, -every))
    return sorted(days)
