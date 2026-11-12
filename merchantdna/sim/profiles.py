"""Sampling helpers: hours, amounts and payer ids for legit and betting behaviour."""
from __future__ import annotations

import numpy as np

CITY_ID_BLOCK = 1_000_000          # payer id = city_index * block + k
TRAVELLER_ID_BASE = 40_000_000     # honest payers who travel / shop online across cities
BETTOR_ID_BASE = 50_000_000        # nationwide bettor pool ids start here
RING_ID_BASE = 60_000_000          # mule ring shared payer pools start here
RING_ID_BLOCK = 10_000


def normalise(weights: list[float] | np.ndarray) -> np.ndarray:
    """Turn non-negative weights into probabilities that sum to 1."""
    w = np.asarray(weights, dtype=float)
    return w / w.sum()


def sample_seconds_of_day(rng: np.random.Generator, hourly: np.ndarray, n: int) -> np.ndarray:
    """Seconds after midnight: hour from the 24-bin profile, uniform inside the hour."""
    hours = rng.choice(24, size=n, p=hourly)
    return hours * 3600 + rng.integers(0, 3600, size=n)


def sample_legit_amounts(rng: np.random.Generator, median: float, sigma: float,
                         price_points: dict[int, float], n: int,
                         tags: list[int] | None = None, tag_share: float = 0.0) -> np.ndarray:
    """Lognormal basket amounts; some snapped to common price tags (x99, x49), some fixed prices."""
    amounts = np.round(median * np.exp(sigma * rng.standard_normal(n)))
    if tags and tag_share > 0:
        snap = rng.random(n) < tag_share
        t = np.asarray(tags, dtype=float)
        amounts[snap] = t[np.abs(amounts[snap, None] - t[None, :]).argmin(axis=1)]
    if price_points:
        prices = np.array(list(price_points.keys()), dtype=float)
        shares = np.array(list(price_points.values()))
        use_fixed = rng.random(n) < shares.sum()
        amounts[use_fixed] = rng.choice(prices, size=use_fixed.sum(), p=shares / shares.sum())
    return np.maximum(amounts, 10)


def sample_betting_amounts(rng: np.random.Generator, price_points: dict[int, float],
                           cover_median: float, cover_sigma: float, n: int,
                           jitter: float = 0.0) -> np.ndarray:
    """Bet top-ups cluster on 499/999/1999; the rest look like normal cover purchases.

    `jitter` > 0 adds +/- noise around each price point (the adaptive mimic's trick).
    """
    amounts = sample_legit_amounts(rng, cover_median, cover_sigma, {}, n)
    prices = np.array(list(price_points.keys()), dtype=float)
    shares = np.array(list(price_points.values()))
    on_point = rng.random(n) < shares.sum()
    picked = rng.choice(prices, size=on_point.sum(), p=shares / shares.sum())
    if jitter > 0:
        picked = np.round(picked * (1 + rng.uniform(-jitter, jitter, size=picked.size)))
    amounts[on_point] = picked
    return amounts


def hash_ids(ids: np.ndarray) -> np.ndarray:
    """Deterministic 64-bit mix (splitmix64) so raw payer ids never leave the simulator."""
    x = ids.astype(np.uint64) + np.uint64(0x9E3779B97F4A7C15)
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    x = x ^ (x >> np.uint64(31))
    return x.view(np.int64)
