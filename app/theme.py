"""Projector-friendly styling and small shared UI pieces."""
from __future__ import annotations

import pandas as pd
import streamlit as st

TIER_COLOR = {"HIGH": "#b91c1c", "MEDIUM": "#d97706", "LOW": "#15803d"}
CATEGORY_COLOR = {"bakery": "#d97706", "grocery": "#2563eb", "restaurant": "#7c3aed",
                  "electronics": "#0891b2", "pharmacy": "#059669", "gym_or_tuition": "#db2777"}
HEROES = {"M0000": "SweetCrust Bakery", "M0001": "FreshOven Bakery", "M0002": "QuickKart Store"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ---------- base typography (projector-friendly) ---------- */
html, body, [class*="css"], .stMarkdown, .stDataFrame, .stSelectbox, .stRadio, .stSlider {
  font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
  font-size: 18px; color: #0f172a;
}
h1 { font-size: 2.25rem !important; font-weight: 800 !important; letter-spacing: -0.02em; color: #0f172a; margin-bottom: 0.2rem !important; }
h2 { font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.01em; color: #0f172a;
     border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3rem; margin-top: 1.4rem !important; }
h3 { font-size: 1.25rem !important; font-weight: 700 !important; color: #1e293b; }
p, li { line-height: 1.5; }
a { color: #1d4ed8; }

/* ---------- hide Streamlit chrome ---------- */
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1480px; }

/* ---------- sidebar: dark navy console ---------- */
section[data-testid="stSidebar"] { background: #0b1b3a; border-right: 1px solid #16284f; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
  border-radius: 8px; padding: 0.35rem 0.6rem; margin: 0.1rem 0; font-weight: 500; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { background: #16284f; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
  background: #1d4ed8; font-weight: 700; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::before {
  content: "MERCHANTDNA"; display: block; font-weight: 800; letter-spacing: 0.18em; font-size: 0.8rem;
  color: #93c5fd; padding: 0.2rem 0.6rem 0.9rem; }

/* ---------- metric tiles as cards ---------- */
[data-testid="stMetric"] {
  background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid #1d4ed8; border-radius: 12px;
  padding: 0.9rem 1.1rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06); }
[data-testid="stMetricLabel"] p { font-size: 0.98rem; color: #475569; font-weight: 600; }
[data-testid="stMetricValue"] { font-size: 2.3rem; font-weight: 800; color: #0f172a; letter-spacing: -0.02em; }
[data-testid="stMetricDelta"] { font-size: 0.95rem; }

/* ---------- our own components ---------- */
.tier { display: inline-block; padding: 0.2rem 0.85rem; border-radius: 999px; color: #fff;
        font-weight: 800; font-size: 1.05rem; letter-spacing: 0.06em; vertical-align: middle; }
.card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 1.1rem 1.3rem;
        margin-bottom: 0.7rem; min-height: 17rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06); }
.card h3 { margin-top: 0; }
.note { color: #475569; font-size: 1rem; }
.kicker { color: #1d4ed8; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; font-size: 0.85rem; }

/* ---------- widgets ---------- */
.stButton > button { border-radius: 10px; font-weight: 600; padding: 0.5rem 1.1rem; border: 1px solid #cbd5e1; }
.stButton > button[kind="primary"] { background: #1d4ed8; border-color: #1d4ed8; }
.stDownloadButton > button { border-radius: 10px; font-weight: 600; }
div[data-baseweb="select"] > div { border-radius: 10px; border-color: #cbd5e1; background: #ffffff; }
.stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 1.05rem; }
.stProgress > div > div > div { background: #1d4ed8; }
[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid #e2e8f0; border-radius: 12px; background: #ffffff; }
.stAlert { border-radius: 12px; }
hr { border-color: #e2e8f0; }
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
