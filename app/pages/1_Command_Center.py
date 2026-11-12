"""Command Center: portfolio KPIs, risk distribution, action queue, review budget."""
from __future__ import annotations

import plotly.express as px
import streamlit as st

import data
import theme

theme.setup("Command Center", "🛰️")
theme.need_artefacts()
s, cfg = data.scores(), data.config()

st.title("🛰️ Command Center")
cap = cfg["decision"]["analyst_capacity"]
queue = s[s["in_review_queue"]]
c = st.columns(5)
c[0].metric("Merchants", f"{len(s):,}")
c[1].metric("🔴 High", int((s["tier"] == "HIGH").sum()))
c[2].metric("🟠 Medium", int((s["tier"] == "MEDIUM").sum()))
c[3].metric("🟢 Low", int((s["tier"] == "LOW").sum()))
c[4].metric("Pending investigation", f"{len(queue)} / {cap}", f"{int(s['awaiting_capacity'].sum())} waiting",
            delta_color="off")

left, right = st.columns([1.1, 1])
with left:
    st.subheader("Risk distribution")
    fig = px.histogram(s, x="risk_score", color="tier", nbins=50, log_y=True,
                       color_discrete_map=theme.TIER_COLOR, category_orders={"tier": ["LOW", "MEDIUM", "HIGH"]})
    fig.update_layout(height=380, font=dict(size=16), xaxis_title="Risk score (0-100)", yaxis_title="Merchants (log)",
                      margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Recommended actions")
    counts = s["rung"].value_counts().reindex([r[0] for r in cfg["decision"]["rungs"]], fill_value=0)
    fig = px.bar(x=counts.values, y=counts.index, orientation="h", text=counts.values)
    fig.update_layout(height=380, font=dict(size=16), xaxis_title="Merchants", yaxis_title="", margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Review budget")
st.progress(min(len(queue) / max(cap, 1), 1.0), text=f"Analyst capacity used: {len(queue)} of {cap} this cycle")

st.subheader("Action queue (highest expected benefit first)")
ev = data.evidence()
q = s[s["rung_index"] > 0].sort_values("net_benefit", ascending=False).copy()
q["top reason"] = [ev[m]["drivers"][0]["label"] if ev[m]["drivers"] else "" for m in q.index]
q["innocence check"] = q["innocence_status"]
show = q[["name", "declared_category", "city", "risk_score", "tier", "rung", "top reason", "innocence check",
          "in_review_queue"]].rename(columns={"risk_score": "risk", "in_review_queue": "in queue"})
st.dataframe(show.style.format({"risk": "{:.0f}"}), use_container_width=True, height=480)
st.caption("Signals, not proof. Every flag above has an evidence page (Merchant Deep Dive / Investigation Report).")
