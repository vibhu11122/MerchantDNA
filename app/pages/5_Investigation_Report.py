"""Investigation Report: everything an analyst needs to decide, exportable."""
from __future__ import annotations

import streamlit as st

import data
import theme
from merchantdna.decision.explain_step import REASONS
from merchantdna.decision.report import investigation_markdown, markdown_to_pdf

theme.setup("Investigation Report")
theme.need_artefacts()
s, ev_all = data.scores(), data.evidence()

theme.page_header("Investigation Report", "The audit trail for one merchant: score, reasons, evidence, the Innocence "
                  "assessment, network findings, the merchant's own explanation and the recommended action.")
mid = theme.merchant_picker(s, "rep")
r, ev = s.loc[mid], dict(ev_all[mid])

theme.merchant_header(r, ev)
st.markdown("")

left, right = st.columns([1, 1.6])
with left, st.container(border=True):
    st.markdown('<div class="ptitle">Merchant "Explain" step <span>before any hold</span></div>', unsafe_allow_html=True)
    st.caption("The merchant may give a reason. We test the claim against the data and record the result either way.")
    reason = st.radio("Merchant's stated reason", ["(no explanation yet)"] + REASONS)
    if reason != "(no explanation yet)":
        claim = ev["claims"][reason]
        ev["claim"] = claim
        tone, col = ("green", "rgba(34,197,94,0.10)") if claim["accepted"] else ("red", "rgba(244,63,94,0.10)")
        st.markdown(f'<div class="verdict" style="background:{col}"><div class="t" style="color:{theme.TONE[tone]}">'
                    f'{"Claim consistent with the data" if claim["accepted"] else "Claim not supported by the data"}</div></div>',
                    unsafe_allow_html=True)
        theme.checks(claim)
    st.markdown("")
    md = investigation_markdown(ev)
    c = st.columns(2)
    c[0].download_button("⬇ Markdown", md, file_name=f"report_{mid}.md", mime="text/markdown", use_container_width=True)
    c[1].download_button("⬇ PDF", markdown_to_pdf(md), file_name=f"report_{mid}.pdf", mime="application/pdf",
                         use_container_width=True)
with right, st.container(border=True):
    st.markdown(md)
