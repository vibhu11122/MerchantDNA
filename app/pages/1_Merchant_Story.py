"""Merchant Story: one merchant, start to finish — why the score, the Innocence check, behaviour,
connections, the merchant's explanation and the drafted reports."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import data
import netviz
import theme
from merchantdna.decision.explain_step import REASONS
from merchantdna.decision.report import investigation_markdown, markdown_to_pdf
from merchantdna.decision.str_report import str_draft

theme.setup("Merchant Story")
theme.need_artefacts()
s, ev_all, cfg = data.scores(), data.evidence(), data.config()

theme.page_header("Merchant Story", "What the merchant claims to be, how it actually behaves, whether a legitimate "
                  "reason explains the difference — and what we would do about it.")
mid = theme.merchant_picker(s, "story")
r, ev = s.loc[mid], dict(ev_all[mid])
feats = data.table("features_current").set_index("merchant_id")
cohort = feats.join(s[["declared_category"]]).query("declared_category == @r.declared_category")
network_lines = [n.replace(" (Jaccard)", "") for n in ev["network"]]

theme.merchant_header(r, ev)
st.markdown("")

# ---------------------------------------------------------------- the verdict
left, right = st.columns([1, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Why this score <span>red raises risk · green lowers it</span></div>',
                unsafe_allow_html=True)
    st.plotly_chart(theme.drivers_chart(ev["drivers"], height=300), use_container_width=True, theme=None)
with right, st.container(border=True):
    st.markdown('<div class="ptitle">Could a legitimate reason explain it? <span>Innocence Engine</span></div>',
                unsafe_allow_html=True)
    theme.verdict_panel(ev["innocence"])

with st.container(border=True):
    st.markdown('<div class="ptitle">Evidence <span>where this merchant is far from its peers</span></div>',
                unsafe_allow_html=True)
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
    fig.update_layout(height=340, yaxis_title="Payments", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True, theme=None)

# ---------------------------------------------------------------- details
t_beh, t_net, t_rep = st.tabs(["Behaviour", "Connections", "Explain & report"])

with t_beh:
    a, b = st.columns(2)
    with a, st.container(border=True):
        st.markdown('<div class="ptitle">When payments happen <span>hour × day</span></div>', unsafe_allow_html=True)
        cube = data.artifact("hour_day_counts")
        grid = cube["counts"][cube["ids"].index(mid)].T
        fig = px.imshow(grid, aspect="auto", origin="lower",
                        color_continuous_scale=[[0, "#0b0a14"], [0.25, "#4c1d95"], [0.6, "#c026d3"], [1, "#fdba74"]],
                        labels=dict(x="Day", y="Hour of day", color="Payments"), x=cal["date"].dt.strftime("%d %b"))
        fig.update_layout(height=360, coloraxis_colorbar=dict(thickness=10, len=0.8))
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with b, st.container(border=True):
        st.markdown('<div class="ptitle">Amount mix vs category peers <span>last 30 days</span></div>',
                    unsafe_allow_html=True)
        bins = cfg["features"]["amount_bins"]
        names = [f"{bins[i]}–{bins[i + 1]}" if bins[i + 1] < 1e6 else f"{bins[i]}+" for i in range(len(bins) - 1)]
        cols = [f"a{i:02d}" for i in range(len(names))]
        df = pd.DataFrame({"Amount (₹)": names * 2,
                           "Share": np.concatenate([feats.loc[mid, cols].to_numpy(float), cohort[cols].mean().to_numpy()]),
                           "Who": ["This merchant"] * len(names) + ["Peers"] * len(names)})
        fig = px.bar(df, x="Amount (₹)", y="Share", color="Who", barmode="group",
                     color_discrete_map={"This merchant": theme.TIER_COLOR[r["tier"]], "Peers": "#6b6488"})
        fig.update_traces(marker_line_width=0)
        fig.update_layout(height=360, xaxis_tickangle=-45, yaxis_tickformat=".0%", legend_title_text="", bargap=0.25)
        st.plotly_chart(fig, use_container_width=True, theme=None)
    with st.container(border=True):
        st.markdown('<div class="ptitle">Who pays <span>the hard-to-fake signals</span></div>', unsafe_allow_html=True)
        rows = {"Repeat payers (share of payments)": "repeat_txn_share", "Payers from other cities": "nonlocal_share",
                "Payers who pay in 3+ cities": "multi_city_payer_share", "Payouts within 12 hours": "fast_payout_share",
                "Night share (00–05)": "night_share", "Exactly ₹499 / 999 / 1999": "pricepoint_share"}
        tbl = pd.DataFrame({"This merchant": [feats.loc[mid, c] for c in rows.values()],
                            "Typical peer": [cohort[c].median() for c in rows.values()]}, index=list(rows))
        st.dataframe(tbl.style.format("{:.0%}"), use_container_width=True)

with t_net:
    left, right = st.columns([1.6, 1])
    with left, st.container(border=True):
        st.markdown('<div class="ptitle">Linked merchants <span>node colour = risk · thicker line = rarer shared '
                    'identifier · hover a line</span></div>', unsafe_allow_html=True)
        components.html(netviz.ego_graph_html(data.artifact("bundle"), s, mid), height=580)
        st.markdown(f'{theme.chip("HIGH", "red")}{theme.chip("MEDIUM", "amber")}{theme.chip("LOW", "green")} &nbsp; '
                    f'<span style="color:{theme.MUTED};font-size:0.9rem">grey solid = shared device / bank / IP / '
                    'address · pink dashed = shared payers</span>', unsafe_allow_html=True)
    with right, st.container(border=True):
        st.markdown(f'<div class="ptitle">What {theme.esc(r["name"])} shares</div>', unsafe_allow_html=True)
        theme.bullet_list(network_lines, "No notable links.")
        st.caption("A shared device or bank account is a strong link. A shared franchise address or GST number is weak.")

with t_rep:
    with st.container(border=True):
        st.markdown('<div class="ptitle">Step 1 · Ask the merchant to explain <span>before any hold</span></div>',
                    unsafe_allow_html=True)
        st.caption("The merchant picks a reason. We test the claim against the data and record the result either way.")
        reason = st.radio("Merchant's stated reason", ["(no explanation yet)"] + REASONS, horizontal=True)
        if reason != "(no explanation yet)":
            claim = ev["claims"][reason]
            ev["claim"] = claim
            tone, col = ("green", "rgba(34,197,94,0.10)") if claim["accepted"] else ("red", "rgba(244,63,94,0.10)")
            st.markdown(f'<div class="verdict" style="background:{col}"><div class="t" style="color:{theme.TONE[tone]}">'
                        f'{"Claim consistent with the data" if claim["accepted"] else "Claim not supported by the data"}'
                        '</div></div>', unsafe_allow_html=True)
            theme.checks(claim)

    ev["network"] = network_lines
    report_md = investigation_markdown(ev)
    str_md = str_draft(ev, data.merchants_public().loc[mid], feats.loc[mid], cfg)

    st.markdown("")
    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown('<div class="ptitle">Step 2 · Investigation report <span>the audit trail</span></div>',
                    unsafe_allow_html=True)
        c = st.columns(2)
        c[0].download_button("⬇ Markdown", report_md, file_name=f"report_{mid}.md", mime="text/markdown",
                             use_container_width=True)
        c[1].download_button("⬇ PDF", markdown_to_pdf(report_md), file_name=f"report_{mid}.pdf",
                             mime="application/pdf", use_container_width=True)
        with st.container(height=520, border=False):
            st.markdown(report_md)
    with right, st.container(border=True):
        st.markdown('<div class="ptitle">Step 3 · Draft STR <span>auto-drafted, a human files</span></div>',
                    unsafe_allow_html=True)
        reviewed = st.checkbox("I have reviewed this draft", key=f"str_ok_{mid}")
        c = st.columns(2)
        c[0].download_button("⬇ STR (Markdown)", str_md, file_name=f"STR_draft_{mid}.md", mime="text/markdown",
                             use_container_width=True, disabled=not reviewed)
        c[1].download_button("⬇ STR (PDF)", markdown_to_pdf(str_md), file_name=f"STR_draft_{mid}.pdf",
                             mime="application/pdf", use_container_width=True, disabled=not reviewed)
        with st.container(height=520, border=False):
            st.markdown(str_md)
