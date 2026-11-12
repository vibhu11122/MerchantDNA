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

theme.setup("Model Lab", "🧪")
theme.need_artefacts()
s, m, cfg = data.scores(), data.metrics(), data.config()

st.title("🧪 Model Lab")
st.caption(f"Measured on {m['dataset']['evaluated']} merchants the models never saw labels for "
           f"({m['dataset']['fraud_in_eval']} of them fraud). Synthetic data: read these as a proof of method, not a forecast.")

# ---------------------------------------------------------------- results
st.header("1 · MerchantDNA vs baselines")
names = {"static_rules": "Static rules", "static_rules_plus_innocence_gate": "Static rules + Innocence gate",
         "isolation_forest": "Isolation Forest", "merchantdna": "MerchantDNA"}
rows = []
for k, label in names.items():
    b = m["methods"][k]
    rows.append({"Method": label, "PR-AUC": f"{b['pr_auc']:.2f} ({b['pr_auc_lo']:.2f}-{b['pr_auc_hi']:.2f})",
                 "Recall @ 2% budget": b["at_review_budget"]["recall"],
                 "Precision @ 2% budget": b["at_review_budget"]["precision"],
                 "False alarms on festival-surge merchants": b["at_native_threshold"]["surge_fpr"],
                 "False alarms on all honest merchants": b["at_native_threshold"]["fpr"]})
st.dataframe(pd.DataFrame(rows).set_index("Method").style.format(
    {c: "{:.0%}" for c in ["Recall @ 2% budget", "Precision @ 2% budget",
                           "False alarms on festival-surge merchants", "False alarms on all honest merchants"]}),
    use_container_width=True)
st.caption("False alarms are measured at each method's own threshold (rules fire / Isolation Forest outlier / "
           "MerchantDNA MEDIUM or above). The 2% budget = what analysts can review.")

a, b = st.columns(2)
with a:
    fig = go.Figure()
    for label, c in m["pr_curves"].items():
        fig.add_trace(go.Scatter(x=c["recall"], y=c["precision"], name=label, line=dict(width=3)))
    fig.update_layout(height=400, font=dict(size=16), xaxis_title="Recall", yaxis_title="Precision",
                      title="Precision-recall curves", margin=dict(t=50))
    st.plotly_chart(fig, use_container_width=True)
with b:
    st.subheader("Ablation: remove one pillar")
    abl = pd.DataFrame({k: {"PR-AUC": v["pr_auc"], "SweetCrust": v["hero_scores"]["M0000"],
                            "FreshOven": v["hero_scores"]["M0001"], "QuickKart": v["hero_scores"]["M0002"]}
                        for k, v in m["ablations"].items()}).T
    st.dataframe(abl.style.format("{:.2f}", subset=["PR-AUC"]).format("{:.0f}", subset=["SweetCrust", "FreshOven", "QuickKart"]),
                 use_container_width=True)
    st.markdown("**Reading it honestly:** payer-side features carry the most weight. Without them QuickKart "
                "drops to LOW. The Innocence Engine adds little to *this* stacker because the stacker already "
                "ignores raw volume. Bolted onto static volume rules, it halves their festival false alarms.")
    st_ = m["stress_test_adaptive_mimic"]
    lt = m["slow_drift_lead_time"]
    st.markdown(f"**Adaptive mimic stress test:** {st_['recall_at_medium_tier']:.0%} of mimics still reach "
                f"MEDIUM or above (rules: {st_['recall_static_rules_native']:.0%}, Isolation Forest: "
                f"{st_['recall_isolation_forest_native']:.0%}).  \n**Slow drift:** caught a median "
                f"**{lt['median_lead_vs_rules_days']:.0f} days** before the rules and "
                f"**{lt['median_lead_vs_iforest_days']:.0f} days** before Isolation Forest "
                f"({lt['detected_by_merchantdna']}/{lt['n']} detected).")

with st.expander("False-alarm rate by merchant type (MEDIUM or above)"):
    pa = pd.DataFrame(m["per_archetype"]).T.sort_values("flagged_medium_or_high")
    st.dataframe(pa.style.format({"n": "{:.0f}", "flagged_medium_or_high": "{:.0%}", "median_score": "{:.1f}"}),
                 use_container_width=True)
    st.caption("Archetypes are simulator ground truth, shown only here for evaluation.")

# ---------------------------------------------------------------- costs
st.header("2 · What should we do? The cost trade-off")
c = st.columns(3)
d = cfg["decision"]
harm = c[0].slider("Cost of missing a betting front (INR)", 50_000, 2_000_000, d["harm_if_missed"], 50_000)
cost = c[1].slider("Cost of wrongly disrupting an honest merchant (INR)", 50_000, 2_000_000, d["cost_disrupt_legit"], 50_000)
cap = c[2].slider("Analyst capacity (merchants per cycle)", 5, 100, d["analyst_capacity"], 5)
th = rung_thresholds(cfg, harm, cost)
rungs = choose_rungs(s["p_drift"], cfg, harm, cost, cap)
grid = np.linspace(0, 1, 201)
nb = net_benefits(grid, cfg, harm, cost)
fig = go.Figure([go.Scatter(x=grid * 100, y=nb[:, i], name=r[0], line=dict(width=3)) for i, r in enumerate(d["rungs"])])
fig.update_layout(height=380, font=dict(size=15), xaxis_title="Risk score (= P(drift) x 100)",
                  yaxis_title="Expected net benefit (INR)", margin=dict(t=10))
left, right = st.columns([1.4, 1])
left.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("**Each action becomes worth it at:**")
    for r, t in zip(d["rungs"][1:], th[1:]):
        st.markdown(f"- {r[0]}: risk ≥ **{100 * t:.0f}**")
    st.metric("Merchants needing review", int((rungs["rung_index"] > 0).sum()),
              f"{int(rungs['awaiting_capacity'].sum())} over capacity", delta_color="off")
    st.dataframe(rungs["rung"].value_counts(), use_container_width=True)

# ---------------------------------------------------------------- live controls
st.header("3 · Try to break it (live re-scoring)")


@st.cache_resource(show_spinner=False)
def lab_context():
    return (data.artifact("bundle"), build_context(cfg), data.table("daily_counts"),
            data.artifact("cohort_stats"), data.artifact("payer_roaming_current"),
            data.table("features_current").set_index("merchant_id"))


def run(mid: str, tx: pd.DataFrame) -> dict:
    b, ctx, daily, stats, roam, pop = lab_context()
    return rescore(b, ctx, tx, data.merchant_settlements(mid), daily, stats, roam, pop, mid)


def show(before: pd.Series, after: dict) -> None:
    k = st.columns(3)
    k[0].metric("Risk before", f"{before['risk_score']:.0f}", before["tier"], delta_color="off")
    k[1].metric("Risk after", f"{after['risk_score']:.0f}", f"{after['risk_score'] - before['risk_score']:+.0f}",
                delta_color="inverse")
    k[2].metric("Tier / action after", after["tier"], after["rung"], delta_color="off")
    st.markdown(f"**Innocence Engine:** {after['innocence']['status']} — {after['innocence']['volume_text']} "
                f"{after['innocence']['composition_text']}")
    st.plotly_chart(theme.drivers_chart(after["drivers"]), use_container_width=True)


cal = data.calendar()
rng = np.random.default_rng(cfg["seed"])
t1, t2 = st.tabs(["Inject a Diwali spike into a genuine bakery", "Make FreshOven mimic a bakery"])
with t1:
    bakeries = s[(s["declared_category"] == "bakery") & (s["tier"] == "LOW") & (~s["volume_up"])].index.tolist()
    c = st.columns(3)
    mid = c[0].selectbox("Genuine bakery", bakeries, format_func=lambda x: f"{s.loc[x, 'name']} ({x})")
    factor = c[1].slider("Peak volume vs usual", 3, 15, 10)
    when = c[2].radio("When", ["During Diwali (peers also spiked)", "An ordinary week (no festival)"])
    if st.button("Inject spike and re-score", type="primary"):
        tx = data.merchant_txns(mid)
        shape = festival_shape(cal, factor, tx) if when.startswith("During") else week_shape(cal, len(cal) - 30, factor)
        with st.spinner("Re-running the full pipeline for this merchant..."):
            after = run(mid, inject_spike(tx, shape, rng))
        show(s.loc[mid], after)
        st.info("Same amounts, hours and payer mix, just more of them. During Diwali the peers rose too, so the "
                "volume is explained. In an ordinary week it is not explained, but volume alone never makes a "
                "merchant high risk.")
with t2:
    jitter = st.slider("Amount jitter around 499/999/1999", 0.0, 0.3, 0.15, 0.05)
    if st.button("Copy a bakery's hours + jitter amounts, then re-score", type="primary"):
        tx = data.merchant_txns("M0001")
        hourly = cfg["sim"]["categories"]["bakery"]["hourly"]
        with st.spinner("Re-running the full pipeline for FreshOven..."):
            after = run("M0001", make_mimic(tx, hourly, cal["date"].iloc[-cfg["features"]["window_long"]], jitter, rng))
        show(s.loc["M0001"], after)
        st.info("Hours and price points can be faked. Who pays (repeat payers from many cities, shared with other "
                "flagged merchants) is much harder to fake. Those signals still fire.")
