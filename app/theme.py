"""Design system for the dashboard: colours, CSS, a Plotly template and HTML components."""
from __future__ import annotations

import html as _html

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------- palette
NAVY, BLUE, INK, MUTED, LINE, BG = "#1a1530", "#a855f7", "#f1eefb", "#a7a3bf", "rgba(255,255,255,0.10)", "#0b0a14"
PINK, ORANGE, VIOLET = "#ec4899", "#f97316", "#8b5cf6"
GRAD = "linear-gradient(90deg, #7c3aed 0%, #c026d3 55%, #f97316 100%)"
TIER_COLOR = {"HIGH": "#f43f5e", "MEDIUM": "#f59e0b", "LOW": "#22c55e"}
TIER_SOFT = {"HIGH": "rgba(244,63,94,0.18)", "MEDIUM": "rgba(245,158,11,0.18)", "LOW": "rgba(34,197,94,0.16)"}
TONE = {"blue": "#a855f7", "red": "#f43f5e", "amber": "#f59e0b", "green": "#22c55e", "grey": "#a7a3bf", "violet": "#ec4899"}
CATEGORY_COLOR = {"bakery": "#f59e0b", "grocery": "#60a5fa", "restaurant": "#a855f7",
                  "electronics": "#22d3ee", "pharmacy": "#4ade80", "gym_or_tuition": "#f472b6"}
PALETTE = ["#a855f7", "#ec4899", "#f97316", "#22d3ee", "#4ade80", "#f59e0b"]
HEROES = {"M0000": "SweetCrust Bakery", "M0001": "FreshOven Bakery", "M0002": "QuickKart Store"}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
:root { --ink:#f1eefb; --muted:#a7a3bf; --line:rgba(255,255,255,0.10); --violet:#a855f7; --pink:#f9a8d4;
        --card:rgba(255,255,255,0.045); --grad:linear-gradient(90deg,#7c3aed 0%,#c026d3 55%,#f97316 100%); }
html, body, [class*="css"], .stMarkdown, .stDataFrame, .stSelectbox, .stRadio, .stSlider, .stMultiSelect, .stTabs {
  font-family: "Inter", "Segoe UI", system-ui, sans-serif; font-size: 17px; color: var(--ink); }
.stApp {
  background:
    radial-gradient(900px 520px at 55% -8%, rgba(190, 24, 93, 0.22), transparent 60%),
    radial-gradient(800px 600px at 92% 30%, rgba(124, 58, 237, 0.22), transparent 60%),
    radial-gradient(700px 500px at 10% 100%, rgba(234, 88, 12, 0.18), transparent 60%),
    #0b0a14;
  background-attachment: fixed; }
.block-container { padding: 1.4rem 2.2rem 4rem; max-width: 1500px; }
p, li { line-height: 1.55; color: #e4e0f3; }
a { color: #c4b5fd; }

/* hide Streamlit chrome */
#MainMenu, footer, .stDeployButton, [data-testid="stStatusWidget"], [data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; height: 0; }

/* sidebar */
section[data-testid="stSidebar"] { background: rgba(10, 9, 20, 0.92); border-right: 1px solid var(--line); min-width: 270px; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { padding-top: 0.6rem; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a { border-radius: 12px; padding: 0.5rem 0.8rem; margin: 0.15rem 0.35rem; font-weight: 500; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span { color: #cfc9e6; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover { background: rgba(255,255,255,0.06); }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] { background: var(--grad) !important; box-shadow: 0 6px 20px rgba(168,85,247,0.35); }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span { color: #fff; font-weight: 700; }
section[data-testid="stSidebar"] [data-testid="stSidebarNav"]::before {
  content: "VAJRA · MERCHANTDNA"; display: block; font-weight: 800; letter-spacing: 0.22em; font-size: 0.74rem; color: var(--pink); padding: 0.4rem 1rem 1rem; }
.side-foot { font-size: 0.82rem; color: var(--muted); line-height: 1.55; padding: 0.9rem 1rem; margin: 0 0.3rem;
             border: 1px solid var(--line); border-radius: 14px; background: var(--card); }
.side-foot b { color: var(--ink); }

/* page header */
.page-head { margin: 0 0 1.4rem; padding-bottom: 1.1rem; border-bottom: 1px solid var(--line); }
.page-head .kicker { display: inline-block; border: 1.5px solid rgba(168,85,247,0.75); border-radius: 999px; padding: 0.35rem 1rem;
  color: #ede9fe; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; font-size: 0.72rem; margin-bottom: 0.9rem; }
.page-head h1 { font-size: 2.6rem; font-weight: 900; margin: 0; line-height: 1.1; letter-spacing: -0.02em;
  background: linear-gradient(90deg, #c4b5fd 0%, #f0abfc 50%, #f9a8d4 100%); -webkit-background-clip: text; background-clip: text; color: transparent; }
.page-head .sub { color: #cfc9e6; font-size: 1.08rem; margin-top: 0.5rem; max-width: 72rem; }
.page-head .sub b { color: #fff; }

/* section titles */
.sec { display: flex; align-items: baseline; gap: 0.9rem; margin: 1.7rem 0 0.8rem; }
.sec h2 { font-size: 0.86rem; font-weight: 700; margin: 0; color: var(--pink); letter-spacing: 0.22em; text-transform: uppercase; }
.sec span { color: var(--muted); font-size: 0.92rem; }
.sec.first { margin-top: 0.2rem; }

/* glass cards */
.kpis { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 0.9rem; margin: 0.2rem 0 1.2rem; }
.kpi, .hero, .mcard, .step, .panel, .verdict {
  background: linear-gradient(160deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02)); border: 1px solid var(--line);
  border-radius: 18px; backdrop-filter: blur(6px); }
.kpi { padding: 1rem 1.15rem 0.95rem; position: relative; overflow: hidden; }
.kpi::before { content: ""; position: absolute; left: 0; right: 0; top: 0; height: 3px; background: var(--tone, #a855f7); }
.kpi .l { color: var(--muted); font-size: 0.8rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.35rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.kpi .v { font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; color: #fff; }
.kpi .s { color: var(--muted); font-size: 0.85rem; margin-top: 0.35rem; }
.kpi .s.up { color: #4ade80; font-weight: 600; } .kpi .s.down { color: #fb7185; font-weight: 600; }

/* bordered streamlit containers = glass panels */
[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) {
  background: linear-gradient(160deg, rgba(255,255,255,0.065), rgba(255,255,255,0.02)); border-radius: 18px; margin-bottom: 0.9rem; }
[data-testid="stVerticalBlockBorderWrapper"]:not(.st-emotion-cache-0) > div { border: 1px solid var(--line) !important; border-radius: 18px !important; }
.panel { padding: 1.1rem 1.3rem; }
.ptitle { font-size: 1.08rem; font-weight: 700; margin: 0 0 0.6rem; color: #fff; }
.ptitle span { color: var(--muted); font-weight: 500; font-size: 0.88rem; margin-left: 0.5rem; }

/* badges and chips */
.badge { display: inline-block; padding: 0.24rem 0.85rem; border-radius: 999px; color: #fff; font-weight: 800; font-size: 0.85rem; letter-spacing: 0.1em; vertical-align: middle; box-shadow: 0 4px 14px rgba(0,0,0,0.35); }
.chip { display: inline-block; padding: 0.2rem 0.75rem; border-radius: 999px; background: rgba(168,85,247,0.18); color: #e9d5ff; font-weight: 600; font-size: 0.82rem; margin-right: 0.35rem; border: 1px solid rgba(168,85,247,0.35); }
.chip.grey { background: rgba(255,255,255,0.06); color: #d4d0e6; border-color: var(--line); }
.chip.green { background: rgba(34,197,94,0.15); color: #86efac; border-color: rgba(34,197,94,0.35); }
.chip.red { background: rgba(244,63,94,0.15); color: #fda4af; border-color: rgba(244,63,94,0.35); }
.chip.amber { background: rgba(245,158,11,0.15); color: #fcd34d; border-color: rgba(245,158,11,0.35); }

/* merchant header card */
.mcard { display: flex; gap: 1.5rem; align-items: center; padding: 1.2rem 1.5rem; }
.mcard .name { font-size: 1.6rem; font-weight: 800; color: #fff; letter-spacing: -0.015em; }
.mcard .meta { color: var(--muted); margin: 0.3rem 0 0.6rem; }
.mcard .facts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.65rem 1.4rem; margin-top: 0.5rem; }
.mcard .facts .k { color: var(--pink); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.14em; }
.mcard .facts .f { font-weight: 700; font-size: 1.04rem; color: #fff; }

/* hero cards on Home */
.hero { padding: 1.25rem 1.35rem 1.05rem; height: 19.5rem; display: flex; flex-direction: column; }
.hero .top { display: flex; justify-content: space-between; align-items: flex-start; gap: 0.8rem; }
.hero .name { font-size: 1.28rem; font-weight: 800; color: #fff; }
.hero .blurb { color: var(--muted); font-size: 0.95rem; margin: 0.3rem 0 0.8rem; min-height: 2.9rem; }
.hero .row { display: flex; justify-content: space-between; align-items: center; margin-top: auto; }
.hero .kv { font-size: 0.78rem; color: var(--pink); letter-spacing: 0.12em; text-transform: uppercase; font-weight: 700; }
.hero .kv b { color: #fff; display: block; font-size: 0.98rem; letter-spacing: 0; text-transform: none; font-weight: 700; margin-top: 0.15rem; }

/* verdict + checks */
.verdict { padding: 1rem 1.2rem; }
.verdict .t { font-weight: 800; font-size: 1.15rem; margin-bottom: 0.4rem; }
.verdict p { margin: 0.3rem 0; font-size: 0.98rem; color: #e4e0f3; }
.checks div { padding: 0.4rem 0; border-bottom: 1px dashed var(--line); color: #e4e0f3; }
.checks .ok::before { content: "✓"; color: #4ade80; font-weight: 800; margin-right: 0.6rem; }
.checks .bad::before { content: "✗"; color: #fb7185; font-weight: 800; margin-right: 0.6rem; }
.ev li { margin: 0.35rem 0; }

/* gradient call-out bar (as on the deck) */
.callout { background: var(--grad); color: #fff; font-weight: 700; font-size: 1.1rem; border-radius: 14px; padding: 0.9rem 1.3rem; margin: 0.4rem 0 0.8rem; }

/* how-it-works steps */
.steps { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0.9rem; }
.step { padding: 1.05rem 1.1rem; }
.step .n { width: 2.2rem; height: 2.2rem; border-radius: 999px; background: linear-gradient(135deg,#a855f7,#ec4899); color: #fff; font-weight: 800; display: grid; place-items: center; margin-bottom: 0.7rem; }
.step .t { font-weight: 700; margin-bottom: 0.3rem; color: #fff; } .step .d { color: var(--muted); font-size: 0.92rem; }

/* budget bar */
.bar { background: rgba(255,255,255,0.08); border-radius: 999px; height: 12px; overflow: hidden; }
.bar > div { height: 100%; background: var(--grad); }

/* widgets */
.stButton > button, .stDownloadButton > button { border-radius: 12px; font-weight: 600; padding: 0.55rem 1.1rem;
  border: 1px solid rgba(168,85,247,0.55); background: rgba(168,85,247,0.08); color: #f1eefb; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color: #ec4899; color: #fff; background: rgba(236,72,153,0.12); }
.stButton > button[kind="primary"] { background: var(--grad); border: none; color: #fff; box-shadow: 0 8px 24px rgba(192,38,211,0.35); }
div[data-baseweb="select"] > div { border-radius: 12px; border-color: var(--line); background: rgba(255,255,255,0.05); }
span[data-baseweb="tag"] { background: linear-gradient(90deg,#7c3aed,#c026d3) !important; }
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; } .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 1rem; padding: 0.4rem 0.9rem; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 14px; overflow: hidden; }
[data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 14px; background: var(--card); }
.stAlert { border-radius: 14px; } hr { border-color: var(--line); }
[data-testid="stWidgetLabel"] p { font-weight: 600; color: #cfc9e6; font-size: 0.9rem; }
.stCaption, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: 0.88rem !important; }
</style>
"""

TEMPLATE = go.layout.Template(layout=go.Layout(
    font=dict(family="Inter, Segoe UI, sans-serif", size=14, color=INK),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=PALETTE,
    margin=dict(l=55, r=20, t=40, b=50),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)", linecolor="rgba(255,255,255,0.12)", tickfont=dict(color=MUTED), title_font=dict(color=MUTED), automargin=True),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)", linecolor="rgba(255,255,255,0.12)", tickfont=dict(color=MUTED), title_font=dict(color=MUTED), automargin=True),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)", font=dict(size=13)),
    hoverlabel=dict(bgcolor="#1a1530", bordercolor="#a855f7", font=dict(color="white", size=13)),
    title=dict(font=dict(size=16, color=INK), x=0, xanchor="left"),
))


# ---------------------------------------------------------------- setup
def setup(title: str, icon: str = "◆") -> None:
    """Page config, CSS, Plotly template and sidebar footer. Call first on every page."""
    st.set_page_config(page_title=f"MerchantDNA · {title}", page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    slug = title.replace(" ", "_")                          # active nav item: matched by its URL
    st.markdown(f'<style>section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][href$="/{slug}"] '
                '{ background: linear-gradient(90deg,#7c3aed,#c026d3 55%,#f97316) !important; '
                'box-shadow: 0 6px 20px rgba(168,85,247,0.35); } '
                f'section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][href$="/{slug}"] span '
                '{ color:#fff !important; font-weight:700; }</style>', unsafe_allow_html=True)
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
            f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="{sw}"/>'
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
    tone = ("green", "rgba(34,197,94,0.10)") if status == "Cleared" else (("grey", "rgba(255,255,255,0.04)") if status == "Nothing to explain" else ("red", "rgba(244,63,94,0.10)"))
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
                           marker=dict(color=["#f43f5e" if x["contribution"] > 0 else "#22c55e" for x in d],
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
        sty = sty.map(lambda t: f"background-color:{TIER_SOFT.get(t, 'transparent')};color:{TIER_COLOR.get(t, INK)};font-weight:700",
                      subset=[tier_col])
    if highlight_row is not None:
        sty = sty.apply(lambda r: ["background-color:rgba(168,85,247,0.22);font-weight:700" if r.name == highlight_row else "" for _ in r], axis=1)
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
