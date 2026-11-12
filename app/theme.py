"""Design system for the dashboard: colours, CSS, a Plotly template and HTML components."""
from __future__ import annotations

import html as _html

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------- palette
NAVY, BLUE, INK, MUTED, LINE, BG = "#0b1b3a", "#2563eb", "#0f172a", "#64748b", "#e5e9f0", "#f5f7fb"
TIER_COLOR = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}
TIER_SOFT = {"HIGH": "#fee2e2", "MEDIUM": "#fef3c7", "LOW": "#dcfce7"}
TONE = {"blue": BLUE, "red": "#dc2626", "amber": "#d97706", "green": "#16a34a", "grey": "#64748b", "violet": "#7c3aed"}
CATEGORY_COLOR = {"bakery": "#d97706", "grocery": "#2563eb", "restaurant": "#7c3aed",
                  "electronics": "#0891b2", "pharmacy": "#16a34a", "gym_or_tuition": "#db2777"}
PALETTE = [BLUE, "#d97706", "#dc2626", "#16a34a", "#7c3aed", "#0891b2"]
HEROES = {"M0000": "SweetCrust Bakery", "M0001": "FreshOven Bakery", "M0002": "QuickKart Store"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --ink:#0f172a; --muted:#64748b; --line:#e5e9f0; --blue:#2563eb; --navy:#0b1b3a; }
html, body, [class*="css"], .stMarkdown, .stDataFrame, .stSelectbox, .stRadio, .stSlider, .stMultiSelect, .stTabs {
  font-family: "Inter", "Segoe UI", system-ui, sans-serif; font-size: 17px; color: var(--ink); }
.stApp { background: #f8fafc; }
.block-container { padding: 1.4rem 2.2rem 4rem; max-width: 1500px; }
p, li { line-height: 1.55; }
h1, h2, h3 { font-family: "Inter", sans-serif; letter-spacing: -0.015em; }

/* hide Streamlit chrome */
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* sidebar: light */
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid var(--line); min-width: 270px; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top: 0.6rem; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a { border-radius: 10px; padding: 0.45rem 0.75rem; margin: 0.12rem 0.3rem; font-weight: 500; font-size: 1rem; color: #334155; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span { color: #334155; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { background: #f1f5f9; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] { background: #eff6ff; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span { color: var(--blue); font-weight: 700; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::before {
  content: "MERCHANTDNA"; display: block; font-weight: 800; letter-spacing: 0.2em; font-size: 0.78rem; color: var(--blue); padding: 0.4rem 1rem 1rem; }
.side-foot { font-size: 0.82rem; color: var(--muted); line-height: 1.5; padding: 0 0.4rem; }
.side-foot b { color: var(--ink); }

/* page header */
.page-head { margin: 0 0 1.3rem; padding-bottom: 1rem; border-bottom: 1px solid var(--line); }
.page-head .kicker { color: var(--blue); font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; font-size: 0.76rem; margin-bottom: 0.35rem; }
.page-head h1 { font-size: 2.1rem; font-weight: 800; margin: 0; color: var(--ink); line-height: 1.15; }
.page-head .sub { color: var(--muted); font-size: 1.05rem; margin-top: 0.4rem; max-width: 70rem; }

/* section titles */
.sec { display: flex; align-items: baseline; gap: 0.8rem; margin: 1.6rem 0 0.7rem; }
.sec h2 { font-size: 1.3rem; font-weight: 700; margin: 0; color: var(--ink); }
.sec span { color: var(--muted); font-size: 0.95rem; }
.sec.first { margin-top: 0.2rem; }

/* KPI tiles */
.kpis { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 0.9rem; margin: 0.2rem 0 1.2rem; }
.kpi { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 0.95rem 1.1rem 0.9rem; box-shadow: 0 1px 2px rgba(15,23,42,.04); position: relative; overflow: hidden; }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--tone, #2563eb); }
.kpi .l { color: var(--muted); font-size: 0.86rem; font-weight: 600; margin-bottom: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi .v { font-size: 2.05rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; color: var(--ink); }
.kpi .s { color: var(--muted); font-size: 0.85rem; margin-top: 0.3rem; }
.kpi .s.up { color: #16a34a; font-weight: 600; } .kpi .s.down { color: #dc2626; font-weight: 600; }

/* panels (bordered containers) */
/* Streamlit wraps every block in this wrapper; only st.container(border=True) gets a non-empty emotion class */
[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) { background: #fff; border-radius: 16px; box-shadow: 0 1px 2px rgba(15,23,42,.04); margin-bottom: 0.9rem; }
[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) > div { border: 1px solid var(--line) !important; border-radius: 16px !important; }
.panel { background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 1.1rem 1.3rem; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.panel h3, .ptitle { font-size: 1.1rem; font-weight: 700; margin: 0 0 0.6rem; color: var(--ink); }
.ptitle span { color: var(--muted); font-weight: 500; font-size: 0.9rem; margin-left: 0.5rem; }

/* badges and chips */
.badge { display: inline-block; padding: 0.22rem 0.8rem; border-radius: 999px; color: #fff; font-weight: 800; font-size: 0.9rem; letter-spacing: 0.08em; vertical-align: middle; }
.chip { display: inline-block; padding: 0.18rem 0.7rem; border-radius: 999px; background: #eef2ff; color: #3730a3; font-weight: 600; font-size: 0.85rem; margin-right: 0.35rem; }
.chip.grey { background: #f1f5f9; color: #334155; } .chip.green { background: #dcfce7; color: #166534; }
.chip.red { background: #fee2e2; color: #991b1b; } .chip.amber { background: #fef3c7; color: #92400e; }

/* merchant header card */
.mcard { display: flex; gap: 1.4rem; align-items: center; background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 1.1rem 1.4rem; box-shadow: 0 1px 2px rgba(15,23,42,.04); }
.mcard .name { font-size: 1.55rem; font-weight: 800; letter-spacing: -0.015em; }
.mcard .meta { color: var(--muted); margin: 0.25rem 0 0.6rem; }
.mcard .facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.6rem 1.4rem; margin-top: 0.5rem; }
.mcard .facts .k { color: var(--muted); font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; }
.mcard .facts .f { font-weight: 700; font-size: 1.05rem; }

/* hero cards on Home */
.hero { background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 1.2rem 1.3rem 1rem; box-shadow: 0 1px 2px rgba(15,23,42,.04); height: 19.5rem; display: flex; flex-direction: column; }
.hero .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; }
.hero .name { font-size: 1.25rem; font-weight: 800; }
.hero .blurb { color: var(--muted); font-size: 0.95rem; margin: 0.3rem 0 0.8rem; min-height: 2.9rem; }
.hero .row { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.hero .kv { font-size: 0.9rem; color: var(--muted); } .hero .kv b { color: var(--ink); display: block; font-size: 0.98rem; }

/* verdict */
.verdict { border-radius: 14px; padding: 1rem 1.2rem; border: 1px solid var(--line); }
.verdict .t { font-weight: 800; font-size: 1.15rem; margin-bottom: 0.4rem; }
.verdict p { margin: 0.3rem 0; font-size: 0.98rem; }
.checks div { padding: 0.35rem 0; border-bottom: 1px dashed var(--line); }
.checks .ok::before { content: "✓"; color: #16a34a; font-weight: 800; margin-right: 0.6rem; }
.checks .bad::before { content: "✗"; color: #dc2626; font-weight: 800; margin-right: 0.6rem; }
.ev li { margin: 0.3rem 0; }

/* how-it-works steps */
.steps { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.9rem; }
.step { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 1rem 1.05rem; }
.step .n { width: 2rem; height: 2rem; border-radius: 999px; background: var(--navy); color: #fff; font-weight: 800; display: grid; place-items: center; margin-bottom: 0.6rem; }
.step .t { font-weight: 700; margin-bottom: 0.3rem; } .step .d { color: var(--muted); font-size: 0.92rem; }

/* budget bar */
.bar { background: #e2e8f0; border-radius: 999px; height: 12px; overflow: hidden; }
.bar > div { height: 100%; background: linear-gradient(90deg, #2563eb, #7c3aed); }

/* widgets */
.stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 600; padding: 0.5rem 1.1rem; border: 1px solid #cbd5e1; background: #fff; }
.stButton > button[kind="primary"] { background: var(--blue); border-color: var(--blue); color: #fff; }
div[data-baseweb="select"] > div { border-radius: 10px; border-color: #cbd5e1; background: #fff; }
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; } .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 1rem; padding: 0.4rem 0.9rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 12px; background: #fff; }
.stAlert { border-radius: 12px; } hr { border-color: var(--line); }
[data-testid="stWidgetLabel"] p { font-weight: 600; color: #334155; font-size: 0.92rem; }
.stCaption, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: 0.88rem !important; }
</style>
"""

TEMPLATE = go.layout.Template(layout=go.Layout(
    font=dict(family="Inter, Segoe UI, sans-serif", size=14, color=INK),
    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", colorway=PALETTE,
    margin=dict(l=55, r=20, t=40, b=50),
    xaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED), automargin=True),
    yaxis=dict(gridcolor=LINE, zerolinecolor=LINE, linecolor=LINE, tickfont=dict(color=MUTED), title_font=dict(color=MUTED), automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font=dict(size=13)),
    hoverlabel=dict(bgcolor=NAVY, font=dict(color="white", size=13)),
    title=dict(font=dict(size=16, color=INK), x=0, xanchor="left"),
))


# ---------------------------------------------------------------- setup
def setup(title: str, icon: str = "◆") -> None:
    """Page config, CSS, Plotly template and sidebar footer. Call first on every page."""
    st.set_page_config(page_title=f"MerchantDNA · {title}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    pio.templates["merchantdna"] = TEMPLATE
    pio.templates.default = "merchantdna"
    st.sidebar.markdown('<div class="side-foot"><b>Follow the Money</b><br>CSITM IIM Bangalore × PayU<br><br>'
                        'Signals, not proof — a human analyst decides.<br>All data is synthetic.</div>',
                        unsafe_allow_html=True)


def need_artefacts() -> None:
    from data import artefacts_ready
    if not artefacts_ready():
        st.error("Artefacts not found. Run `make all` first, then reload this page.")
        st.stop()


# ---------------------------------------------------------------- html components
def esc(x: object) -> str:
    return _html.escape(str(x))


def page_header(title: str, subtitle: str = "", kicker: str = "MerchantDNA") -> None:
    st.markdown(f'<div class="page-head"><div class="kicker">{esc(kicker)}</div><h1>{esc(title)}</h1>'
                f'{f"<div class=sub>{subtitle}</div>" if subtitle else ""}</div>', unsafe_allow_html=True)


def section(title: str, sub: str = "", first: bool = False) -> None:
    st.markdown(f'<div class="sec{" first" if first else ""}"><h2>{esc(title)}</h2>'
                f'{f"<span>{esc(sub)}</span>" if sub else ""}</div>', unsafe_allow_html=True)


def kpis(items: list[dict]) -> None:
    """items: {label, value, sub?, tone?, trend?('up'|'down')}"""
    tiles = []
    for it in items:
        tone = TONE.get(it.get("tone", "blue"), BLUE)
        sub = it.get("sub", "")
        cls = f"s {it.get('trend', '')}".strip()
        tiles.append(f'<div class="kpi" style="--tone:{tone}"><div class="l">{esc(it["label"])}</div>'
                     f'<div class="v">{esc(it["value"])}</div>{f"<div class={chr(34)}{cls}{chr(34)}>{esc(sub)}</div>" if sub else ""}</div>')
    st.markdown(f'<div class="kpis">{"".join(tiles)}</div>', unsafe_allow_html=True)


def badge(tier: str) -> str:
    return f'<span class="badge" style="background:{TIER_COLOR[tier]}">{tier}</span>'


def chip(text: str, tone: str = "") -> str:
    return f'<span class="chip {tone}">{esc(text)}</span>'


def ring(score: float, tier: str, size: int = 104) -> str:
    """SVG donut showing the 0-100 score in the tier colour."""
    r, sw = 44, 9
    c = 2 * 3.14159 * r
    dash = c * max(0.0, min(score, 100)) / 100
    col = TIER_COLOR[tier]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" style="flex:none">'
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="#eef2f7" stroke-width="{sw}"/>'
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-dasharray="{dash:.1f} {c:.1f}" transform="rotate(-90 50 50)"/>'
            f'<text x="50" y="50" text-anchor="middle" dominant-baseline="central" font-size="30" font-weight="800" '
            f'font-family="Inter, sans-serif" fill="{INK}">{score:.0f}</text>'
            f'<text x="50" y="72" text-anchor="middle" font-size="11" font-weight="600" fill="{MUTED}" font-family="Inter, sans-serif">/ 100</text></svg>')


def hero_card(name: str, blurb: str, r: pd.Series) -> str:
    return (f'<div class="hero"><div class="top"><div><div class="name">{esc(name)}</div>'
            f'<div class="blurb">{esc(blurb)}</div></div>{ring(r["risk_score"], r["tier"], 96)}</div>'
            f'<div>{badge(r["tier"])}</div>'
            f'<div class="row"><div class="kv">Action<b>{esc(r["rung"])}</b></div></div>'
            f'<div class="kv" style="margin-top:0.5rem">Innocence check<b>{esc(r["innocence_status"])}</b></div></div>')


def merchant_header(r: pd.Series, ev: dict) -> None:
    facts = [("Declared category", r["declared_category"].replace("_", " ")),
             ("Behaves like", f'{ev["behaves_like"].replace("_", " ")} · {ev["behaves_like_p"]:.0%}'),
             ("DNA drift vs own history", f'{r["dna_drift_self"]:.1f}× typical'),
             ("Recommended action", r["rung"]), ("City", r["city"]),
             ("Innocence Engine", ev["innocence"]["status"])]
    fhtml = "".join(f'<div><div class="k">{esc(k)}</div><div class="f">{esc(v)}</div></div>' for k, v in facts)
    st.markdown(f'<div class="mcard">{ring(r["risk_score"], r["tier"], 120)}<div style="flex:1">'
                f'<div class="name">{esc(r["name"])} &nbsp;{badge(r["tier"])}</div>'
                f'<div class="meta">{esc(r.name)} · {chip(r["declared_category"].replace("_", " "))}{chip(r["city"], "grey")}</div>'
                f'<div class="facts">{fhtml}</div></div></div>', unsafe_allow_html=True)


def verdict_panel(inn: dict) -> None:
    status = inn["status"]
    tone = ("green", "#f0fdf4") if status == "Cleared" else (("grey", "#f8fafc") if status == "Nothing to explain" else ("red", "#fef2f2"))
    col = TONE[tone[0]]
    st.markdown(f'<div class="verdict" style="background:{tone[1]}"><div class="t" style="color:{col}">{esc(status)}</div>'
                f'<p>{esc(inn["volume_text"])}</p><p>{esc(inn["composition_text"])}</p></div>', unsafe_allow_html=True)


def bullet_list(items: list[str], empty: str) -> None:
    items = items or [empty]
    st.markdown('<ul class="ev">' + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>", unsafe_allow_html=True)


def checks(claim: dict) -> None:
    rows = "".join(f'<div class="{"ok" if k["passed"] else "bad"}">{esc(k["check"])}</div>' for k in claim["checks"])
    st.markdown(f'<div class="checks">{rows}</div>', unsafe_allow_html=True)


def budget_bar(used: int, cap: int) -> None:
    pct = min(used / max(cap, 1), 1.0) * 100
    st.markdown(f'<div style="display:flex;justify-content:space-between;color:{MUTED};font-size:0.9rem;margin-bottom:0.35rem">'
                f'<span>Analyst capacity used this cycle</span><b style="color:{INK}">{used} / {cap}</b></div>'
                f'<div class="bar"><div style="width:{pct:.0f}%"></div></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- charts and widgets
def drivers_chart(drivers: list[dict], height: int | None = None) -> go.Figure:
    """Horizontal bars of SHAP contributions (red raises risk, green lowers it)."""
    d = list(reversed(drivers))
    fig = go.Figure(go.Bar(x=[x["contribution"] for x in d], y=[x["label"] for x in d], orientation="h",
                           marker=dict(color=["#dc2626" if x["contribution"] > 0 else "#16a34a" for x in d],
                                       cornerradius=6),
                           text=[f'{x["contribution"]:+.2f}' for x in d], textposition="outside", cliponaxis=False))
    fig.update_layout(height=height or 70 + 46 * len(d), margin=dict(l=10, r=45, t=10, b=45), showlegend=False,
                      xaxis_title="Push on risk (log-odds)", yaxis=dict(tickfont=dict(size=13)))
    return fig


def style_table(df: pd.DataFrame, fmt: dict | None = None, tier_col: str | None = None, highlight_row: str | None = None):
    """Pandas Styler with tier colours and an optional highlighted row."""
    sty = df.style
    if fmt:
        sty = sty.format(fmt)
    if tier_col:
        sty = sty.map(lambda t: f"background-color:{TIER_SOFT.get(t, '#fff')};color:{TIER_COLOR.get(t, INK)};font-weight:700",
                      subset=[tier_col])
    if highlight_row is not None:
        sty = sty.apply(lambda r: ["background-color:#eff6ff;font-weight:700" if r.name == highlight_row else "" for _ in r], axis=1)
    return sty


def merchant_picker(scores: pd.DataFrame, key: str, default: str = "M0001", label: str = "Merchant") -> str:
    """Selectbox listing hero merchants first, then everyone by risk."""
    order = list(HEROES) + [m for m in scores.sort_values("risk_score", ascending=False).index if m not in HEROES]
    labels = {m: f"{scores.loc[m, 'name']}  ·  {m}  ·  {scores.loc[m, 'tier']} {scores.loc[m, 'risk_score']:.0f}"
              for m in order}
    chosen = st.session_state.get("merchant", default)
    start = order.index(chosen) if chosen in order else order.index(default)
    mid = st.selectbox(label, order, index=start, format_func=labels.get, key=key)
    st.session_state["merchant"] = mid
    return mid


def open_page(page: str, mid: str, label: str, key: str, primary: bool = False) -> None:
    """Button that opens another page focused on merchant `mid`."""
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True):
        st.session_state["merchant"] = mid
        st.switch_page(page)
