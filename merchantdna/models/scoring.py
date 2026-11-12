"""Turn a window's features into component scores and a final risk score.

The same function scores (1) the whole population as of today, (2) every weekly
snapshot (for trajectories and lead time) and (3) a single edited merchant in the app.
For (3) the population reference statistics computed in (1) are passed in as `refs`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import pandas as pd

from merchantdna.models import fusion as F
from merchantdna.models.dna_autoencoder import drift_scores
from merchantdna.models.innocence import composition_tests, volume_bands, volume_verdict
from merchantdna.models.network import network_features
from merchantdna.models.verifier import score_verifier


@dataclass
class Bundle:
    """Every fitted model and reference table needed to score."""
    cfg: dict[str, Any]
    merchants: pd.DataFrame          # label-free merchant table, indexed by merchant_id
    cohorts: pd.Series               # merchant_id -> "category|tier"
    calendar: pd.DataFrame
    base: pd.DataFrame               # history-window features
    website_table: pd.DataFrame
    website_model: Any
    verifier: dict[str, Any]
    ae: dict[str, Any]
    base_codes: pd.DataFrame
    centroids: pd.DataFrame
    spread: pd.Series
    volume_model: dict[str, Any]
    ident_graph: nx.Graph
    payer_graph: nx.Graph
    communities: dict[str, int]
    fusion: dict[str, Any] | None = None
    refs: dict[str, Any] = field(default_factory=dict)   # population refs as of today

    @property
    def declared(self) -> pd.Series:
        return self.merchants["declared_category"]


def components(b: Bundle, feats: pd.DataFrame, daily: pd.DataFrame, as_of_day: int,
               refs: dict[str, Any] | None = None) -> dict[str, Any]:
    """All component scores for the rows of `feats` (indexed by merchant_id).

    Returns a dict with the fusion input table `x` (gated), the ungated table, the
    innocence pieces (volume verdict, composition, daily bands), DNA codes and refs.
    """
    cfg = b.cfg
    single = refs is not None
    refs = refs or {}
    ver = score_verifier(b.verifier, feats, b.declared)
    drift, codes = drift_scores(b.ae, feats, b.base_codes, b.centroids, b.spread, b.declared)
    comp, comp_ref = composition_tests(feats, b.base, b.cohorts, cfg, refs.get("composition"))
    bands, peers = volume_bands(b.volume_model, daily, b.calendar, b.cohorts, cfg, as_of_day,
                                refs.get("peers"))
    vol = volume_verdict(bands, feats, cfg)

    z_cols = [c for c in F.ALL if c.startswith("z_")]
    x = pd.concat([b.website_table[["website_mismatch"]].reindex(feats.index),
                   ver[["verifier_mismatch"]], drift, comp[[c for c in F.COMPOSITION]],
                   feats[z_cols], vol[["exceed_rate"]]], axis=1)
    ungated = x.copy()
    x = F.gate(x, vol["volume_explained"])
    stage1, s1_ref = F.stage1_score(x, refs.get("stage1"))
    if single:
        net = refs["network"].reindex(feats.index)
    else:
        net = network_features(b.ident_graph, b.payer_graph, b.communities, stage1, cfg)
    x = pd.concat([x, net[F.NETWORK]], axis=1)
    ungated = pd.concat([ungated, net[F.NETWORK]], axis=1)
    return {"x": x, "ungated": ungated, "verifier": ver, "drift": drift, "codes": codes,
            "composition": comp, "volume": vol, "bands": bands, "stage1": stage1, "network": net,
            "refs": {"composition": comp_ref, "peers": peers, "stage1": s1_ref, "network": net}}


def risk(b: Bundle, x: pd.DataFrame) -> pd.Series:
    """0-100 risk score from the fitted fusion model."""
    return 100 * F.predict_fusion(b.fusion, x)
