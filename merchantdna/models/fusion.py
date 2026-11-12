"""Fusion: combine all component scores into one calibrated P(purpose drift).

A shallow gradient-boosted stacker (depth 2, every input constrained so that "more
anomalous" can only raise risk) is trained on a small analyst-labelled subset,
calibrated on out-of-fold predictions (sigmoid by default, isotonic optional), then
corrected from the labelled sample's fraud rate to the population prior. SHAP explains
every score.
"""
from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold

CLAIMED = ["website_mismatch"]
BEHAVIOUR = ["verifier_mismatch", "dna_drift_self", "dna_drift_cat", "dna_recon_error"]
COMPOSITION = ["comp_hours_self_z", "comp_hours_peer_z", "comp_amounts_self_z", "comp_amounts_peer_z",
               "comp_payers_self_z", "comp_payers_peer_z"]
PATTERN = ["z_pricepoint_share", "z_night_share", "z_post_wicket_lift", "z_ipl_evening_lift",
           "z_burst_index", "z_fast_payout_share"]
PAYER = ["z_repeat_txn_share", "z_multi_city_payer_share", "z_nonlocal_share"]
VOLUME = ["z_cnt_short", "z_vol_ratio_hist", "z_growth_short_vs_long", "z_daily_fano", "exceed_rate"]
NETWORK = ["identity_neighbor_risk", "strong_link_count", "community_risk", "payer_overlap_degree",
           "payer_neighbor_risk"]
ALL = CLAIMED + BEHAVIOUR + COMPOSITION + PATTERN + PAYER + VOLUME + NETWORK

# Label-free behavioural suspicion used to propagate risk over the network graphs.
STAGE1 = BEHAVIOUR + COMPOSITION + PATTERN + PAYER + CLAIMED

PAYER_DERIVED = PAYER + ["comp_payers_self_z", "comp_payers_peer_z", "payer_overlap_degree",
                         "payer_neighbor_risk"]

PLAIN = {
    "website_mismatch": "Website text does not match the declared category",
    "verifier_mismatch": "Does not behave like its declared category",
    "dna_drift_self": "Business DNA moved away from its own history",
    "dna_drift_cat": "Business DNA is far from its category's typical DNA",
    "dna_recon_error": "Unusual overall behaviour pattern",
    "comp_hours_self_z": "Trading hours changed vs its own history",
    "comp_hours_peer_z": "Trading hours differ from peers",
    "comp_amounts_self_z": "Amount mix changed vs its own history",
    "comp_amounts_peer_z": "Amount mix differs from peers",
    "comp_payers_self_z": "Payer geography changed vs its own history",
    "comp_payers_peer_z": "Payer geography differs from peers",
    "z_pricepoint_share": "Many payments at exactly 499 / 999 / 1999",
    "z_night_share": "High share of night-time (00-05) payments",
    "z_post_wicket_lift": "Payments spike minutes after cricket wickets",
    "z_ipl_evening_lift": "Busier on match evenings",
    "z_burst_index": "Payments arrive in tight bursts",
    "z_fast_payout_share": "Takes fast (same-day) payouts",
    "z_repeat_txn_share": "Same payers pay again and again",
    "z_multi_city_payer_share": "Payers also pay merchants in many other cities",
    "z_nonlocal_share": "Most payers are from other cities",
    "z_cnt_short": "Higher recent transaction count than peers",
    "z_vol_ratio_hist": "Volume up vs its own history",
    "z_growth_short_vs_long": "Sharp growth in the last week",
    "z_daily_fano": "Very uneven day-to-day volume",
    "exceed_rate": "Days above the expected volume range",
    "identity_neighbor_risk": "Shares device / bank / IP with suspicious merchants",
    "strong_link_count": "Shares a device or bank account with other merchants",
    "community_risk": "Belongs to a suspicious cluster of linked merchants",
    "payer_overlap_degree": "Shares many payers with other merchants",
    "payer_neighbor_risk": "Shares payers with suspicious merchants",
}


def gate(x: pd.DataFrame, volume_explained: pd.Series) -> pd.DataFrame:
    """Innocence gate: if volume is explained, set ONLY the volume inputs to neutral (0)."""
    x = x.copy()
    explained = volume_explained.reindex(x.index).fillna(False).to_numpy(bool)
    for c in VOLUME:
        x.loc[explained, c] = 0.0
    return x


def stage1_score(x: pd.DataFrame, ref: dict[str, np.ndarray] | None = None
                 ) -> tuple[pd.Series, dict[str, np.ndarray]]:
    """Label-free behavioural suspicion as a population percentile (0..1).

    Step 1: percentile rank of each behavioural input; step 2: average them;
    step 3: percentile of that average. `ref` holds the sorted population values
    so a single merchant can be ranked on its own.
    """
    if ref is None:
        ref = {c: np.sort(x[c].to_numpy()) for c in STAGE1}
    ranks = np.column_stack([np.searchsorted(ref[c], x[c].to_numpy(), side="right") / len(ref[c])
                             for c in STAGE1])
    mean_rank = ranks.mean(axis=1)
    if "_mean" not in ref:
        ref = {**ref, "_mean": np.sort(mean_rank)}
    pct = np.searchsorted(ref["_mean"], mean_rank, side="right") / len(ref["_mean"])
    return pd.Series(pct, index=x.index), ref


def select_labelled(ids: pd.Index, labels: pd.Series, cfg: dict[str, Any], exclude: list[str],
                    cases: dict[str, int] | None = None) -> pd.Index:
    """Simulate an analyst-reviewed subset: ~10% of merchants, enriched in fraud.

    Analysts work in cases: when a reviewed merchant turns out to be fraud and is
    strongly linked (shared device / bank) to others, the whole linked case is
    reviewed and labelled together. `cases` maps merchant -> case id (label-free).
    """
    p = cfg["models"]["fusion"]
    rng = np.random.default_rng(cfg["seed"])
    pool = labels.reindex(ids).drop(exclude, errors="ignore")
    n = int(round(p["labelled_share"] * len(ids)))
    n_fraud = min(int(round(p["labelled_fraud_share"] * n)), int(pool.sum()) // 2)
    chosen: list[str] = []
    for mid in rng.permutation(np.sort(pool.index[pool == 1])):
        if len(chosen) >= n_fraud:
            break
        if mid in chosen:
            continue
        case = [mid] if cases is None else sorted(m for m, c in cases.items() if c == cases.get(mid))
        chosen += [m for m in case if m in pool.index and m not in chosen]
    legit = rng.choice(np.sort(pool.index[(pool == 0) & ~pool.index.isin(chosen)]), n - len(chosen),
                       replace=False)
    return pd.Index(sorted(np.concatenate([chosen, legit])))       # sorted: run-to-run stable


def _model(cfg: dict[str, Any], cols: list[str]) -> lgb.LGBMClassifier:
    p = cfg["models"]["fusion"]
    return lgb.LGBMClassifier(n_estimators=p["n_estimators"], learning_rate=p["learning_rate"],
                              max_depth=p["max_depth"], num_leaves=2 ** p["max_depth"],
                              min_child_samples=p["min_child_samples"], reg_lambda=p["reg_lambda"],
                              colsample_bytree=p["colsample_bytree"], subsample=p["subsample"],
                              subsample_freq=1, monotone_constraints=[1] * len(cols),
                              random_state=cfg["seed"], verbose=-1, deterministic=True,
                              force_row_wise=True, n_jobs=1)


def fit_fusion(x: pd.DataFrame, y: pd.Series, cfg: dict[str, Any], cols: list[str] | None = None
               ) -> dict[str, Any]:
    """Stacker + calibration on out-of-fold raw scores + prior correction."""
    cols = cols or ALL
    folds = StratifiedKFold(cfg["models"]["cv_folds"], shuffle=True, random_state=cfg["seed"])
    oof = np.zeros(len(x))
    for tr, te in folds.split(x, y):
        m = _model(cfg, cols).fit(x.iloc[tr][cols], y.iloc[tr])
        oof[te] = m.predict(x.iloc[te][cols], raw_score=True)       # log-odds
    if cfg["models"]["fusion"]["calibration"] == "isotonic":
        cal = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99).fit(oof, y)
    else:
        cal = LogisticRegression().fit(oof[:, None], y)                # Platt scaling
    model = _model(cfg, cols).fit(x[cols], y)
    return {"model": model, "calibrator": cal, "cols": cols, "sample_prior": float(y.mean()),
            "population_prior": cfg["models"]["fusion"]["population_prior"],
            "oof_raw": oof, "oof_y": y.to_numpy()}


def _calibrate(fm: dict[str, Any], raw: np.ndarray) -> np.ndarray:
    cal = fm["calibrator"]
    if isinstance(cal, IsotonicRegression):
        return cal.predict(raw)
    return cal.predict_proba(raw[:, None])[:, 1]


def predict_fusion(fm: dict[str, Any], x: pd.DataFrame) -> pd.Series:
    """Calibrated, prior-corrected P(purpose drift)."""
    raw = fm["model"].predict(x[fm["cols"]], raw_score=True)
    p = np.clip(_calibrate(fm, raw), 0.001, 0.999)
    s, t = fm["sample_prior"], fm["population_prior"]
    odds = p / (1 - p) * (t / (1 - t)) / (s / (1 - s))              # Bayes prior shift
    return pd.Series(odds / (1 + odds), index=x.index)


def explain(fm: dict[str, Any], x: pd.DataFrame, top: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Top SHAP drivers per merchant (log-odds contribution), in plain English."""
    sv = shap.TreeExplainer(fm["model"]).shap_values(x[fm["cols"]])
    sv = sv[1] if isinstance(sv, list) else sv
    out = {}
    for i, mid in enumerate(x.index):
        order = np.argsort(-np.abs(sv[i]))[:top]
        out[mid] = [{"feature": fm["cols"][j], "label": PLAIN.get(fm["cols"][j], fm["cols"][j]),
                     "value": float(x.iloc[i][fm["cols"][j]]), "contribution": float(sv[i][j])}
                    for j in order if abs(sv[i][j]) > 1e-6]
    return out
