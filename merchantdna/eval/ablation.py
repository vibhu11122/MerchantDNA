"""Ablations: retrain the stacker without one pillar and see what breaks."""
from __future__ import annotations

from typing import Any

import pandas as pd

from merchantdna.models import fusion as F


def ablation_scores(x_gated: pd.DataFrame, x_ungated: pd.DataFrame, y: pd.Series,
                    labelled: pd.Index, cfg: dict[str, Any]) -> dict[str, pd.Series]:
    """0-100 scores for the full system and each ablated variant (same labelled set)."""
    variants = {
        "full": (x_gated, F.ALL),
        "no_innocence_engine": (x_ungated, F.ALL),
        "no_network": (x_gated, [c for c in F.ALL if c not in F.NETWORK]),
        "no_payer_features": (x_gated, [c for c in F.ALL if c not in F.PAYER_DERIVED]),
    }
    out = {}
    for name, (x, cols) in variants.items():
        fm = F.fit_fusion(x.loc[labelled], y.loc[labelled], cfg, cols)
        out[name] = 100 * F.predict_fusion(fm, x)
    return out
