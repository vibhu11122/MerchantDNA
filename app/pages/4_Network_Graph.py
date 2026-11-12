"""Network Graph: who shares devices, bank accounts, IPs or payers with whom."""
from __future__ import annotations

import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

import data
import theme

theme.setup("Network Graph", "🕸️")
theme.need_artefacts()
s = data.scores()
bundle = data.artifact("bundle")
ident, payer = bundle.ident_graph, bundle.payer_graph

st.title("🕸️ Network Graph")
st.markdown("Merchants are linked when they share an identifier or many payers. **Thicker line = rarer shared "
            "identifier** (a shared device or bank account is strong, a shared franchise GST number is weak).")
c = st.columns([2, 1, 1])
with c[0]:
    mid = theme.merchant_picker(s, "net", default="M0002")
hops = c[1].radio("Hops", [1, 2], index=1, horizontal=True)
show_payer = c[2].toggle("Show shared-payer links", value=True)

g = nx.Graph()
g.add_edges_from(ident.edges(data=True))
if show_payer:
    for a, b, d in payer.edges(data=True):
        if g.has_edge(a, b):
            g[a][b]["payer_jaccard"] = d["weight"]
        else:
            g.add_edge(a, b, weight=0.0, via=[], payer_jaccard=d["weight"])
g.add_node(mid)
sub = g.subgraph(nx.ego_graph(g, mid, radius=hops).nodes)

net = Network(height="650px", width="100%", bgcolor="#ffffff", font_color="#111827", cdn_resources="in_line")
net.barnes_hut(gravity=-6000, spring_length=160)
for n in sub.nodes:
    r = s.loc[n]
    net.add_node(n, label=f"{r['name']}\n{r['risk_score']:.0f}", color=theme.TIER_COLOR[r["tier"]],
                 size=14 + 0.35 * r["risk_score"], borderWidth=5 if n == mid else 1,
                 title=f"{r['name']} ({n})\n{r['declared_category']}, {r['city']}\nRisk {r['risk_score']:.0f} ({r['tier']})",
                 font={"size": 20})
for a, b, d in sub.edges(data=True):
    if d.get("via"):
        net.add_edge(a, b, value=d["weight"], color="#374151",
                     title=f"Shares {' + '.join(sorted(set(d['via'])))} (strength {d['weight']:.1f})")
    if d.get("payer_jaccard"):
        net.add_edge(a, b, value=1 + 20 * d["payer_jaccard"], color="#2563eb", dashes=True,
                     title=f"Shares {d['payer_jaccard']:.0%} of payers")
components.html(net.generate_html(), height=680)
st.caption("Red = high, orange = medium, green = low risk; node label = risk score. Grey solid = shared identifier, "
           "blue dashed = shared payers. Hover a line to see what is shared.")

st.subheader(f"What {s.loc[mid, 'name']} shares")
for line in data.evidence()[mid]["network"] or ["No notable links."]:
    st.markdown(f"- {line}")

st.subheader("Most suspicious linked clusters (Louvain communities)")
comm = s[s["community"].map(s["community"].value_counts()) > 1].groupby("community").agg(
    merchants=("name", "size"), mean_risk=("risk_score", "mean"), max_risk=("risk_score", "max"),
    members=("name", lambda x: ", ".join(x.head(6))))
st.dataframe(comm.sort_values("mean_risk", ascending=False).head(10).style.format(
    {"mean_risk": "{:.0f}", "max_risk": "{:.0f}"}), use_container_width=True)
