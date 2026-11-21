"""MerchantDNA dashboard - home page. Run with `make app`."""
from __future__ import annotations

import streamlit as st

import data
import theme

theme.setup("Home")
theme.need_artefacts()
s, m = data.scores(), data.metrics()
md = m["methods"]["merchantdna"]

theme.page_header(
    "MerchantDNA",
    "Learns what a legitimate business looks like from <b>behaviour, not paperwork</b>, tests every deviation "
    "against legitimate explanations, then responds proportionately. We detect <b>purpose drift</b> — behaviour "
    "that does not fit the declared category. Signals, not proof: a human analyst decides.",
    kicker="Follow the Money · Innovation Challenge")

st.markdown('<div class="callout">Too strict hurts genuine merchants. Too lax lets fraud continue. MerchantDNA explains before it flags.</div>', unsafe_allow_html=True)

flagged = int((s["rung_index"] > 0).sum())
theme.kpis([
    {"label": "Merchants monitored", "value": f"{len(s):,}", "sub": "120 days · 4.7M payments", "tone": "blue"},
    {"label": "Flagged for review", "value": flagged,
     "sub": f"{int((s['tier'] == 'HIGH').sum())} high · {int((s['tier'] == 'MEDIUM').sum())} medium", "tone": "red"},
    {"label": "Festival merchants wrongly flagged", "value": f"{md['at_native_threshold']['surge_fpr']:.0%}",
     "sub": f"static rules: {m['methods']['static_rules']['at_native_threshold']['surge_fpr']:.0%}", "tone": "green"},
])

theme.section("The three demo merchants", "scores come from the models — nothing is hard-coded", first=True)
blurbs = {"M0000": "Genuine bakery with a 10× Diwali spike.",
          "M0001": "Registered as a bakery; starts collecting bets mid-period.",
          "M0002": "Looks like a normal grocery; shares a device with a ring."}
for col, (mid, name) in zip(st.columns(3), theme.HEROES.items()):
    with col:
        st.markdown(theme.hero_card(name, blurbs[mid], s.loc[mid]), unsafe_allow_html=True)
        theme.open_page("pages/1_Merchant_Story.py", mid, f"Open {name.split()[0]} →", key=f"open_{mid}")

theme.section("How it works", "three signal pillars, one arbiter, one proportionate action")
steps = [
    ("Claimed profile", "Does the website read like the declared business? No website = no penalty."),
    ("Behaviour", "Hours, amounts and — above all — who pays. A 12-number DNA fingerprint shows drift."),
    ("Network", "Shared devices, bank accounts, IPs and payers. Rare shared identifiers count more."),
    ("Innocence Engine", "Did peers spike too? Is the mix unchanged? A festival explains more sales, not different sales."),
    ("Fusion + action", "One calibrated probability with its reasons, then the cheapest proportionate action."),
]
st.markdown('<div class="steps">' + "".join(
    f'<div class="step"><div class="n">{i + 1}</div><div class="t">{t}</div><div class="d">{d}</div></div>'
    for i, (t, d) in enumerate(steps)) + "</div>", unsafe_allow_html=True)

theme.section("Top 10 to review", "highest expected benefit first · click a hero card above for the full story")
ev = data.evidence()
q = s[s["rung_index"] > 0].sort_values("net_benefit", ascending=False).head(10).copy()
q["Top reason"] = [ev[i]["drivers"][0]["label"] if ev[i]["drivers"] else "" for i in q.index]
show = q[["name", "declared_category", "risk_score", "tier", "rung", "Top reason"]].rename(columns={
    "name": "Merchant", "declared_category": "Declared", "risk_score": "Risk", "tier": "Tier", "rung": "Recommended action"})
show["Declared"] = show["Declared"].str.replace("_", " ")
st.dataframe(theme.style_table(show, {"Risk": "{:.0f}"}, tier_col="Tier"), use_container_width=True,
             column_config={"Risk": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%d")})

with st.expander("Why this matters: the regulatory hook"):
    st.markdown("Under the **Promotion and Regulation of Online Gaming Act 2025**, payment intermediaries may not "
                "facilitate online-money-game transactions, and the **RBI Payment Aggregator Directions (Sept 2025)** "
                "require continuous monitoring of merchant transactions against the business profile. MerchantDNA turns "
                "that obligation into a working system with an audit trail — down to a drafted STR an analyst can file.")
