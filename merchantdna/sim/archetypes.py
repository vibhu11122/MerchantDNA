"""Daily behaviour plans per archetype.

Every merchant gets two arrays over the simulated days:
  legit_mult[d] - multiplier on its normal (declared-category) business
  bet_mult[d]   - multiplier on betting-style collections (0 for honest merchants)
Expected daily txns = base_daily * (legit_mult * calendar effects + bet_mult * match effects).
"""
from __future__ import annotations

from typing import Any

import numpy as np

def _active(n_days: int, onboard_day: int) -> np.ndarray:
    """1 on days the merchant exists, 0 before onboarding."""
    return (np.arange(n_days) >= onboard_day).astype(float)


def _ramp(n_days: int, start: int, length: int) -> np.ndarray:
    """0 before `start`, rises linearly to 1 over `length` days, then stays 1."""
    return np.clip((np.arange(n_days) - start) / max(length, 1), 0.0, 1.0)


def daily_plan(p: dict[str, Any], n_days: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (legit_mult, bet_mult) arrays for one merchant's archetype parameters `p`."""
    arch = p["archetype"]
    active = _active(n_days, p["onboard_day"])
    legit = np.ones(n_days)
    bet = np.zeros(n_days)
    w = np.zeros(n_days)                                   # share of flow that is betting

    bw = p["bet_weight"]                                   # share of flow that is betting
    if arch == "growing":
        legit = np.linspace(1.0, p["growth_total"], n_days)
    elif arch in ("betting_collector", "adaptive_mimic"):
        w[:] = bw
    elif arch == "slow_drift":
        w = bw * _ramp(n_days, p["drift_start"], p["drift_ramp"])
    elif arch == "sleeper":
        awake = np.arange(n_days) >= p["wake_day"]
        legit = np.where(awake, 1 - bw, p["dormant_mult"])
        bet = np.where(awake, bw * p["burst_mult"], 0.0)
        return legit * active, bet * active
    elif arch == "mule_network" and not p["is_front"]:
        w[:] = p["mule_intensity"]

    legit = legit * (1 - w)
    bet = w * p["bet_scale"]
    return legit * active, bet * active
