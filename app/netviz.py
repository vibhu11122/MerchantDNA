"""Interactive ego network (pyvis) for one merchant: shared identifiers and shared payers."""
from __future__ import annotations

import networkx as nx
import pandas as pd
from pyvis.network import Network

import theme


def ego_graph_html(bundle, scores: pd.DataFrame, mid: str, hops: int = 2, show_payer: bool = True,
                   height: int = 560) -> str:
    """HTML for the merchants within `hops` links of `mid`. Thicker line = rarer shared identifier."""
    g = nx.Graph()
    g.add_edges_from(bundle.ident_graph.edges(data=True))
    if show_payer:
        for a, b, d in bundle.payer_graph.edges(data=True):
            if g.has_edge(a, b):
                g[a][b]["payer_jaccard"] = d["weight"]
            else:
                g.add_edge(a, b, weight=0.0, via=[], payer_jaccard=d["weight"])
    g.add_node(mid)
    sub = g.subgraph(nx.ego_graph(g, mid, radius=hops).nodes)

    net = Network(height=f"{height}px", width="100%", bgcolor="#120f22", font_color="#f1eefb", cdn_resources="in_line")
    net.barnes_hut(gravity=-7000, spring_length=170)
    for n in sub.nodes:
        r = scores.loc[n]
        net.add_node(n, label=f"{r['name']}\n{r['risk_score']:.0f}",
                     color={"background": theme.TIER_COLOR[r["tier"]], "border": "#ffffff" if n == mid else "#120f22"},
                     size=14 + 0.35 * r["risk_score"], borderWidth=5 if n == mid else 2,
                     title=f"{r['name']} ({n})\n{r['declared_category']}, {r['city']}\nRisk {r['risk_score']:.0f} ({r['tier']})",
                     font={"size": 18, "face": "Inter"})
    for a, b, d in sub.edges(data=True):
        if d.get("via"):
            net.add_edge(a, b, value=d["weight"], color="#8b84a8",
                         title=f"Shares {' + '.join(sorted(set(d['via'])))} (strength {d['weight']:.1f})")
        if d.get("payer_jaccard"):
            net.add_edge(a, b, value=1 + 20 * d["payer_jaccard"], color="#ec4899", dashes=True,
                         title=f"{d['payer_jaccard']:.0%} of payers in common")
    return net.generate_html().replace("<body>", '<body style="background:#120f22;margin:0">').replace(
        "border: 1px solid lightgray;", "border: none;")
