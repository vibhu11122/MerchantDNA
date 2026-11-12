"""Merchant Deep Dive: claimed vs actual behaviour, with every score's reasons."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data
import theme

theme.setup("Merchant Deep Dive", "🔎")
theme.need_artefacts()
s, ev_all, cfg = data.scores(), data.evidence(), data.config()

st.title("🔎 Merchant Deep Dive")
mid = theme.merchant_picker(s, "dd")
r, ev = s.loc[mid], ev_all[mid]
feats = data.table("features_current").set_index("merchant_id")
cohort = (feats.join(s[["declared_category"]]).query("declared_category == @r.declared_category"))

st.markdown(f"## {r['name']} &nbsp; {theme.tier_badge(r['tier'])}", unsafe_allow_html=True)
c = st.columns(4)
c[0].metric("Risk score", f"{r['risk_score']:.0f} / 100")
c[1].metric("Declared category", r["declared_category"].replace("_", " "))
c[2].metric("Behaves like", ev["behaves_like"].replace("_", " "), f"P = {ev['behaves_like_p']:.0%}", delta_color="off")
c[3].metric("DNA drift vs own history", f"{r['dna_drift_self']:.1f}x", "typical for its category = 1x", delta_color="off")
st.markdown(f"**Recommended action:** {r['rung']} &nbsp;·&nbsp; **City:** {r['city']}")

left, right = st.columns([1, 1])
with left:
    st.subheader("Why this score")
    st.plotly_chart(theme.drivers_chart(ev["drivers"]), use_container_width=True)
with right:
    st.subheader("Innocence Engine verdict")
    inn = ev["innocence"]
    color = "#15803d" if inn["status"] == "Cleared" else ("#52525b" if inn["status"] == "Nothing to explain" else "#b91c1c")
    st.markdown(f'<div class="card"><h3 style="color:{color}">{inn["status"]}</h3>'
                f'<p>{inn["volume_text"]}</p><p>{inn["composition_text"]}</p></div>', unsafe_allow_html=True)
    st.subheader("Evidence")
    for e in ev["evidence"] or ["No single signal is far from its peers."]:
        st.markdown(f"- {e}")

st.subheader("Timeline: daily payments, cricket matches and Diwali")
cal = data.calendar()
daily = data.table("daily_counts").query("merchant_id == @mid")
bands = data.table("volume_bands").query("merchant_id == @mid")
fig = go.Figure()
for _, d in cal[cal["is_diwali_window"]].iterrows():
    fig.add_vrect(x0=d["date"] - pd.Timedelta(hours=12), x1=d["date"] + pd.Timedelta(hours=12),
                  fillcolor="#fde68a", opacity=0.45, line_width=0, layer="below")
fig.add_trace(go.Scatter(x=bands["date"], y=bands["upper"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=bands["date"], y=bands["lower"], fill="tonexty", fillcolor="rgba(37,99,235,0.15)",
                         line=dict(width=0), name="Expected range (peers + calendar)"))
fig.add_trace(go.Scatter(x=daily["date"], y=daily["cnt"], name="Payments per day", line=dict(color="#111827", width=2.5)))
match = cal[cal["ipl_match"]]
fig.add_trace(go.Scatter(x=match["date"], y=np.zeros(len(match)), mode="markers", name="Cricket match day",
                         marker=dict(symbol="triangle-up", size=11, color="#7c3aed")))
fig.update_layout(height=380, font=dict(size=16), margin=dict(t=10), legend=dict(orientation="h", y=1.12),
                  yaxis_title="Payments")
st.plotly_chart(fig, use_container_width=True)
st.caption("Yellow = Diwali window. Blue band = range expected from the merchant's own history x how much its peers moved that day.")

a, b = st.columns(2)
with a:
    st.subheader("When payments happen (hour x day)")
    cube = data.artifact("hour_day_counts")
    grid = cube["counts"][cube["ids"].index(mid)].T
    fig = px.imshow(grid, aspect="auto", color_continuous_scale="Blues", origin="lower",
                    labels=dict(x="Day", y="Hour of day", color="Payments"),
                    x=cal["date"].dt.strftime("%d %b"))
    fig.update_layout(height=420, font=dict(size=15), margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
with b:
    st.subheader("Amount mix vs category peers (last 30 days)")
    bins = cfg["features"]["amount_bins"]
    names = [f"{bins[i]}-{bins[i + 1]}" if bins[i + 1] < 1e6 else f"{bins[i]}+" for i in range(len(bins) - 1)]
    cols = [f"a{i:02d}" for i in range(len(names))]
    df = pd.DataFrame({"Amount (INR)": names * 2,
                       "Share": np.concatenate([feats.loc[mid, cols].to_numpy(float), cohort[cols].mean().to_numpy()]),
                       "Who": ["This merchant"] * len(names) + ["Peers"] * len(names)})
    fig = px.bar(df, x="Amount (INR)", y="Share", color="Who", barmode="group",
                 color_discrete_map={"This merchant": "#b91c1c", "Peers": "#94a3b8"})
    fig.update_layout(height=420, font=dict(size=15), margin=dict(t=10), xaxis_tickangle=-45, yaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Payer side (hard to fake)")
rows = {"Repeat payers (share of payments)": "repeat_txn_share", "New payers (share of payers)": "new_payer_rate",
        "Payers from other cities": "nonlocal_share", "Payers who pay in 3+ cities": "multi_city_payer_share",
        "Payer concentration (HHI)": "payer_hhi", "Payouts within 12 hours": "fast_payout_share",
        "Night share (00-05)": "night_share", "Exactly 499/999/1999": "pricepoint_share"}
tbl = pd.DataFrame({"This merchant": [feats.loc[mid, c] for c in rows.values()],
                    "Peer median": [cohort[c].median() for c in rows.values()],
                    "Peer z-score": [feats.loc[mid, f"z_{c}"] if f"z_{c}" in feats else np.nan for c in rows.values()]},
                   index=list(rows))
st.dataframe(tbl.style.format({"This merchant": "{:.1%}", "Peer median": "{:.1%}", "Peer z-score": "{:+.1f}"}),
             use_container_width=True)
theme.open_page("pages/5_Investigation_Report.py", mid, "Open the investigation report →", key="to_report")
