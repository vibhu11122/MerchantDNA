"""Claimed profile: does the website text read like the declared category?

TF-IDF + logistic regression, trained to predict declared category from text.
Out-of-fold probabilities so no merchant is scored by a model that saw its own text.
Merchants without a website get a neutral value (no penalty).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline, make_pipeline


def make_model(cfg: dict[str, Any]) -> Pipeline:
    """Word + bigram TF-IDF into a multinomial logistic regression."""
    p = cfg["models"]["website"]
    return make_pipeline(TfidfVectorizer(ngram_range=(1, 2), max_features=p["max_features"]),
                         LogisticRegression(C=p["C"], max_iter=2000))


def fit_website(merchants: pd.DataFrame, cfg: dict[str, Any]) -> tuple[Pipeline, pd.DataFrame]:
    """Return (model fitted on all websites, per-merchant P(declared | text) and mismatch)."""
    has = merchants["has_website"].to_numpy()
    text = merchants.loc[has, "website_text"]
    y = merchants.loc[has, "declared_category"]
    model = make_model(cfg)
    folds = StratifiedKFold(cfg["models"]["cv_folds"], shuffle=True, random_state=cfg["seed"])
    proba = cross_val_predict(model, text, y, cv=folds, method="predict_proba")
    classes = np.sort(y.unique())
    p_declared = proba[np.arange(len(y)), np.searchsorted(classes, y.to_numpy())]
    model.fit(text, y)

    out = pd.DataFrame(index=merchants["merchant_id"])
    out["website_p_declared"] = np.nan
    out.loc[merchants.loc[has, "merchant_id"], "website_p_declared"] = p_declared
    out["website_mismatch"] = 1 - out["website_p_declared"]
    neutral = out["website_mismatch"].median()                       # no website = no evidence
    out["website_mismatch"] = out["website_mismatch"].fillna(neutral)
    return model, out


def top_terms(model: Pipeline, text: str, category: str, k: int = 5) -> list[str]:
    """Words in `text` that pull hardest AWAY from the declared category (for the report)."""
    vec, lr = model.named_steps["tfidfvectorizer"], model.named_steps["logisticregression"]
    x = vec.transform([text])
    ci = list(lr.classes_).index(category)
    contrib = x.multiply(lr.coef_[ci]).toarray().ravel()
    idx = [i for i in np.argsort(contrib) if contrib[i] < 0][:k]
    names = vec.get_feature_names_out()
    return [names[i] for i in idx]
