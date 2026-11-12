"""Model Lab (for judges): honest metrics, the cost trade-off, and two live 'break it' controls."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import data
import theme
from merchantdna.decision.ladder import choose_rungs, net_benefits, rung_thresholds
from merchantdna.features.windows import build_context
from merchantdna.models.rescore import festival_shape, inject_spike, make_mimic, rescore, week_shape

theme.setup("Model Lab")
theme.need_artefacts()
s, m, cfg = data.scores(), data.metrics(), data.config()
ds = m["dataset"]

theme.page_header("Model Lab", f"Measured on <b>{ds['evaluated']} merchants</b> the models never saw labels for "
                  f"({ds['fraud_in_eval']} of them fraud). Synthetic data: read these as a proof of method, not a forecast.")

# ---------------------------------------------------------------- results
theme.section("1 · MerchantDNA vs baselines", first=True)
md, iso, rules = m["methods"]["merchantdna"], m["methods"]["isolation_forest"], m["methods"]["static_rules"]
lt, st_ = m["slow_drift_lead_time"], m["stress_test_adaptive_mimic"]
theme.kpis([
    {"label": "PR-AUC", "value": f"{md['pr_auc']:.2f}", "sub": f"Isolation Forest {iso['pr_auc']:.2f} · rules {rules['pr_auc']:.2f}",
     "tone": "green"},
    {"label": "Festival false alarms", "value": f"{md['at_native_threshold']['surge_fpr']:.0%}",
     "sub": f"rules {rules['at_native_threshold']['surge_fpr']:.0%}", "tone": "green"},
    {"label": "Recall at MEDIUM", "value": f"{md['at_native_threshold']['recall']:.0%}",
     "sub": f"precision {md['at_native_threshold']['precision']:.0%}", "tone": "blue"},
    {"label": "Slow drift caught earlier", "value": f"{lt['median_lead_vs_rules_days']:.0f} days",
     "sub": f"than rules · {lt['median_lead_vs_iforest_days']:.0f} d than Isolation Forest", "tone": "violet"},
    {"label": "Adaptive mimics caught", "value": f"{st_['recall_at_medium_tier']:.0%}",
     "sub": f"baselines {st_['recall_static_rules_native']:.0%} / {st_['recall_isolation_forest_native']:.0%}", "tone": "amber"},
])

names = {"static_rules": "Static rules", "static_rules_plus_innocence_gate": "Static rules + Innocence gate",
         "isolation_forest": "Isolation Forest", "merchantdna": "MerchantDNA"}
rows = []
for k, label in names.items():
    b = m["methods"][k]
    rows.append({"Method": label, "PR-AUC": b["pr_auc"], "90% interval": f"{b['pr_auc_lo']:.2f} – {b['pr_auc_hi']:.2f}",
                 "Recall @ 2% budget": b["at_review_budget"]["recall"],
                 "Precision @ 2% budget": b["at_review_budget"]["precision"],
                 "False alarms (festival)": b["at_native_threshold"]["surge_fpr"],
                 "False alarms (honest)": b["at_native_threshold"]["fpr"]})
tbl = pd.DataFrame(rows).set_index("Method")
pct = ["Recall @ 2% budget", "Precision @ 2% budget", "False alarms (festival)", "False alarms (honest)"]
left, right = st.columns([1.35, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Head to head <span>false alarms at each method\'s own threshold</span></div>', unsafe_allow_html=True)
    st.dataframe(theme.style_table(tbl, {**{c: "{:.0%}" for c in pct}, "PR-AUC": "{:.2f}"}, highlight_row="MerchantDNA"),
                 use_container_width=True)
    st.caption("The 2% budget = the 14 merchants analysts can review. Both good methods are budget-bound there; "
               "at MerchantDNA's own MEDIUM threshold recall is 97%.")
with right, st.container(border=True):
    st.markdown('<div class="ptitle">Precision–recall curves</div>', unsafe_allow_html=True)
    fig = go.Figure()
    for (label, c), col in zip(m["pr_curves"].items(), [theme.MUTED, "#0891b2", "#dc2626"]):
        fig.add_trace(go.Scatter(x=c["recall"], y=c["precision"], name=label, line=dict(width=3, color=col, shape="hv")))
    fig.update_layout(height=250, xaxis_title="Recall", yaxis_title="Precision", margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True, theme=None)

a, b = st.columns([1, 1.2])
with a, st.container(border=True):
    st.markdown('<div class="ptitle">Ablation <span>remove one pillar, retrain</span></div>', unsafe_allow_html=True)
    abl = pd.DataFrame({k.replace("_", " "): {"PR-AUC": v["pr_auc"], "SweetCrust": v["hero_scores"]["M0000"],
                        "FreshOven": v["hero_scores"]["M0001"], "QuickKart": v["hero_scores"]["M0002"]}
                        for k, v in m["ablations"].items()}).T
    st.dataframe(abl.style.format({"PR-AUC": "{:.2f}", "SweetCrust": "{:.0f}", "FreshOven": "{:.0f}", "QuickKart": "{:.0f}"}),
                 use_container_width=True)
with b, st.container(border=True):
    st.markdown('<div class="ptitle">Reading it honestly</div>', unsafe_allow_html=True)
    st.markdown("- **Payer-side features carry the most weight.** Without them PR-AUC falls to "
                f"{m['ablations']['no_payer_features']['pr_auc']:.2f} and QuickKart drops to LOW.\n"
                "- **The Innocence Engine barely moves this stacker's PR-AUC** — the stacker already ignores raw volume. "
                f"Bolted onto static rules it cuts their festival false alarms from {rules['at_native_threshold']['surge_fpr']:.0%} "
                f"to {m['methods']['static_rules_plus_innocence_gate']['at_native_threshold']['surge_fpr']:.0%}.\n"
                "- **The network adds explanation more than lift** here: ring members already look suspicious on their own.")
with st.expander("False-alarm rate by merchant type (MEDIUM or above) — simulator ground truth, evaluation only"):
    pa = pd.DataFrame(m["per_archetype"]).T.sort_values("flagged_medium_or_high")
    pa.index = pa.index.str.replace("_", " ")
    st.dataframe(pa.rename(columns={"n": "Merchants", "flagged_medium_or_high": "Flagged", "median_score": "Median score"})
                 .style.format({"Merchants": "{:.0f}", "Flagged": "{:.0%}", "Median score": "{:.1f}"}), use_container_width=True)

# ---------------------------------------------------------------- costs
theme.section("2 · What should we do?", "the action is chosen by expected cost — your risk appetite is a dial")
d = cfg["decision"]
with st.container(border=True):
    c = st.columns(3)
    harm = c[0].slider("Cost of missing a betting front (₹)", 50_000, 2_000_000, d["harm_if_missed"], 50_000)
    cost = c[1].slider("Cost of wrongly disrupting an honest merchant (₹)", 50_000, 2_000_000, d["cost_disrupt_legit"], 50_000)
    cap = c[2].slider("Analyst capacity (merchants per cycle)", 5, 100, d["analyst_capacity"], 5)
th = rung_thresholds(cfg, harm, cost)
rungs = choose_rungs(s["p_drift"], cfg, harm, cost, cap)
grid = np.linspace(0, 1, 201)
nb = net_benefits(grid, cfg, harm, cost)
left, right = st.columns([1.5, 1])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Expected net benefit of each action <span>vs risk score</span></div>', unsafe_allow_html=True)
    fig = go.Figure([go.Scatter(x=grid * 100, y=nb[:, i], name=r[0].split(" (")[0], line=dict(width=3)) for i, r in enumerate(d["rungs"])])
    fig.update_layout(height=330, xaxis_title="Risk score (= P(drift) × 100)", yaxis_title="Net benefit (₹)")
    st.plotly_chart(fig, use_container_width=True, theme=None)
with right, st.container(border=True):
    st.markdown('<div class="ptitle">Each action becomes worth it at</div>', unsafe_allow_html=True)
    rows_html = "".join(f'<div style="display:flex;justify-content:space-between;padding:0.4rem 0;border-bottom:1px dashed {theme.LINE}">'
                        f'<span>{theme.esc(r[0])}</span><b>risk ≥ {100 * t:.0f}</b></div>' for r, t in zip(d["rungs"][1:], th[1:]))
    st.markdown(rows_html, unsafe_allow_html=True)
    st.markdown("")
    theme.kpis([{"label": "Need review", "value": int((rungs["rung_index"] > 0).sum()),
                 "sub": f"{int(rungs['awaiting_capacity'].sum())} over capacity", "tone": "violet"},
                {"label": "Suspend", "value": int((rungs["rung_index"] == 4).sum()), "tone": "red"}])

# ---------------------------------------------------------------- live controls
theme.section("3 · Try to break it", "edits one merchant's transactions and re-runs the whole pipeline in under a second")


@st.cache_resource(show_spinner=False)
def lab_context():
    return (data.artifact("bundle"), build_context(cfg), data.table("daily_counts"),
            data.artifact("cohort_stats"), data.artifact("payer_roaming_current"),
            data.table("features_current").set_index("merchant_id"))


def run(mid: str, tx: pd.DataFrame) -> dict:
    b, ctx, daily, stats, roam, pop = lab_context()
    return rescore(b, ctx, tx, data.merchant_settlements(mid), daily, stats, roam, pop, mid)


def show(before: pd.Series, after: dict) -> None:
    delta = after["risk_score"] - before["risk_score"]
    theme.kpis([
        {"label": "Risk before", "value": f"{before['risk_score']:.0f}", "sub": before["tier"], "tone": "grey"},
        {"label": "Risk after", "value": f"{after['risk_score']:.0f}", "sub": f"{delta:+.0f} · {after['tier']}",
         "tone": {"HIGH": "red", "MEDIUM": "amber", "LOW": "green"}[after["tier"]], "trend": "up" if delta < 0 else "down"},
        {"label": "Action after", "value": after["rung"].split(" (")[0], "tone": "blue"},
    ])
    a, b = st.columns([1, 1])
    with a:
        theme.verdict_panel(after["innocence"])
    with b:
        st.plotly_chart(theme.drivers_chart(after["drivers"], height=260), use_container_width=True, theme=None)


cal = data.calendar()
rng = np.random.default_rng(cfg["seed"])
t1, t2 = st.tabs(["Inject a Diwali spike into a genuine bakery", "Make FreshOven mimic a bakery"])
with t1, st.container(border=True):
    bakeries = s[(s["declared_category"] == "bakery") & (s["tier"] == "LOW") & (~s["volume_up"])].index.tolist()
    c = st.columns([1.4, 1, 1.4])
    mid = c[0].selectbox("Genuine bakery", bakeries, format_func=lambda x: f"{s.loc[x, 'name']} ({x})")
    factor = c[1].slider("Peak volume vs usual", 3, 15, 10)
    when = c[2].radio("When", ["During Diwali (peers also spiked)", "An ordinary week (no festival)"])
    if st.button("Inject spike and re-score", type="primary"):
        tx = data.merchant_txns(mid)
        shape = festival_shape(cal, factor, tx) if when.startswith("During") else week_shape(cal, len(cal) - 30, factor)
        with st.spinner("Re-running the full pipeline for this merchant…"):
            after = run(mid, inject_spike(tx, shape, rng))
        show(s.loc[mid], after)
        st.info("Same amounts, hours and payer mix — just more of them. During Diwali the peers rose too, so the "
                "volume is explained. In an ordinary week it is not explained, but volume alone never makes a merchant high risk.")
with t2, st.container(border=True):
    jitter = st.slider("Amount jitter around ₹499 / 999 / 1999", 0.0, 0.3, 0.15, 0.05)
    if st.button("Copy a bakery's hours + jitter amounts, then re-score", type="primary"):
        tx = data.merchant_txns("M0001")
        hourly = cfg["sim"]["categories"]["bakery"]["hourly"]
        with st.spinner("Re-running the full pipeline for FreshOven…"):
            after = run("M0001", make_mimic(tx, hourly, cal["date"].iloc[-cfg["features"]["window_long"]], jitter, rng))
        show(s.loc["M0001"], after)
        st.info("Hours and price points can be faked. Who pays — repeat payers from many cities, shared with other "
                "flagged merchants — is much harder to fake. Those signals still fire.")
