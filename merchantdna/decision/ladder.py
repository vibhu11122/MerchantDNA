"""Action ladder: choose the proportionate response by expected cost.

For each rung r: net benefit = P x harm_if_missed x prevented_r - (1 - P) x cost_disrupt x disruption_r.
Pick the rung with the highest net benefit ("Monitor" has net benefit 0). Analyst
capacity limits how many merchants can be reviewed; the rest wait in the queue.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def tier(score: float | np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    """LOW / MEDIUM / HIGH from the 0-100 risk score."""
    t = cfg["decision"]["tiers"]
    s = np.asarray(score, dtype=float)
    return np.where(s >= t["high"], "HIGH", np.where(s >= t["medium"], "MEDIUM", "LOW"))


def net_benefits(p: np.ndarray, cfg: dict[str, Any], harm: float | None = None,
                 cost: float | None = None) -> np.ndarray:
    """[n_merchants, n_rungs] expected net benefit in INR."""
    d = cfg["decision"]
    harm = d["harm_if_missed"] if harm is None else harm
    cost = d["cost_disrupt_legit"] if cost is None else cost
    prevent = np.array([r[1] for r in d["rungs"]])
    disrupt = np.array([r[2] for r in d["rungs"]])
    p = np.asarray(p, dtype=float)[:, None]
    return p * harm * prevent[None, :] - (1 - p) * cost * disrupt[None, :]


def choose_rungs(p: pd.Series, cfg: dict[str, Any], harm: float | None = None,
                 cost: float | None = None, capacity: int | None = None) -> pd.DataFrame:
    """Recommended rung per merchant + whether it fits in the analyst review queue."""
    d = cfg["decision"]
    capacity = d["analyst_capacity"] if capacity is None else capacity
    nb = net_benefits(p.to_numpy(), cfg, harm, cost)
    best = nb.argmax(axis=1)
    out = pd.DataFrame({"rung_index": best, "rung": [d["rungs"][i][0] for i in best],
                        "net_benefit": nb.max(axis=1)}, index=p.index)
    needs_review = out["rung_index"] > 0
    order = out.loc[needs_review, "net_benefit"].sort_values(ascending=False).index
    out["in_review_queue"] = out.index.isin(order[:capacity])
    out["awaiting_capacity"] = needs_review & ~out["in_review_queue"]
    return out


def rung_thresholds(cfg: dict[str, Any], harm: float | None = None, cost: float | None = None) -> list[float]:
    """Lowest P at which each rung becomes the best choice (for the Model Lab chart)."""
    grid = np.linspace(0, 1, 2001)
    best = net_benefits(grid, cfg, harm, cost).argmax(axis=1)
    return [float(grid[np.argmax(best >= r)]) if (best >= r).any() else 1.0
            for r in range(len(cfg["decision"]["rungs"]))]
