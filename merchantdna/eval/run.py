"""Evaluate MerchantDNA vs baselines: `python -m merchantdna.eval.run`.

Everything is measured on merchants OUTSIDE the analyst-labelled training subset.
Writes reports/metrics.json and reports/*.png (the dashboard only reads these).
"""
from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from merchantdna.eval.ablation import ablation_scores  # noqa: E402
from merchantdna.eval.baselines import fit_iforest, iforest_score, rules_score  # noqa: E402
from merchantdna.eval.metrics import budget_flags, flag_metrics, pr_auc_ci, pr_curve  # noqa: E402
from merchantdna.utils.config import load_config, path_for  # noqa: E402
from merchantdna.utils.io import read_json, read_table, write_json  # noqa: E402
from merchantdna.utils.logging import get_logger  # noqa: E402

log = get_logger("eval")
HEROES = ["M0000", "M0001", "M0002"]


def method_block(y: pd.Series, s: pd.Series, native: pd.Series, surge: pd.Series,
                 cfg: dict[str, Any]) -> dict[str, Any]:
    """All headline metrics for one method's scores on the evaluation set."""
    e = cfg["eval"]
    return {**pr_auc_ci(y, s, seed=cfg["seed"]),
            "at_review_budget": flag_metrics(y, budget_flags(s, e["review_budget"]), surge),
            "at_5pct_budget": flag_metrics(y, budget_flags(s, 0.05), surge),
            "at_native_threshold": flag_metrics(y, native, surge)}


def lead_times(snap: pd.DataFrame, feats_snap: pd.DataFrame, ids: list[str], iforest,
               cfg: dict[str, Any]) -> dict[str, Any]:
    """Days by which MerchantDNA flags slow-drift merchants before each baseline does."""
    medium = cfg["decision"]["tiers"]["medium"]
    rows = []
    for mid in ids:
        s = snap[snap["merchant_id"] == mid].sort_values("as_of_day").set_index("as_of_day")
        f = feats_snap.loc[[mid]].set_index("as_of_day")
        ours = s.index[s["risk_score"] >= medium]
        rule = f.index[rules_score(f, cfg)[1].to_numpy()]
        iso = f.index[iforest_score(iforest, f)[1].to_numpy()]
        end = int(s.index.max())
        first = lambda idx: int(idx.min()) if len(idx) else None  # noqa: E731
        rows.append({"merchant_id": mid, "merchantdna_day": first(ours), "rules_day": first(rule),
                     "iforest_day": first(iso), "last_day": end})
    df = pd.DataFrame(rows)

    def lead(col: str) -> float:
        d = df.dropna(subset=["merchantdna_day"])
        never = d["last_day"] + cfg["features"]["snapshot_every"]           # never flagged = after the end
        other = d[col].astype(float).where(d[col].notna(), never)
        return float((other - d["merchantdna_day"]).median()) if len(d) else float("nan")

    return {"per_merchant": df.to_dict(orient="records"),
            "detected_by_merchantdna": int(df["merchantdna_day"].notna().sum()), "n": len(df),
            "median_lead_vs_rules_days": lead("rules_day"),
            "median_lead_vs_iforest_days": lead("iforest_day")}


def plots(curves: dict[str, Any], abl: dict[str, Any], scores: pd.DataFrame, out) -> None:
    """PR curves, ablation bars and score distribution by archetype."""
    plt.rcParams.update({"font.size": 13})
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for name, c in curves.items():
        ax.plot(c["recall"], c["precision"], label=name, lw=2.5)
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision"); ax.set_title("Precision-recall (held-out merchants)")
    ax.legend(); ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig(out / "pr_curves.png", dpi=120); plt.close(fig)

    names = list(abl)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    axes[0].bar(names, [abl[n]["pr_auc"] for n in names], color="#2b6cb0")
    axes[0].set_title("PR-AUC"); axes[0].set_ylim(0, 1)
    axes[1].bar(names, [abl[n]["at_native_threshold"]["surge_fpr"] for n in names], color="#c05621")
    axes[1].set_title("False-positive rate on festival-surge merchants")
    for ax in axes:
        ax.tick_params(axis="x", rotation=20)
    fig.tight_layout(); fig.savefig(out / "ablation.png", dpi=120); plt.close(fig)

    order = scores.groupby("archetype")["risk_score"].median().sort_values().index
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.boxplot([scores.loc[scores["archetype"] == a, "risk_score"] for a in order], vert=False)
    ax.set_yticklabels(order); ax.set_xlabel("Risk score (0-100)"); ax.set_title("Risk score by archetype")
    fig.tight_layout(); fig.savefig(out / "score_by_archetype.png", dpi=120); plt.close(fig)


def main() -> None:
    """Compute and save every evaluation number."""
    cfg = load_config()
    truth = read_table("merchants", columns=["merchant_id", "label", "archetype"]).set_index("merchant_id")
    scores = read_table("scores", "artifacts").set_index("merchant_id").join(truth)
    feats = read_table("features_current", "artifacts").set_index("merchant_id")
    labelled = pd.Index(read_json("labelled_set", "artifacts")["labelled"])
    ev = scores.index.difference(labelled)
    y, surge = scores.loc[ev, "label"], scores.loc[ev, "archetype"] == "festival_surge"
    medium = cfg["decision"]["tiers"]["medium"]

    r_s, r_f = rules_score(feats, cfg)
    iforest = fit_iforest(feats, cfg)
    i_s, i_f = iforest_score(iforest, feats)
    ours = scores["risk_score"]
    explained = scores["volume_explained"].astype(bool)
    g_s, g_f = rules_score(feats.assign(vol_ratio_hist=feats["vol_ratio_hist"].where(~explained, 1.0)), cfg)
    methods = {
        "static_rules": method_block(y, r_s[ev], r_f[ev], surge, cfg),
        "static_rules_plus_innocence_gate": method_block(y, g_s[ev], g_f[ev], surge, cfg),
        "isolation_forest": method_block(y, i_s[ev], i_f[ev], surge, cfg),
        "merchantdna": method_block(y, ours[ev], ours[ev] >= medium, surge, cfg),
    }
    curves = {"Static rules": pr_curve(y, r_s[ev]), "Isolation Forest": pr_curve(y, i_s[ev]),
              "MerchantDNA": pr_curve(y, ours[ev])}

    x = read_table("fusion_inputs", "artifacts").set_index("merchant_id")
    xu = read_table("fusion_inputs_ungated", "artifacts").set_index("merchant_id")
    abl_scores = ablation_scores(x, xu, truth["label"], labelled, cfg)
    abl = {k: {**method_block(y, s[ev], s[ev] >= medium, surge, cfg),
               "hero_scores": {m: float(s[m]) for m in HEROES}} for k, s in abl_scores.items()}

    mimic = ev[scores.loc[ev, "archetype"] == "adaptive_mimic"]
    k = budget_flags(ours[ev], cfg["eval"]["review_budget"])
    stress = {"n_adaptive_mimic_in_eval": len(mimic),
              "recall_at_medium_tier": float((ours[mimic] >= medium).mean()) if len(mimic) else None,
              "recall_in_review_budget": float(k[mimic].mean()) if len(mimic) else None,
              "recall_isolation_forest_native": float(i_f[mimic].mean()) if len(mimic) else None,
              "recall_static_rules_native": float(r_f[mimic].mean()) if len(mimic) else None}

    snap = read_table("snapshot_scores", "artifacts")
    fsnap = read_table("features_snapshots", "artifacts").set_index("merchant_id")
    drift_ids = [m for m in ev if truth.loc[m, "archetype"] == "slow_drift"] + ["M0001"]
    lead = lead_times(snap, fsnap, drift_ids, iforest, cfg)

    se = scores.loc[ev].assign(flag=scores.loc[ev, "risk_score"] >= medium)
    per_arch = se.groupby("archetype").agg(n=("flag", "size"), flagged_medium_or_high=("flag", "mean"),
                                           median_score=("risk_score", "median")).to_dict(orient="index")
    metrics = {
        "dataset": {"merchants": len(scores), "fraud": int(truth["label"].sum()),
                    "labelled_for_training": len(labelled), "evaluated": len(ev),
                    "fraud_in_eval": int(y.sum()), "surge_merchants_in_eval": int(surge.sum()),
                    "review_budget_share": cfg["eval"]["review_budget"]},
        "methods": methods, "ablations": abl, "stress_test_adaptive_mimic": stress,
        "slow_drift_lead_time": lead, "per_archetype": per_arch,
        "heroes": {m: {"risk_score": float(scores.loc[m, "risk_score"]), "tier": scores.loc[m, "tier"],
                       "rung": scores.loc[m, "rung"]} for m in HEROES},
        "pr_curves": curves,
    }
    write_json(metrics, "metrics")
    plots(curves, abl, scores, path_for("reports"))
    for name, mb in methods.items():
        log.info("%-33s PR-AUC %.3f [%.3f-%.3f] | budget recall %.2f prec %.2f | surge FPR native %.3f",
                 name, mb["pr_auc"], mb["pr_auc_lo"], mb["pr_auc_hi"], mb["at_review_budget"]["recall"],
                 mb["at_review_budget"]["precision"], mb["at_native_threshold"]["surge_fpr"])
    for name, mb in abl.items():
        log.info("ablation %-20s PR-AUC %.3f surge FPR %.3f heroes %s", name, mb["pr_auc"],
                 mb["at_native_threshold"]["surge_fpr"], {k: round(v, 1) for k, v in mb["hero_scores"].items()})
    log.info("adaptive mimic: %s", stress)
    log.info("slow drift lead: vs rules %.0f d, vs iforest %.0f d (%d/%d detected)",
             lead["median_lead_vs_rules_days"], lead["median_lead_vs_iforest_days"],
             lead["detected_by_merchantdna"], lead["n"])


if __name__ == "__main__":
    main()
