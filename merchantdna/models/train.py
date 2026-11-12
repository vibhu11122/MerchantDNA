"""Train every model and score every merchant: `python -m merchantdna.models.train`.

Order: website -> verifier -> DNA autoencoder -> volume model -> components today ->
fusion (analyst-labelled subset) -> scores, SHAP, actions, evidence -> weekly snapshots -> UMAP.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import umap

from merchantdna.decision.explain_step import verify_all
from merchantdna.decision.ladder import choose_rungs, tier
from merchantdna.decision.report import evidence_lines
from merchantdna.features.columns import SHAPE
from merchantdna.features.peer import cohort_key
from merchantdna.features.windows import city_tiers, window
from merchantdna.models import fusion as F
from merchantdna.models.dna_autoencoder import category_centroids, embed, fit_autoencoder
from merchantdna.models.innocence import fit_volume_model, verdict
from merchantdna.models.network import communities, identity_graph, payer_overlap_graph, strong_cases
from merchantdna.models.scoring import Bundle, components, risk
from merchantdna.models.verifier import fit_verifier
from merchantdna.models.website import fit_website, top_terms
from merchantdna.utils.config import load_config
from merchantdna.utils.io import (load_artifact, read_labels, read_merchants_for_models, read_table,
                                  save_artifact, write_json, write_table)
from merchantdna.utils.logging import Timer, get_logger

log = get_logger("train")
HEROES = ["M0000", "M0001", "M0002"]


def load_inputs(cfg: dict[str, Any]) -> dict[str, Any]:
    """Label-free inputs: merchants, calendar, feature tables, daily counts, recent txns."""
    m = read_merchants_for_models()
    m["tier"] = m["city"].map(city_tiers(cfg))
    m = m.set_index("merchant_id")
    cal = read_table("calendar")
    feats = {k: read_table(f"features_{k}", "artifacts").set_index("merchant_id")
             for k in ("baseline", "current", "snapshots")}
    tx = read_table("transactions", columns=["merchant_id", "payer_id_hash", "timestamp"])
    tx["day_idx"] = (tx["timestamp"].dt.normalize() - cal["date"].min()).dt.days
    recent = window(tx, len(cal) - 1, cfg["features"]["window_long"])
    return {"merchants": m, "calendar": cal, "daily": read_table("daily_counts", "artifacts"),
            "recent": recent, **feats}


def fit_bundle(cfg: dict[str, Any], d: dict[str, Any]) -> Bundle:
    """Fit all label-free component models."""
    m, base = d["merchants"], d["baseline"]
    cohorts = cohort_key(m)
    with Timer(log, "website classifier"):
        web_model, web_table = fit_website(m.reset_index(), cfg)
    with Timer(log, "behavioural verifier"):
        ver = fit_verifier(base, m.reset_index(), cfg)
    with Timer(log, "DNA autoencoder"):
        ae = fit_autoencoder(pd.concat([base[SHAPE], d["snapshots"][SHAPE]]), cfg)
        base_codes = pd.DataFrame(embed(ae, base), index=base.index)
        cent, spread = category_centroids(base_codes, m["declared_category"])
    with Timer(log, "expected-volume model"):
        n_days = len(d["calendar"])
        vm = fit_volume_model(d["daily"], d["calendar"], cohorts, cfg,
                              n_days - cfg["features"]["window_long"])
    with Timer(log, "graphs"):
        ident = identity_graph(m.reset_index(), cfg)
        payer = payer_overlap_graph(d["recent"], cfg)
        comm = communities(ident, cfg["seed"])
    return Bundle(cfg, m, cohorts, d["calendar"], base, web_table, web_model, ver, ae, base_codes,
                  cent, spread, vm, ident, payer, comm)


def network_findings(b: Bundle, mid: str, scores: pd.Series) -> list[str]:
    """Plain-English list of the merchant's notable identity and payer links."""
    out = []
    names = b.merchants["name"]
    for nb, e in sorted(b.ident_graph[mid].items(), key=lambda kv: -kv[1]["weight"])[:6]:
        via = sorted(set(e["via"]))
        if any(v in ("device", "bank") for v in via) or e["weight"] > 2:
            out.append(f"Shares {' + '.join(via)} with {names[nb]} ({nb}), risk {scores[nb]:.0f}/100 "
                       f"(link strength {e['weight']:.1f})")
    for nb, e in sorted(b.payer_graph[mid].items(), key=lambda kv: -kv[1]["weight"])[:3] if mid in b.payer_graph else []:
        out.append(f"Shares {e['weight']:.0%} of payers (Jaccard) with {names[nb]} ({nb}), risk {scores[nb]:.0f}/100")
    return out


def build_evidence(b: Bundle, c: dict[str, Any], feats: pd.DataFrame, scores: pd.Series,
                   rungs: pd.DataFrame, drivers: dict[str, Any]) -> dict[str, Any]:
    """Per-merchant evidence bundle for the dashboard and reports."""
    cfg = b.cfg
    stats = load_artifact("cohort_stats")["median"]
    ev_all = {}
    for mid in feats.index:
        m = b.merchants.loc[mid]
        f = feats.loc[mid]
        vol, comp = c["volume"].loc[mid], c["composition"].loc[mid]
        inn = verdict(vol, comp, m["declared_category"])
        claim_ev = {**vol.to_dict(), **f.to_dict(), "shifted": inn["shifted"],
                    "ticket_growth": (f["gmv_short"] / max(f["cnt_short"], 1))
                    / max(f["gmv_long"] / max(f["cnt_long"], 1), 1e-9)}
        web_p = b.website_table.loc[mid, "website_p_declared"]
        ev_all[mid] = {
            "merchant_id": mid, "name": m["name"], "declared_category": m["declared_category"],
            "city": m["city"], "risk_score": float(scores[mid]),
            "tier": str(tier(scores[mid], cfg)), "rung": rungs.loc[mid, "rung"],
            "behaves_like": c["verifier"].loc[mid, "behaves_like"],
            "behaves_like_p": float(c["verifier"].loc[mid, "behaves_like_p"]),
            "verifier_p_declared": float(c["verifier"].loc[mid, "verifier_p_declared"]),
            "drivers": drivers[mid],
            "evidence": evidence_lines(f, stats.loc[b.cohorts[mid]], m["city"],
                                       cfg["models"]["innocence"]["composition_z"]),
            "innocence": inn,
            "network": network_findings(b, mid, scores),
            "website": {"has_website": bool(m["has_website"]),
                        "p": None if pd.isna(web_p) else float(web_p),
                        "terms": top_terms(b.website_model, m["website_text"], m["declared_category"])
                        if m["has_website"] else []},
            "claims": verify_all(claim_ev, cfg),
        }
    return ev_all


def score_snapshots(b: Bundle, d: dict[str, Any]) -> tuple[pd.DataFrame, np.ndarray]:
    """Risk score and DNA code for every merchant at every weekly snapshot."""
    rows, codes = [], []
    for day, f in d["snapshots"].groupby("as_of_day"):
        c = components(b, f, d["daily"], int(day))
        rows.append(pd.DataFrame({"as_of_day": day, "as_of_date": f["as_of_date"].iloc[0],
                                  "risk_score": risk(b, c["x"]), "night_share": f["night_share"],
                                  "z_night_share": f["z_night_share"]}, index=f.index))
        codes.append(c["codes"])
    return pd.concat(rows), np.vstack(codes)


def main() -> None:
    """Fit, score, explain and save everything the dashboard and evaluation need."""
    cfg = load_config()
    d = load_inputs(cfg)
    b = fit_bundle(cfg, d)
    cur = d["current"]
    n_days = len(d["calendar"])
    with Timer(log, "components (today)"):
        c = components(b, cur, d["daily"], n_days - 1)
    b.refs = c["refs"]

    labels = read_labels()                                     # simulated analyst labels only
    labelled = F.select_labelled(cur.index, labels, cfg, exclude=HEROES, cases=strong_cases(b.ident_graph))
    with Timer(log, "fusion"):
        b.fusion = F.fit_fusion(c["x"].loc[labelled], labels.loc[labelled], cfg)
    scores = risk(b, c["x"])
    rungs = choose_rungs(scores / 100, cfg)
    drivers = F.explain(b.fusion, c["x"])
    del labels                                                  # nothing below may use labels

    with Timer(log, "evidence"):
        evidence = build_evidence(b, c, cur, scores, rungs, drivers)
    out = pd.DataFrame({
        "name": b.merchants["name"], "declared_category": b.declared, "city": b.merchants["city"],
        "risk_score": scores, "tier": tier(scores, cfg), "p_drift": scores / 100,
    }).join(rungs).join(c["x"]).join(c["verifier"][["behaves_like", "behaves_like_p", "verifier_p_declared"]])
    out = out.join(c["volume"][["volume_up", "volume_explained", "cold_start", "vol_ratio"]])
    out["innocence_status"] = [evidence[m]["innocence"]["status"] for m in out.index]
    out["stage1"] = c["stage1"]
    out["community"] = pd.Series(b.communities).reindex(out.index)
    out["has_website"] = b.merchants["has_website"]
    out["in_labelled_set"] = out.index.isin(labelled)

    with Timer(log, "weekly snapshots"):
        snaps, snap_codes = score_snapshots(b, d)
    with Timer(log, "UMAP"):
        reducer = umap.UMAP(n_components=2, random_state=cfg["seed"], **cfg["models"]["umap"])
        xy = reducer.fit_transform(np.vstack([b.base_codes.to_numpy(), snap_codes]))
    hist = pd.DataFrame({"as_of_day": -1, "as_of_date": d["calendar"]["date"].iloc[0],
                         "risk_score": np.nan}, index=b.base_codes.index)
    traj = pd.concat([hist, snaps[["as_of_day", "as_of_date", "risk_score"]]])
    traj["umap_x"], traj["umap_y"] = xy[:, 0], xy[:, 1]
    traj["declared_category"] = b.declared.reindex(traj.index).to_numpy()

    write_table(out.reset_index(names="merchant_id"), "scores", "artifacts")
    write_table(c["x"].reset_index(names="merchant_id"), "fusion_inputs", "artifacts")
    write_table(c["ungated"].reset_index(names="merchant_id"), "fusion_inputs_ungated", "artifacts")
    write_table(c["bands"], "volume_bands", "artifacts")
    write_table(snaps.reset_index(names="merchant_id"), "snapshot_scores", "artifacts")
    write_table(traj.reset_index(names="merchant_id"), "dna_trajectory", "artifacts")
    write_json(evidence, "evidence", "artifacts")
    write_json({"labelled": list(labelled)}, "labelled_set", "artifacts")
    save_artifact(b, "bundle")
    for h in HEROES:
        e = evidence[h]
        log.info("%s %-18s score %5.1f %-6s %s | %s", h, e["name"], e["risk_score"], e["tier"],
                 e["rung"], e["innocence"]["status"])
    log.info("tiers: %s", out["tier"].value_counts().to_dict())


if __name__ == "__main__":
    main()
