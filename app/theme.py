"""Projector-friendly styling and small shared UI pieces."""
from __future__ import annotations

import pandas as pd
import streamlit as st

TIER_COLOR = {"HIGH": "#b91c1c", "MEDIUM": "#c2410c", "LOW": "#15803d"}
CATEGORY_COLOR = {"bakery": "#d97706", "grocery": "#2563eb", "restaurant": "#7c3aed",
                  "electronics": "#0891b2", "pharmacy": "#059669", "gym_or_tuition": "#db2777"}
HEROES = {"M0000": "SweetCrust Bakery", "M0001": "FreshOven Bakery", "M0002": "QuickKart Store"}

CSS = """
<style>
html, body, [class*="css"] { font-size: 19px; }
h1 { font-size: 2.3rem !important; } h2 { font-size: 1.75rem !important; } h3 { font-size: 1.4rem !important; }
[data-testid="stMetricValue"] { font-size: 2.4rem; font-weight: 700; }
[data-testid="stMetricLabel"] p { font-size: 1.05rem; }
.block-container { padding-top: 1.5rem; max-width: 1500px; }
.tier { display:inline-block; padding: 0.15rem 0.8rem; border-radius: 0.5rem; color: white;
        font-weight: 700; font-size: 1.15rem; }
.card { border: 2px solid #d4d4d8; border-radius: 0.7rem; padding: 0.9rem 1.1rem; margin-bottom: 0.6rem; min-height: 17rem; }
.note { color: #3f3f46; font-size: 1rem; }
</style>
"""


def setup(title: str, icon: str = "🧬") -> None:
    """Page config + CSS. Call first on every page."""
    st.set_page_config(page_title=f"MerchantDNA · {title}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def tier_badge(tier: str) -> str:
    return f'<span class="tier" style="background:{TIER_COLOR[tier]}">{tier}</span>'


def merchant_picker(scores: pd.DataFrame, key: str, default: str = "M0001") -> str:
    """Selectbox listing hero merchants first, then everyone by risk."""
    order = list(HEROES) + [m for m in scores.sort_values("risk_score", ascending=False).index if m not in HEROES]
    labels = {m: f"{scores.loc[m, 'name']} ({m}) · {scores.loc[m, 'tier']} {scores.loc[m, 'risk_score']:.0f}"
              for m in order}
    chosen = st.session_state.get("merchant", default)             # shared across pages
    start = order.index(chosen) if chosen in order else order.index(default)
    mid = st.selectbox("Merchant", order, index=start, format_func=labels.get, key=key)
    st.session_state["merchant"] = mid
    return mid


def open_page(page: str, mid: str, label: str, key: str) -> None:
    """Button that opens another page focused on merchant `mid`."""
    if st.button(label, key=key):
        st.session_state["merchant"] = mid
        st.switch_page(page)


def drivers_chart(drivers: list[dict]):
    """Horizontal bar chart of SHAP contributions (red raises risk, green lowers it)."""
    import plotly.graph_objects as go
    d = list(reversed(drivers))
    fig = go.Figure(go.Bar(x=[x["contribution"] for x in d], y=[x["label"] for x in d], orientation="h",
                           marker_color=["#b91c1c" if x["contribution"] > 0 else "#15803d" for x in d]))
    fig.update_layout(height=60 + 48 * len(d), margin=dict(l=10, r=10, t=10, b=10), font=dict(size=16),
                      xaxis_title="Push on risk (log-odds)")
    return fig


def need_artefacts() -> None:
    from data import artefacts_ready
    if not artefacts_ready():
        st.error("Artefacts not found. Run `make all` first, then reload this page.")
        st.stop()
