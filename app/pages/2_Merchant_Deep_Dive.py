"""Merchant Deep Dive: claimed vs actual behaviour, with every score's reasons."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data
import theme

theme.setup("Merchant Deep Dive")
theme.need_artefacts()
s, ev_all, cfg = data.scores(), data.evidence(), data.config()

theme.page_header("Merchant Deep Dive", "What the merchant claims to be, how it actually behaves, and whether the "
                  "Innocence Engine could explain the difference.")
mid = theme.merchant_picker(s, "dd")
r, ev = s.loc[mid], ev_all[mid]
feats = data.table("features_current").set_index("merchant_id")
cohort = feats.join(s[["declared_category"]]).query("declared_category == @r.declared_category")

theme.merchant_header(r, ev)
st.markdown("")

left, right = st.columns([1, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Why this score <span>SHAP drivers, plain English</span></div>', unsafe_allow_html=True)
    st.plotly_chart(theme.drivers_chart(ev["drivers"], height=300), use_container_width=True, theme=None)
with right, st.container(border=True):
    st.markdown('<div class="ptitle">Innocence Engine verdict</div>', unsafe_allow_html=True)
    theme.verdict_panel(ev["innocence"])

with st.container(border=True):
    st.markdown('<div class="ptitle">Evidence <span>where this merchant is far from its peers</span></div>', unsafe_allow_html=True)
    theme.bullet_list(ev["evidence"], "No single signal is far from its peers.")

with st.container(border=True):
    st.markdown('<div class="ptitle">Daily payments vs the expected range <span>Diwali window shaded · '
                'triangles = cricket match days</span></div>', unsafe_allow_html=True)
    cal = data.calendar()
    daily = data.table("daily_counts").query("merchant_id == @mid")
    bands = data.table("volume_bands").query("merchant_id == @mid")
    fig = go.Figure()
    dw = cal[cal["is_diwali_window"]]["date"]
    fig.add_vrect(x0=dw.min() - pd.Timedelta(hours=12), x1=dw.max() + pd.Timedelta(hours=12), fillcolor="#f97316",
                  opacity=0.14, line_width=0, layer="below", annotation_text="Diwali", annotation_position="top left",
                  annotation_font=dict(color="#fdba74", size=13))
    fig.add_trace(go.Scatter(x=bands["date"], y=bands["upper"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=bands["date"], y=bands["lower"], fill="tonexty", fillcolor="rgba(168,85,247,0.22)",
                             line=dict(width=0), name="Expected range (own history × peers)"))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["cnt"], name="Payments per day",
                             line=dict(color=theme.INK, width=2.4)))
    match = cal[cal["ipl_match"]]
    fig.add_trace(go.Scatter(x=match["date"], y=np.zeros(len(match)), mode="markers", name="Match day",
                             marker=dict(symbol="triangle-up", size=10, color="#ec4899")))
    fig.update_layout(height=360, yaxis_title="Payments", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True, theme=None)

a, b = st.columns(2)
with a, st.container(border=True):
    st.markdown('<div class="ptitle">When payments happen <span>hour × day</span></div>', unsafe_allow_html=True)
    cube = data.artifact("hour_day_counts")
    grid = cube["counts"][cube["ids"].index(mid)].T
    fig = px.imshow(grid, aspect="auto", color_continuous_scale=[[0, "#0b0a14"], [0.25, "#4c1d95"], [0.6, "#c026d3"], [1, "#fdba74"]], origin="lower",
                    labels=dict(x="Day", y="Hour of day", color="Payments"), x=cal["date"].dt.strftime("%d %b"))
    fig.update_layout(height=380, coloraxis_colorbar=dict(thickness=10, len=0.8))
    st.plotly_chart(fig, use_container_width=True, theme=None)
with b, st.container(border=True):
    st.markdown('<div class="ptitle">Amount mix vs category peers <span>last 30 days</span></div>', unsafe_allow_html=True)
    bins = cfg["features"]["amount_bins"]
    names = [f"{bins[i]}–{bins[i + 1]}" if bins[i + 1] < 1e6 else f"{bins[i]}+" for i in range(len(bins) - 1)]
    cols = [f"a{i:02d}" for i in range(len(names))]
    df = pd.DataFrame({"Amount (₹)": names * 2,
                       "Share": np.concatenate([feats.loc[mid, cols].to_numpy(float), cohort[cols].mean().to_numpy()]),
                       "Who": ["This merchant"] * len(names) + ["Peers"] * len(names)})
    fig = px.bar(df, x="Amount (₹)", y="Share", color="Who", barmode="group",
                 color_discrete_map={"This merchant": theme.TIER_COLOR[r["tier"]], "Peers": "#6b6488"})
    fig.update_traces(marker_line_width=0)
    fig.update_layout(height=380, xaxis_tickangle=-45, yaxis_tickformat=".0%", legend_title_text="", bargap=0.25)
    st.plotly_chart(fig, use_container_width=True, theme=None)

with st.container(border=True):
    st.markdown('<div class="ptitle">Payer side <span>the hard-to-fake signals</span></div>', unsafe_allow_html=True)
    rows = {"Repeat payers (share of payments)": "repeat_txn_share", "New payers (share of payers)": "new_payer_rate",
            "Payers from other cities": "nonlocal_share", "Payers who pay in 3+ cities": "multi_city_payer_share",
            "Payer concentration (HHI)": "payer_hhi", "Payouts within 12 hours": "fast_payout_share",
            "Night share (00–05)": "night_share", "Exactly ₹499 / 999 / 1999": "pricepoint_share"}
    tbl = pd.DataFrame({"This merchant": [feats.loc[mid, c] for c in rows.values()],
                        "Peer median": [cohort[c].median() for c in rows.values()],
                        "Peer z-score": [feats.loc[mid, f"z_{c}"] if f"z_{c}" in feats else np.nan for c in rows.values()]},
                       index=list(rows))
    sty = tbl.style.format({"This merchant": "{:.1%}", "Peer median": "{:.1%}", "Peer z-score": "{:+.1f}"}).map(
        lambda z: "color:#fb7185;font-weight:700" if z >= 3 else ("color:#fbbf24;font-weight:600" if z >= 1.5 else ""),
        subset=["Peer z-score"])
    st.dataframe(sty, use_container_width=True, height=330)
    st.caption("z-score = how many robust standard deviations from the median of peers in the same category and city tier.")

c = st.columns([1, 2, 1])
with c[1]:
    theme.open_page("pages/5_Investigation_Report.py", mid, "Open the investigation report →", key="to_report", primary=True)
