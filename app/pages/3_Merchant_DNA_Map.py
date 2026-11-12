"""Merchant DNA Map: every merchant's 12-number behaviour code, projected to 2-D (UMAP).

Animated week by week: FreshOven walks out of the bakery cluster while SweetCrust's
volume explodes at Diwali but its DNA stays put.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import data
import theme

theme.setup("Merchant DNA Map")
theme.need_artefacts()
s = data.scores()
traj = data.table("dna_trajectory")

theme.page_header("Merchant DNA Map", "Each dot is a merchant's <b>behaviour fingerprint</b> — hours, amounts, payers, "
                  "timing — not its size. Merchants that do business the same way sit together. Press ▶ to watch the weeks go by.")
picks = st.multiselect("Follow merchants", list(s.index), default=list(theme.HEROES),
                       format_func=lambda m: f"{s.loc[m, 'name']} ({m})")

frames_days = sorted(traj["as_of_day"].unique())
label = {d: ("History" if d == -1 else traj.loc[traj["as_of_day"] == d, "as_of_date"].iloc[0].strftime("%d %b"))
         for d in frames_days}
TRAIL = ["#ffffff", "#f43f5e", "#f59e0b", "#22d3ee", "#4ade80", "#a855f7"]


def traces(day: int) -> list[go.Scatter]:
    """Background merchants by category + trails for followed merchants up to `day`."""
    now = traj[traj["as_of_day"] == day]
    out = []
    for cat, color in theme.CATEGORY_COLOR.items():
        p = now[now["declared_category"] == cat]
        out.append(go.Scatter(x=p["umap_x"], y=p["umap_y"], mode="markers", name=cat.replace("_", " "),
                              marker=dict(size=8, color=color, opacity=0.3, line=dict(width=0)),
                              text=p["merchant_id"], hoverinfo="text"))
    for i, mid in enumerate(picks):
        t = traj[(traj["merchant_id"] == mid) & (traj["as_of_day"] <= day)].sort_values("as_of_day")
        score = t["risk_score"].iloc[-1]
        col = TRAIL[i % len(TRAIL)]
        out.append(go.Scatter(x=t["umap_x"], y=t["umap_y"], mode="lines+markers+text", name=s.loc[mid, "name"],
                              line=dict(color=col, width=3),
                              marker=dict(size=[7] * (len(t) - 1) + [22], color=col, line=dict(width=2, color="#0b0a14")),
                              text=[""] * (len(t) - 1) + [f"{s.loc[mid, 'name'].split()[0]}"
                                                          f"{'' if score != score else f'  ·  {score:.0f}'}"],
                              textposition="top center", textfont=dict(size=15, color=col, family="Inter")))
    return out


with st.container(border=True):
    fig = go.Figure(data=traces(frames_days[0]), frames=[go.Frame(data=traces(d), name=label[d]) for d in frames_days])
    pad = 1.0
    fig.update_layout(
        height=700, margin=dict(t=50, b=10),
        xaxis=dict(range=[traj["umap_x"].min() - pad, traj["umap_x"].max() + pad], showticklabels=False, title="", showgrid=False, zeroline=False),
        yaxis=dict(range=[traj["umap_y"].min() - pad, traj["umap_y"].max() + pad], showticklabels=False, title="", showgrid=False, zeroline=False),
        legend=dict(orientation="v", x=1.01, y=1, yanchor="top"),
        updatemenus=[dict(type="buttons", x=0.0, y=1.09, direction="left", bgcolor="#1a1530", bordercolor="#a855f7",
                          font=dict(size=14, color="#f1eefb"), buttons=[
            dict(label="▶  Play", method="animate",
                 args=[None, {"frame": {"duration": 900, "redraw": True}, "fromcurrent": True}]),
            dict(label="❚❚", method="animate", args=[[None], {"mode": "immediate", "frame": {"duration": 0}}])])],
        sliders=[dict(active=0, currentvalue=dict(prefix="Week ending: ", font=dict(size=14)), bgcolor="#2a2340",
                      bordercolor="#2a2340", tickcolor=theme.MUTED, font=dict(size=12, color=theme.MUTED), steps=[
            dict(label=label[d], method="animate", args=[[label[d]], {"mode": "immediate", "frame": {"redraw": True}}])
            for d in frames_days])],
    )
    st.plotly_chart(fig, use_container_width=True, theme=None)
    st.caption("Number after the name = risk score that week. UMAP projection of the autoencoder's 12-dimensional "
               "bottleneck; distances are only meaningful locally.")
