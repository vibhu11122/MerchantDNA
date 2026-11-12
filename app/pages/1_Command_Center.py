"""Command Center: portfolio KPIs, risk distribution, action queue, review budget."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

import data
import theme

theme.setup("Command Center")
theme.need_artefacts()
s, cfg = data.scores(), data.config()
cap = cfg["decision"]["analyst_capacity"]
queue = s[s["in_review_queue"]]

theme.page_header("Command Center", "Portfolio view: how much risk is in the book, what the system recommends, "
                  "and what analysts can get through this cycle.")
theme.kpis([
    {"label": "Merchants", "value": f"{len(s):,}", "tone": "blue"},
    {"label": "High risk", "value": int((s["tier"] == "HIGH").sum()), "sub": "score ≥ 50", "tone": "red"},
    {"label": "Medium risk", "value": int((s["tier"] == "MEDIUM").sum()), "sub": "15 – 49", "tone": "amber"},
    {"label": "Low risk", "value": int((s["tier"] == "LOW").sum()), "sub": "below 15", "tone": "green"},
    {"label": "In review queue", "value": f"{len(queue)} / {cap}", "sub": f"{int(s['awaiting_capacity'].sum())} waiting for capacity",
     "tone": "violet"},
])

left, right = st.columns([1.15, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Risk distribution <span>log scale</span></div>', unsafe_allow_html=True)
    fig = px.histogram(s, x="risk_score", color="tier", nbins=50, log_y=True, color_discrete_map=theme.TIER_COLOR,
                       category_orders={"tier": ["LOW", "MEDIUM", "HIGH"]})
    fig.update_traces(marker_line_width=0)
    fig.update_layout(height=340, xaxis_title="Risk score (0–100)", yaxis_title="Merchants", bargap=0.08,
                      legend_title_text="")
    st.plotly_chart(fig, use_container_width=True, theme=None)
with right, st.container(border=True):
    st.markdown('<div class="ptitle">Recommended actions <span>expected-cost ladder</span></div>', unsafe_allow_html=True)
    order = [r[0] for r in cfg["decision"]["rungs"]]
    counts = s["rung"].value_counts().reindex(order, fill_value=0)
    fig = px.bar(x=counts.values, y=[o.split(" (")[0] for o in order], orientation="h", text=counts.values)
    fig.update_traces(marker_color=[theme.MUTED, theme.TONE["amber"], "#ea580c", "#dc2626", "#7f1d1d"],
                      marker_cornerradius=6, textposition="outside", cliponaxis=False)
    fig.update_layout(height=340, xaxis_title="Merchants", yaxis_title="", yaxis=dict(autorange="reversed"),
                      xaxis=dict(range=[0, counts.max() * 1.18]))
    st.plotly_chart(fig, use_container_width=True, theme=None)

with st.container(border=True):
    st.markdown('<div class="ptitle">Review budget</div>', unsafe_allow_html=True)
    theme.budget_bar(len(queue), cap)
    st.caption("Merchants are queued by expected net benefit; the rest wait for the next cycle.")

theme.section("Action queue", "highest expected benefit first · every row has an evidence page")
ev = data.evidence()
q = s[s["rung_index"] > 0].sort_values("net_benefit", ascending=False).copy()
q["top reason"] = [ev[m]["drivers"][0]["label"] if ev[m]["drivers"] else "" for m in q.index]
show = q[["name", "declared_category", "city", "risk_score", "tier", "rung", "top reason", "innocence_status",
          "in_review_queue"]].rename(columns={
    "name": "Merchant", "declared_category": "Declared", "city": "City", "risk_score": "Risk", "tier": "Tier",
    "rung": "Recommended action", "top reason": "Top reason", "innocence_status": "Innocence check",
    "in_review_queue": "In queue"})
show["Declared"] = show["Declared"].str.replace("_", " ")
st.dataframe(theme.style_table(show, {"Risk": "{:.0f}"}, tier_col="Tier"), use_container_width=True, height=520,
             column_config={"Risk": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d"),
                            "In queue": st.column_config.CheckboxColumn("In queue")})
