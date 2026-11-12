"""Metric helpers: PR-AUC with bootstrap CI, budget metrics, false-positive rates."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve


def pr_auc_ci(y: pd.Series, s: pd.Series, n_boot: int = 300, seed: int = 42) -> dict[str, float]:
    """Average precision (PR-AUC) and a 90% bootstrap interval."""
    rng = np.random.default_rng(seed)
    yv, sv = y.to_numpy(), s.to_numpy()
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, len(yv), len(yv))
        if yv[i].sum() > 0:
            boots.append(average_precision_score(yv[i], sv[i]))
    return {"pr_auc": float(average_precision_score(yv, sv)),
            "pr_auc_lo": float(np.percentile(boots, 5)), "pr_auc_hi": float(np.percentile(boots, 95))}


def budget_flags(s: pd.Series, budget: float) -> pd.Series:
    """True for the top `budget` share of merchants by score (the analyst review budget)."""
    k = max(1, int(round(budget * len(s))))
    return s.rank(ascending=False, method="first") <= k


def flag_metrics(y: pd.Series, flagged: pd.Series, surge: pd.Series) -> dict[str, float]:
    """Precision, recall, overall FPR and FPR on legitimate surge merchants for a flag set."""
    tp = int((flagged & (y == 1)).sum())
    fp = int((flagged & (y == 0)).sum())
    return {"flagged": int(flagged.sum()), "precision": tp / max(tp + fp, 1),
            "recall": tp / max(int(y.sum()), 1), "fpr": fp / max(int((y == 0).sum()), 1),
            "surge_fpr": float(flagged[surge].mean()) if surge.any() else float("nan")}


def pr_curve(y: pd.Series, s: pd.Series) -> dict[str, list[float]]:
    """Precision-recall curve points (for plotting)."""
    p, r, _ = precision_recall_curve(y, s)
    return {"precision": p.tolist(), "recall": r.tolist()}
