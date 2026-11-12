"""Network pillar: who shares identifiers, and who shares payers.

1. Identity graph: merchants linked by shared device / bank / IP / address / GST.
   Edge weight = attribute strength x rarity (IDF): sharing a rare device is strong
   evidence, sharing a franchise GST number is weak.
2. Payer-overlap graph: merchants linked when many of the same (hashed) payers pay both.
Risk is propagated label-free: a merchant inherits the behavioural ("stage-1")
suspicion of its neighbours, weighted by edge strength.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

ATTRS = {"device": "device_ids", "bank": "bank_account_hash", "ip": "ip_cluster",
         "address": "address_hash", "gstin": "gstin_hash"}
STRONG = ("device", "bank")


def identity_graph(merchants: pd.DataFrame, cfg: dict[str, Any]) -> nx.Graph:
    """Weighted merchant-merchant graph from shared identifiers (rarity weighted)."""
    strength = cfg["models"]["network"]["attr_strength"]
    n = len(merchants)
    g = nx.Graph()
    g.add_nodes_from(merchants["merchant_id"])
    for attr, col in ATTRS.items():
        holders: dict[str, list[str]] = defaultdict(list)
        for mid, val in zip(merchants["merchant_id"], merchants[col]):
            for v in (list(val) if attr == "device" else [val]):
                holders[v].append(mid)
        for members in holders.values():
            if len(members) < 2:
                continue
            w = strength[attr] * np.log(n / len(members))           # IDF: rarer = stronger
            for a, b in combinations(sorted(set(members)), 2):
                e = g.get_edge_data(a, b, {"weight": 0.0, "via": []})
                g.add_edge(a, b, weight=e["weight"] + w, via=e["via"] + [attr])
    return g


def payer_overlap_graph(w: pd.DataFrame, cfg: dict[str, Any]) -> nx.Graph:
    """Merchants linked when they share many payers (Jaccard on unique hashed payers)."""
    p = cfg["models"]["network"]
    pm = w[["merchant_id", "payer_id_hash"]].drop_duplicates()
    pm["merchant_id"] = pm["merchant_id"].astype(str)
    n_payers = pm.groupby("merchant_id").size()
    per_payer = pm.groupby("payer_id_hash")["merchant_id"].transform("size")
    pm = pm[(per_payer >= 2) & (per_payer <= p["payer_max_merchants_per_payer"])]
    pairs = pm.merge(pm, on="payer_id_hash")
    pairs = pairs[pairs["merchant_id_x"] < pairs["merchant_id_y"]]
    shared = pairs.groupby(["merchant_id_x", "merchant_id_y"]).size().rename("shared").reset_index()
    shared["jaccard"] = shared["shared"] / (n_payers.reindex(shared["merchant_id_x"]).to_numpy()
                                            + n_payers.reindex(shared["merchant_id_y"]).to_numpy()
                                            - shared["shared"])
    keep = shared[(shared["shared"] >= p["payer_min_shared"]) & (shared["jaccard"] >= p["payer_min_jaccard"])]
    g = nx.Graph()
    g.add_nodes_from(n_payers.index)
    g.add_weighted_edges_from(keep[["merchant_id_x", "merchant_id_y", "jaccard"]].itertuples(index=False))
    return g


def strong_cases(g: nx.Graph) -> dict[str, int]:
    """Connected groups over strong links only (shared device or bank) = one analyst case."""
    strong = nx.Graph()
    strong.add_nodes_from(g.nodes)
    strong.add_edges_from((a, b) for a, b, d in g.edges(data=True) if any(v in STRONG for v in d["via"]))
    return {m: i for i, comp in enumerate(nx.connected_components(strong)) for m in comp}


def communities(g: nx.Graph, seed: int) -> dict[str, int]:
    """Louvain community id per merchant."""
    comms = nx.community.louvain_communities(g, weight="weight", seed=seed)
    return {m: i for i, c in enumerate(comms) for m in c}


def _neighbour_risk(g: nx.Graph, stage1: pd.Series, prior: float) -> pd.Series:
    """Edge-weighted mean of neighbours' stage-1 risk, shrunk towards 0 for weak ties."""
    vals = {}
    for m in g.nodes:
        nb = g[m]
        if not nb:
            vals[m] = 0.0
            continue
        w = np.array([d["weight"] for d in nb.values()])
        r = stage1.reindex(list(nb)).fillna(0).to_numpy()
        vals[m] = float((w * r).sum() / (w.sum() + prior))         # prior = weight on "no risk"
    return pd.Series(vals)


def network_features(ident: nx.Graph, payer: nx.Graph, comm: dict[str, int],
                     stage1: pd.Series, cfg: dict[str, Any]) -> pd.DataFrame:
    """Per-merchant network signals."""
    p = cfg["models"]["network"]
    idx = stage1.index
    q = p["propagate_above_pct"]
    stage1 = ((stage1 - q) / (1 - q)).clip(lower=0)            # typical merchants pass on nothing
    out = pd.DataFrame(index=idx)
    out["identity_neighbor_risk"] = _neighbour_risk(ident, stage1, p["identity_prior_weight"]).reindex(idx).fillna(0)
    out["strong_link_count"] = [sum(any(v in STRONG for v in d["via"]) for d in ident[m].values())
                                if m in ident else 0 for m in idx]
    comm_s = pd.Series(comm).reindex(idx)
    size = comm_s.map(comm_s.value_counts())
    total = stage1.groupby(comm_s).transform("sum")
    out["community_risk"] = ((total - stage1) / (size - 1).clip(lower=1)).where(size > 1, 0.0)
    out["community_size"] = size.fillna(1).astype(int)
    out["payer_overlap_degree"] = [payer.degree(m) if m in payer else 0 for m in idx]
    out["payer_neighbor_risk"] = _neighbour_risk(payer, stage1, p["payer_prior_weight"]).reindex(idx).fillna(0)
    return out
