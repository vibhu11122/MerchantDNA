"""Evidence sentences and the investigation report (markdown)."""
from __future__ import annotations

from typing import Any

import pandas as pd

# feature, format of the value, sentence template. Shown when the peer z-score is high.
EVIDENCE_RULES = [
    ("pricepoint_share", "{v:.0%} of payments are exactly INR 499 / 999 / 1999 (peers: {m:.1%})."),
    ("night_share", "{v:.0%} of payments happen between midnight and 5 am (peers: {m:.1%})."),
    ("multi_city_payer_share", "{v:.0%} of payers also paid merchants in 3+ different cities (peers: {m:.1%})."),
    ("nonlocal_share", "{v:.0%} of payers are from outside {city} (peers: {m:.0%})."),
    ("repeat_txn_share", "{v:.0%} of payments come from repeat payers (peers: {m:.0%})."),
    ("post_wicket_lift", "Payments are {v:.1f}x more likely in the 10 minutes after a wicket (peers: {m:.1f}x)."),
    ("ipl_evening_lift", "Match evenings are {v:.1f}x busier than other evenings (peers: {m:.1f}x)."),
    ("fast_payout_share", "{v:.0%} of payouts were settled within 12 hours (peers: {m:.0%})."),
    ("burst_index", "Payments arrive in tight bursts (burst index {v:.1f}, peers {m:.1f})."),
]


def evidence_lines(feats: pd.Series, cohort_median: pd.Series, city: str, z_min: float) -> list[str]:
    """Plain-English facts where the merchant is far from its peers."""
    lines = []
    for col, tmpl in EVIDENCE_RULES:
        if feats.get(f"z_{col}", 0) >= z_min:
            lines.append(tmpl.format(v=feats[col], m=cohort_median[col], city=city))
    return lines


def investigation_markdown(ev: dict[str, Any]) -> str:
    """Full investigation report for one merchant, ready to export."""
    L = [f"# Investigation report: {ev['name']} ({ev['merchant_id']})", "",
         f"**Risk score:** {ev['risk_score']:.0f} / 100 ({ev['tier']})  ",
         f"**Recommended action:** {ev['rung']}  ",
         f"**Declared category:** {ev['declared_category']} · **City:** {ev['city']}  ",
         f"**Behaves like:** {ev['behaves_like']} (P = {ev['behaves_like_p']:.0%}); "
         f"P(behaves like declared) = {ev['verifier_p_declared']:.0%}", "",
         "> Signals, not proof. A human analyst makes the final decision.", "",
         "## Why this score (top drivers)"]
    for d in ev["drivers"]:
        arrow = "raises" if d["contribution"] > 0 else "lowers"
        L.append(f"- {d['label']} — {arrow} risk ({d['contribution']:+.2f} log-odds)")
    L += ["", "## Evidence"] + [f"- {e}" for e in ev["evidence"] or ["No individual signal is far from peers."]]
    L += ["", "## Innocence assessment", f"**{ev['innocence']['status']}**", "",
          f"- {ev['innocence']['volume_text']}", f"- {ev['innocence']['composition_text']}"]
    L += ["", "## Network findings"] + [f"- {n}" for n in ev["network"] or ["No notable links."]]
    w = ev["website"]
    site = (f"P(text matches declared category) = {w['p']:.0%}" if w["has_website"]
            else "none (neutral, no penalty)")
    L += ["", "## Claimed profile", f"- Website: {site}"]
    if w.get("terms"):
        L.append(f"- Words pulling away from '{ev['declared_category']}': {', '.join(w['terms'])}")
    if ev.get("claim"):
        c = ev["claim"]
        L += ["", f"## Merchant explanation: \"{c['reason']}\"", f"**{c['summary']}**"]
        L += [f"- {'PASS' if k['passed'] else 'FAIL'}: {k['check']}" for k in c["checks"]]
    return "\n".join(L) + "\n"


def _latin1(text: str) -> str:
    """Core PDF fonts are Latin-1 only: map the few typographic characters we use."""
    for a, b in {"—": "-", "–": "-", "·": "-", "’": "'", "“": '"', "”": '"', "→": "->", "₹": "INR "}.items():
        text = text.replace(a, b)
    return text.encode("latin-1", "replace").decode("latin-1")


def markdown_to_pdf(md: str) -> bytes:
    """Render the report's simple markdown (#, ##, -, >, **bold**) to PDF bytes."""
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    nl = {"new_x": "LMARGIN", "new_y": "NEXT"}                     # start every block on a new line
    for raw in md.splitlines():
        line = _latin1(raw)
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 17); pdf.multi_cell(0, 9, line[2:], **nl); pdf.ln(2)
        elif line.startswith("## "):
            pdf.ln(2); pdf.set_font("Helvetica", "B", 13); pdf.multi_cell(0, 8, line[3:], **nl)
        elif line.startswith("> "):
            pdf.set_font("Helvetica", "I", 10); pdf.multi_cell(0, 6, line[2:], **nl)
        elif line.startswith("- "):
            pdf.set_font("Helvetica", "", 10.5); pdf.multi_cell(0, 6, "  * " + line[2:], markdown=True, **nl)
        elif line.strip():
            pdf.set_font("Helvetica", "", 10.5); pdf.multi_cell(0, 6, line.rstrip(" "), markdown=True, **nl)
        else:
            pdf.ln(2)
    return bytes(pdf.output())
