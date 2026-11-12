"""MerchantDNA dashboard - home page. Run with `make app`."""
from __future__ import annotations

import streamlit as st

import data
import theme

theme.setup("Home")
theme.need_artefacts()
s, m = data.scores(), data.metrics()

st.markdown('<div class="kicker">Follow the Money · PayU × IIM Bangalore</div>', unsafe_allow_html=True)
st.title("MerchantDNA")
st.markdown('<p style="font-size:1.35rem;font-weight:600;line-height:1.4;color:#1e293b">Learns what a legitimate '
            'business looks like from <span style="color:#1d4ed8">behaviour, not paperwork</span>, tests every deviation '
            'against legitimate explanations, then responds proportionately.</p>', unsafe_allow_html=True)
st.markdown('<p class="note">We detect <b>purpose drift</b>: behaviour that does not fit the declared '
            'category. Betting collection is the motivating case. These are signals, not proof: a human '
            'analyst decides. All data on this page is synthetic.</p>', unsafe_allow_html=True)

c = st.columns(4)
c[0].metric("Merchants monitored", f"{len(s):,}")
c[1].metric("High risk", int((s["tier"] == "HIGH").sum()))
c[2].metric("Medium risk", int((s["tier"] == "MEDIUM").sum()))
md = m["methods"]["merchantdna"]
c[3].metric("PR-AUC vs Isolation Forest", f"{md['pr_auc']:.2f}",
            f"{md['pr_auc'] - m['methods']['isolation_forest']['pr_auc']:+.2f}")

st.markdown("## The three demo merchants")
cols = st.columns(3)
blurbs = {"M0000": "Genuine bakery. Volume up ~10x at Diwali.",
          "M0001": "Registered as a bakery. Starts behaving differently mid-period.",
          "M0002": "Looks like a normal grocery. Shares a device with other merchants."}
for col, (mid, name) in zip(cols, theme.HEROES.items()):
    r = s.loc[mid]
    col.markdown(f'<div class="card"><h3>{name}</h3><p>{blurbs[mid]}</p>'
                 f'<p>Risk <b style="font-size:1.6rem">{r["risk_score"]:.0f}</b> / 100 &nbsp; {theme.tier_badge(r["tier"])}</p>'
                 f'<p><b>Action:</b> {r["rung"]}<br><b>Innocence check:</b> {r["innocence_status"]}</p></div>',
                 unsafe_allow_html=True)
    with col:
        theme.open_page("pages/2_Merchant_Deep_Dive.py", mid, f"Open {name.split()[0]} →", key=f"open_{mid}")

st.markdown("## How it works")
st.markdown("""
1. **Claimed profile.** Does the website read like the declared business? (No website = no penalty.)
2. **Behaviour.** Does the merchant *behave* like its category: hours, amounts, payers? Its 12-number "DNA" shows drift.
3. **Network.** Who shares devices, bank accounts or payers with whom? Rare shared identifiers count more.
4. **Innocence Engine.** Before flagging, test legitimate explanations: did peers also spike (festival)? Is the business mix unchanged?
   *A festival explains more sales. It does not explain INR 999 repeats at midnight from payers in 20 states.*
5. **Fusion + action ladder.** One calibrated probability with its top reasons, then the cheapest proportionate action by expected cost.
""")
