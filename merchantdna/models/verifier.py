"""Behavioural category verifier: does the merchant BEHAVE like its declared category?

LightGBM multiclass on behaviour-only "shape" features, trained on the history window.
Cross-fitted by merchant: each merchant is scored by a model that never saw it.
Output P(declared | behaviour); a low value means "doesn't behave like what it claims".
"""
from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from merchantdna.features.columns import SHAPE


def make_model(cfg: dict[str, Any], n_classes: int) -> lgb.LGBMClassifier:
    """Small multiclass gradient-boosted trees."""
    p = cfg["models"]["verifier"]
    return lgb.LGBMClassifier(objective="multiclass", num_class=n_classes, verbose=-1,
                              random_state=cfg["seed"], deterministic=True,
                              force_row_wise=True, n_jobs=1, **p)


def fit_verifier(base: pd.DataFrame, merchants: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    """Train one model per fold on history-window features. Returns fold models + fold map."""
    y = merchants.set_index("merchant_id").loc[base.index, "declared_category"]
    classes = sorted(y.unique())
    folds = StratifiedKFold(cfg["models"]["cv_folds"], shuffle=True, random_state=cfg["seed"])
    fold_of, models = {}, []
    for k, (tr, te) in enumerate(folds.split(base, y)):
        m = make_model(cfg, len(classes)).fit(base.iloc[tr][SHAPE], y.iloc[tr])
        models.append(m)
        fold_of.update({mid: k for mid in base.index[te]})
    return {"models": models, "fold_of": fold_of, "classes": classes}


def score_verifier(ver: dict[str, Any], feats: pd.DataFrame, declared: pd.Series) -> pd.DataFrame:
    """P(declared | behaviour) and the most likely behavioural category, per row of `feats`.

    `feats` is indexed by merchant_id (may repeat, e.g. snapshots); each row uses the
    fold model that excluded that merchant.
    """
    out = pd.DataFrame(index=feats.index)
    proba = np.zeros((len(feats), len(ver["classes"])))
    fold = feats.index.map(ver["fold_of"]).to_numpy()
    for k, m in enumerate(ver["models"]):
        rows = fold == k
        if rows.any():
            proba[rows] = m.predict_proba(feats.loc[rows, SHAPE])
    decl = declared.reindex(feats.index).to_numpy()
    ci = np.array([ver["classes"].index(c) for c in decl])
    out["verifier_p_declared"] = proba[np.arange(len(feats)), ci]
    out["verifier_mismatch"] = 1 - out["verifier_p_declared"]
    out["behaves_like"] = np.array(ver["classes"])[proba.argmax(axis=1)]
    out["behaves_like_p"] = proba.max(axis=1)
    return out
