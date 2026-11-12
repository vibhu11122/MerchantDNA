"""Baselines MerchantDNA must beat: static rules and a plain Isolation Forest."""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from merchantdna.features.columns import SHAPE, VOLUME


def rules_score(feats: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.Series, pd.Series]:
    """Typical static rules: volume jump OR night-time share above a threshold.

    Returns (continuous score for ranking, boolean 'rule fired')."""
    e = cfg["eval"]
    s = np.maximum(feats["vol_ratio_hist"] / e["rule_volume_ratio"], feats["night_share"] / e["rule_night_share"])
    return pd.Series(s, index=feats.index), pd.Series(s >= 1.0, index=feats.index)


def fit_iforest(feats: pd.DataFrame, cfg: dict[str, Any]) -> IsolationForest:
    """Unsupervised anomaly detector on the raw behaviour + volume features."""
    return IsolationForest(n_estimators=300, contamination=cfg["eval"]["iforest_contamination"],
                           random_state=cfg["seed"]).fit(feats[SHAPE + VOLUME])


def iforest_score(model: IsolationForest, feats: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(anomaly score, flagged) - higher score = more anomalous."""
    x = feats[SHAPE + VOLUME]
    return (pd.Series(-model.score_samples(x), index=feats.index),
            pd.Series(model.predict(x) == -1, index=feats.index))
