"""Merchant DNA: a small autoencoder compresses behaviour "shape" into a 12-number code.

sklearn MLPRegressor learns X -> X through a 12-unit bottleneck; we read the bottleneck
by running the first layers forward by hand. Drift = how far the code moved from the
merchant's own history and from its declared category's centre.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from merchantdna.features.columns import SHAPE


def fit_autoencoder(train: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    """Standardise SHAPE features and train the autoencoder (tanh units)."""
    p = cfg["models"]["autoencoder"]
    scaler = StandardScaler().fit(train[SHAPE])
    x = np.clip(scaler.transform(train[SHAPE]), -6, 6)
    ae = MLPRegressor(hidden_layer_sizes=tuple(p["hidden"]), activation="tanh", alpha=p["alpha"],
                      max_iter=p["max_iter"], random_state=cfg["seed"], early_stopping=True)
    ae.fit(x, x)
    return {"scaler": scaler, "ae": ae, "bottleneck_layer": len(p["hidden"]) // 2 + 1}


def _scaled(model: dict[str, Any], feats: pd.DataFrame) -> np.ndarray:
    return np.clip(model["scaler"].transform(feats[SHAPE]), -6, 6)


def embed(model: dict[str, Any], feats: pd.DataFrame) -> np.ndarray:
    """The DNA code: activations of the bottleneck layer."""
    h = _scaled(model, feats)
    ae = model["ae"]
    for W, b in list(zip(ae.coefs_, ae.intercepts_))[:model["bottleneck_layer"]]:
        h = np.tanh(h @ W + b)
    return h


def recon_error(model: dict[str, Any], feats: pd.DataFrame) -> np.ndarray:
    """Mean squared reconstruction error (how 'unusual' the shape is overall)."""
    x = _scaled(model, feats)
    return ((model["ae"].predict(x) - x) ** 2).mean(axis=1)


def category_centroids(codes: pd.DataFrame, declared: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """Median code per declared category, and each category's typical distance to it."""
    cat = declared.reindex(codes.index)
    cent = codes.groupby(cat.to_numpy()).median()
    dist = np.linalg.norm(codes.to_numpy() - cent.loc[cat].to_numpy(), axis=1)
    spread = pd.Series(dist, index=codes.index).groupby(cat.to_numpy()).median()
    return cent, spread


def drift_scores(model: dict[str, Any], feats: pd.DataFrame, base_codes: pd.DataFrame,
                 centroids: pd.DataFrame, spread: pd.Series,
                 declared: pd.Series) -> tuple[pd.DataFrame, np.ndarray]:
    """Distance from own history code and from declared-category centre (in typical-spread units)."""
    codes = embed(model, feats)
    cat = declared.reindex(feats.index).to_numpy()
    own = base_codes.reindex(feats.index).to_numpy()
    out = pd.DataFrame(index=feats.index)
    out["dna_drift_self"] = np.linalg.norm(codes - own, axis=1) / spread.loc[cat].to_numpy()
    out["dna_drift_cat"] = np.linalg.norm(codes - centroids.loc[cat].to_numpy(), axis=1) \
        / spread.loc[cat].to_numpy()
    out["dna_recon_error"] = recon_error(model, feats)
    return out, codes
