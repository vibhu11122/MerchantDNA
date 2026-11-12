"""Synthetic calendar: festivals (real Diwali 2026 dates) and a synthetic T20 league."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def date_range(cfg: dict[str, Any], n_days: int) -> pd.DatetimeIndex:
    """The n_days simulated dates, ending on sim.end_date."""
    end = pd.Timestamp(cfg["sim"]["end_date"])
    return pd.date_range(end=end, periods=n_days, freq="D")


def _in_window(dates: pd.DatetimeIndex, start: str, end: str) -> np.ndarray:
    """Boolean mask of dates inside [start, end] (inclusive)."""
    return np.asarray((dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end)))


def build_calendar(cfg: dict[str, Any], n_days: int, rng: np.random.Generator) -> pd.DataFrame:
    """One row per day with festival flags, match flag and wicket times (minutes after midnight)."""
    sim = cfg["sim"]
    dates = date_range(cfg, n_days)
    cal = pd.DataFrame({"date": dates, "day_idx": np.arange(n_days), "dow": dates.dayofweek})
    cal["is_weekend"] = cal["dow"] >= 5
    cal["is_diwali_window"] = _in_window(dates, *sim["diwali_window"])
    cal["is_diwali_peak"] = _in_window(dates, *sim["diwali_peak"])

    other_mult = np.ones(n_days)                       # minor festivals lift everyone a little
    for start, end, mult in sim["other_festivals"]:
        other_mult[_in_window(dates, start, end)] = mult
    cal["other_festival_mult"] = other_mult
    cal["is_other_festival"] = other_mult > 1

    cal["ipl_match"] = rng.random(n_days) < sim["match_day_prob"]
    start_min = int(sim["match_start_hour"] * 60)
    end_min = int(sim["match_end_hour"] * 60)
    cal["match_start"] = [d + pd.Timedelta(minutes=start_min) if m else pd.NaT
                          for d, m in zip(dates, cal["ipl_match"])]
    cal["wicket_minutes"] = [
        np.sort(rng.integers(start_min, end_min, sim["wickets_per_match"])).tolist() if m else []
        for m in cal["ipl_match"]
    ]
    return cal
