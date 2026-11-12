"""Network Graph: who shares devices, bank accounts, IPs or payers with whom."""
from __future__ import annotations

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

import data
import theme

theme.setup("Network Graph")
theme.need_artefacts()
s = data.scores()
bundle = data.artifact("bundle")
ident, payer = bundle.ident_graph, bundle.payer_graph

theme.page_header("Network Graph", "Merchants are linked when they share an identifier or many payers. "
                  "<b>Thicker line = rarer shared identifier</b>: a shared device or bank account is strong, "
                  "a shared franchise GST number is weak.")
c = st.columns([2.2, 1, 1.2])
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

net = Network(height="620px", width="100%", bgcolor="#ffffff", font_color=theme.INK, cdn_resources="in_line")
net.barnes_hut(gravity=-7000, spring_length=170)
for n in sub.nodes:
    r = s.loc[n]
    net.add_node(n, label=f"{r['name']}\n{r['risk_score']:.0f}", color={"background": theme.TIER_COLOR[r["tier"]],
                 "border": theme.NAVY if n == mid else "#ffffff"}, size=14 + 0.35 * r["risk_score"],
                 borderWidth=5 if n == mid else 2,
                 title=f"{r['name']} ({n})\n{r['declared_category']}, {r['city']}\nRisk {r['risk_score']:.0f} ({r['tier']})",
                 font={"size": 18, "face": "Inter"})
for a, b, d in sub.edges(data=True):
    if d.get("via"):
        net.add_edge(a, b, value=d["weight"], color="#475569",
                     title=f"Shares {' + '.join(sorted(set(d['via'])))} (strength {d['weight']:.1f})")
    if d.get("payer_jaccard"):
        net.add_edge(a, b, value=1 + 20 * d["payer_jaccard"], color=theme.BLUE, dashes=True,
                     title=f"Shares {d['payer_jaccard']:.0%} of payers")

left, right = st.columns([1.6, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Linked merchants <span>node size and colour = risk · hover a line to see what is shared</span></div>',
                unsafe_allow_html=True)
    components.html(net.generate_html(), height=640)
    st.markdown(f'{theme.chip("HIGH", "red")}{theme.chip("MEDIUM", "amber")}{theme.chip("LOW", "green")} &nbsp; '
                f'<span style="color:{theme.MUTED};font-size:0.9rem">grey solid = shared identifier · blue dashed = shared payers</span>',
                unsafe_allow_html=True)
with right:
    with st.container(border=True):
        st.markdown(f'<div class="ptitle">What {theme.esc(s.loc[mid, "name"])} shares</div>', unsafe_allow_html=True)
        theme.bullet_list(data.evidence()[mid]["network"], "No notable links.")
    with st.container(border=True):
        st.markdown('<div class="ptitle">Most suspicious clusters <span>Louvain communities</span></div>', unsafe_allow_html=True)
        comm = s[s["community"].map(s["community"].value_counts()) > 1].groupby("community").agg(
            Merchants=("name", "size"), Mean_risk=("risk_score", "mean"), Max_risk=("risk_score", "max"),
            Members=("name", lambda x: ", ".join(x.head(4))))
        comm = comm.sort_values("Mean_risk", ascending=False).head(8).rename(columns={"Mean_risk": "Mean risk", "Max_risk": "Max risk"})
        st.dataframe(comm.style.format({"Mean risk": "{:.0f}", "Max risk": "{:.0f}"}), use_container_width=True,
                     hide_index=True, height=330)
