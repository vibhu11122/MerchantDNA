"""Investigation Report: everything an analyst needs to decide, exportable."""
from __future__ import annotations

import streamlit as st

import data
import theme
from merchantdna.decision.explain_step import REASONS
from merchantdna.decision.report import investigation_markdown, markdown_to_pdf

theme.setup("Investigation Report", "📄")
theme.need_artefacts()
s, ev_all = data.scores(), data.evidence()

st.title("📄 Investigation Report")
mid = theme.merchant_picker(s, "rep")
ev = dict(ev_all[mid])

st.subheader("Merchant \"Explain\" step")
st.markdown("Before any hold, the merchant may give a reason. We check the claim against the data and record the result.")
reason = st.radio("Merchant's stated reason", ["(no explanation yet)"] + REASONS, horizontal=True)
if reason != "(no explanation yet)":
    claim = ev["claims"][reason]
    ev["claim"] = claim
    (st.success if claim["accepted"] else st.error)(claim["summary"])
    for k in claim["checks"]:
        st.markdown(f"{'✅' if k['passed'] else '❌'} {k['check']}")

md = investigation_markdown(ev)
st.divider()
st.markdown(md)
c = st.columns(2)
c[0].download_button("Download report (Markdown)", md, file_name=f"report_{mid}.md", mime="text/markdown")
c[1].download_button("Download report (PDF)", markdown_to_pdf(md), file_name=f"report_{mid}.pdf",
                     mime="application/pdf")
