"""Generate transactions for one merchant from its daily plan, category profile and calendar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from merchantdna.sim import profiles as pr
from merchantdna.sim.archetypes import daily_plan


@dataclass
class PayerPools:
    """Home city of every payer in the shared pools (bettors and mule rings)."""
    bettor_city: np.ndarray      # city index of each nationwide bettor (all communities)
    ring_city: np.ndarray        # city index of each ring-pool payer, flattened by ring
    traveller_city: np.ndarray   # home city of each honest traveller


def make_pools(cfg: dict[str, Any], n_rings: int, rng: np.random.Generator) -> PayerPools:
    """Bettors and ring payers live all over the country (uniform over cities)."""
    sim = cfg["sim"]
    n_cities = len(sim["cities"])
    n_bettors = sim["betting"]["bettor_pool"] * sim["betting"]["n_bettor_communities"]
    return PayerPools(
        bettor_city=rng.integers(0, n_cities, n_bettors),
        ring_city=rng.integers(0, n_cities, max(n_rings, 1) * pr.RING_ID_BLOCK),
        traveller_city=rng.integers(0, n_cities, sim["traveller_pool"]),
    )


def payer_city_index(ids: np.ndarray, pools: PayerPools) -> np.ndarray:
    """Recover each raw payer id's home city (raw ids never leave the simulator)."""
    city = ids // pr.CITY_ID_BLOCK
    is_traveller = (ids >= pr.TRAVELLER_ID_BASE) & (ids < pr.BETTOR_ID_BASE)
    is_bettor = (ids >= pr.BETTOR_ID_BASE) & (ids < pr.RING_ID_BASE)
    is_ring = ids >= pr.RING_ID_BASE
    city[is_traveller] = pools.traveller_city[ids[is_traveller] - pr.TRAVELLER_ID_BASE]
    city[is_bettor] = pools.bettor_city[ids[is_bettor] - pr.BETTOR_ID_BASE]
    city[is_ring] = pools.ring_city[ids[is_ring] - pr.RING_ID_BASE]
    return city


def _calendar_mult(p: dict[str, Any], cal: pd.DataFrame, cprof: dict[str, Any]) -> np.ndarray:
    """Legit demand multiplier per day: weekends, month-start fees, minor festivals, Diwali."""
    m = np.where(cal["is_weekend"], cprof["weekend_mult"], 1.0)
    if "month_start_mult" in cprof:
        m = m * np.where(cal["date"].dt.day <= 5, cprof["month_start_mult"], 0.75)
    m = m * cal["other_festival_mult"].to_numpy()
    dm = p["diwali_mult"]
    diwali = np.where(cal["is_diwali_peak"], dm,
                      np.where(cal["is_diwali_window"], 1 + (dm - 1) * 0.4, 1.0))
    return m * diwali


def _legit_payers(p: dict[str, Any], cfg: dict[str, Any], n: int, rng: np.random.Generator,
                  regulars: np.ndarray) -> np.ndarray:
    """Mostly local walk-ins, some regulars, a few visitors from other cities."""
    sim = cfg["sim"]
    pool, n_cities = sim["city_payer_pool"], len(sim["cities"])
    repeat_p = sim["categories"][p["category"]]["repeat_prob"]
    visitor_p = p["nonlocal_share"]
    r = rng.random(n)
    ids = p["city_idx"] * pr.CITY_ID_BLOCK + rng.integers(0, pool, n)          # local walk-in
    is_regular = r < repeat_p
    ids[is_regular] = rng.choice(regulars, size=is_regular.sum())
    is_visitor = (r >= repeat_p) & (r < repeat_p + visitor_p)
    ids[is_visitor] = rng.integers(0, n_cities, is_visitor.sum()) * pr.CITY_ID_BLOCK \
        + rng.integers(0, pool, is_visitor.sum())
    is_traveller = rng.random(n) < p["traveller_share"]
    ids[is_traveller] = pr.TRAVELLER_ID_BASE + rng.integers(0, sim["traveller_pool"], is_traveller.sum())
    return ids


def _ring_payers(p: dict[str, Any], cfg: dict[str, Any], n: int, rng: np.random.Generator) -> np.ndarray:
    """Payers from the mule ring's shared pool."""
    return pr.RING_ID_BASE + p["ring_id"] * pr.RING_ID_BLOCK \
        + rng.integers(0, cfg["sim"]["ring_payer_pool"], n)


def _betting_times(cal: pd.DataFrame, days: np.ndarray, bcfg: dict[str, Any], hourly: np.ndarray,
                   wicket_share: float, rng: np.random.Generator) -> np.ndarray:
    """Seconds of day for betting txns; on match days a share lands minutes after a wicket."""
    secs = pr.sample_seconds_of_day(rng, hourly, days.size)
    wickets = cal["wicket_minutes"].to_numpy()
    after_wicket = (rng.random(days.size) < wicket_share) & cal["ipl_match"].to_numpy()[days]
    for k in np.flatnonzero(after_wicket):
        w = wickets[days[k]]
        secs[k] = w[rng.integers(len(w))] * 60 + rng.integers(0, bcfg["post_wicket_minutes"] * 60)
    return secs


def generate_merchant(p: dict[str, Any], cal: pd.DataFrame, cfg: dict[str, Any],
                      pools: PayerPools, rng: np.random.Generator) -> pd.DataFrame:
    """All transactions of one merchant over the simulated period."""
    sim, bcfg = cfg["sim"], cfg["sim"]["betting"]
    cprof = sim["categories"][p["category"]]
    n_days = len(cal)
    legit_mult, bet_mult = daily_plan(p, n_days)
    noise = rng.gamma(sim["daily_noise_shape"], 1 / sim["daily_noise_shape"], n_days)
    is_mimic = p["archetype"] == "adaptive_mimic"
    match = cal["ipl_match"].to_numpy()

    lam_legit = p["base_daily"] * legit_mult * _calendar_mult(p, cal, cprof) * noise \
        * np.where(match, p["legit_match_mult"], 1.0)
    lam_bet = p["base_daily"] * bet_mult * np.where(match, p["bet_match_mult"], 1.0) * noise
    n_legit, n_bet = rng.poisson(lam_legit), rng.poisson(lam_bet)

    # ---- legit (declared-category) business
    days_l = np.repeat(np.arange(n_days), n_legit)
    hourly = pr.normalise(p["hourly"])
    secs_l = pr.sample_seconds_of_day(rng, hourly, days_l.size)
    amt_l = pr.sample_legit_amounts(rng, cprof["amount_median"], cprof["amount_sigma"],
                                    p["legit_price_points"], days_l.size,
                                    sim["price_tags"], sim["legit_price_tag_share"])
    n_regulars = max(20, int(p["base_daily"] * sim["regulars_per_daily_txn"]))
    regulars = p["city_idx"] * pr.CITY_ID_BLOCK + rng.integers(0, sim["city_payer_pool"], n_regulars)
    pay_l = _legit_payers(p, cfg, days_l.size, rng, regulars)
    if p["is_front"]:                                  # front store: a few ring payers mixed in
        ring = rng.random(days_l.size) < sim["front_store_ring_payer_share"]
        pay_l[ring] = _ring_payers(p, cfg, ring.sum(), rng)
    card_l = rng.random(days_l.size) < cprof["card_share"]
    refund_l = rng.random(days_l.size) < cprof["refund_rate"]

    # ---- betting-style collections
    days_b = np.repeat(np.arange(n_days), n_bet)
    bet_hourly = hourly if is_mimic else pr.normalise(bcfg["hourly"])
    secs_b = _betting_times(cal, days_b, bcfg, bet_hourly, 0.0 if is_mimic else bcfg["post_wicket_share"], rng)
    amt_b = pr.sample_betting_amounts(rng, p["bet_price_points"], cprof["amount_median"],
                                      cprof["amount_sigma"], days_b.size, jitter=p["bet_jitter"])
    community = pr.BETTOR_ID_BASE + p["bettor_community"] * bcfg["bettor_pool"]
    bettors = community + rng.choice(bcfg["bettor_pool"], bcfg["bettors_per_merchant"], replace=False)
    pay_b = rng.choice(bettors, size=days_b.size)
    if p["ring_id"] >= 0:
        ring = rng.random(days_b.size) < sim["ring_payer_share"]
        pay_b[ring] = _ring_payers(p, cfg, ring.sum(), rng)
    local = rng.random(days_b.size) < p["local_cover"]
    pay_b[local] = p["city_idx"] * pr.CITY_ID_BLOCK + rng.integers(0, sim["city_payer_pool"], local.sum())
    card_b = rng.random(days_b.size) < bcfg["card_share"]
    refund_b = rng.random(days_b.size) < bcfg["refund_rate"]

    days = np.concatenate([days_l, days_b])
    secs = np.concatenate([secs_l, secs_b]) % 86400
    payers = np.concatenate([pay_l, pay_b])
    ts = cal["date"].to_numpy()[days] + secs.astype("timedelta64[s]")
    return pd.DataFrame({
        "merchant_id": p["merchant_id"],
        "payer_raw": payers,
        "timestamp": ts,
        "amount": np.concatenate([amt_l, amt_b]).astype("float32"),
        "is_card": np.concatenate([card_l, card_b]),
        "is_refund": np.concatenate([refund_l, refund_b]),
        "is_bet": np.concatenate([np.zeros(days_l.size, bool), np.ones(days_b.size, bool)]),
    })


def settlements_for(txns: pd.DataFrame, plans: list[dict[str, Any]], cfg: dict[str, Any],
                    rng: np.random.Generator) -> pd.DataFrame:
    """Daily payouts. Betting-heavy days (and some honest merchants) settle within hours."""
    sim = cfg["sim"]
    t = txns.assign(date=txns["timestamp"].dt.normalize(),
                    signed=np.where(txns["is_refund"], -txns["amount"], txns["amount"]))
    daily = t.groupby(["merchant_id", "date"], observed=True).agg(
        payout_amount=("signed", "sum"), bet_share=("is_bet", "mean")).reset_index()
    legit_fast = {p["merchant_id"] for p in plans if p["fast_payout"] and not p["label"]}
    fraud_fast = {p["merchant_id"] for p in plans if p["fast_payout"] and p["label"]}
    betting_day = daily["bet_share"].to_numpy() > 0.2              # fraud speeds up once betting starts
    fast = daily["merchant_id"].isin(legit_fast).to_numpy() \
        | (daily["merchant_id"].isin(fraud_fast).to_numpy() & betting_day)
    slow_h = rng.uniform(*sim["legit_payout_delay_hours"], len(daily))
    fast_h = rng.uniform(*sim["betting"]["payout_delay_hours"], len(daily))
    daily["payout_delay_hours"] = np.round(np.where(fast, fast_h, slow_h), 1)
    return daily.drop(columns="bet_share")
