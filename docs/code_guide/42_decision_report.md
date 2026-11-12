source: merchantdna/decision/report.py
sha1: ee4967fdbd59
title: Evidence sentences and the investigation report
mode: line

Turns numbers into sentences an analyst can read, assembles the investigation report in Markdown, and renders that Markdown to PDF for export.

### 1-6
Imports.

### 7-19
`EVIDENCE_RULES`: for nine signals, a template sentence with the merchant's value `{v}` and the cohort median `{m}`. A sentence is shown only when the merchant's peer z-score for that signal is high.

### 20-21
Spacing.

### 22-28
`evidence_lines`: for each rule, if the merchant's `z_<signal>` is at least `z_min` (3.0), format the sentence. Returns a list of plain-English facts such as "75% of payments are exactly INR 499 / 999 / 1999 (peers: 0.6%)".

### 29-30
Spacing.

### 31-40
`investigation_markdown`: the header — title, score and tier, recommended action, declared category and city, what the merchant behaves like, the "signals, not proof" line, and the drivers heading.

### 41-43
One bullet per SHAP driver with its direction and contribution.

### 44-47
Evidence, innocence assessment (status plus the two sentences) and network findings sections, each with a fallback line when empty.

### 48-53
Claimed profile: the website probability or "none (neutral, no penalty)", and the words pulling away from the declared category when there are any.

### 54-58
If the merchant gave an explanation, its verdict and each check as PASS / FAIL. Join the lines and return.

### 59-60
Spacing.

### 61-65
`_latin1`: the built-in PDF fonts only cover Latin-1, so replace the few typographic characters the report uses (dashes, middle dot, curly quotes, arrows, the rupee sign) before rendering.

### 66-67
Spacing.

### 68-74
`markdown_to_pdf`: a minimal renderer for the report's own Markdown subset. `nl` makes every block start at the left margin on the next line.

### 75-88
Line by line: `# ` → large bold title; `## ` → section heading; `> ` → italic note; `- ` → bullet (with `**bold**` support via fpdf's markdown mode); other text → paragraph; blank → small gap.

### 89
Return the PDF bytes for Streamlit's download button.
