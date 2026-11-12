source: merchantdna/eval/run.py
sha1: 640bc9f037dd
title: Evaluation runner — `make eval`
mode: line

Measures MerchantDNA against the baselines on the 720 merchants outside the labelled set, runs the ablations, the adaptive-mimic stress test and the slow-drift lead-time comparison, and writes `reports/metrics.json` plus three PNGs. The dashboard reads these files and never recomputes them.

### 1-5
Docstring.

### 6-22
Imports; matplotlib's file backend is selected before pyplot is imported.

### 23-25
Logger and hero ids (reported in the metrics file for the record).

### 26-27
Spacing.

### 28-35
`method_block`: for one method's scores — PR-AUC with interval, metrics at the 2% review budget, at a 5% budget, and at the method's own ("native") threshold.

### 36-37
Spacing.

### 38-43
`lead_times`: for each slow-drift merchant, when did each method first flag it across the weekly snapshots?

### 44-52
Per merchant: its snapshot scores and features; the first snapshot day where MerchantDNA reaches MEDIUM, where the rules fire, and where the Isolation Forest flags; `None` if never.

### 53
Collect into a frame.

### 54-59
`lead` for a baseline column: among merchants MerchantDNA detected, a baseline that never fired is treated as firing one week after the last snapshot; the median difference in days is the lead.

### 60-64
Return the per-merchant table and the summary numbers.

### 65-66
Spacing.

### 67-74
`plots`: precision–recall curves for the three methods.

### 75-84
Ablation bars: PR-AUC and the festival-surge false-positive rate per variant.

### 85-90
Box plot of the risk score by archetype (ground truth, evaluation only).

### 91-92
Spacing.

### 93-102
`main`: load ground truth, the scores joined with truth, the current features, the labelled ids; `ev` = everyone **not** in the labelled set; the labels and the surge mask on that set; the MEDIUM threshold.

### 103
Blank.

### 104-109
Baseline scores and flags. Line 109 builds a fourth method — static rules with the Innocence gate applied (volume ratio set to 1 where volume is explained) — to isolate what the engine alone does for a rules team.

### 110-117
Metric blocks for the four methods and the PR curves for three of them.

### 118
Blank.

### 119-123
Ablations: fit each variant and compute its metric block plus the three hero scores.

### 124
Blank.

### 125-131
Adaptive-mimic stress test on the evaluation set: recall at MEDIUM, within the 2% budget, and under each baseline's native flag.

### 132
Blank.

### 133-136
Lead times for the slow-drift merchants (held-out ones plus the hero, which is never in the labelled set).

### 137
Blank.

### 138-140
Per-archetype flag rate and median score (where the false positives are).

### 141-153
Assemble the metrics dict (dataset sizes, methods, ablations, stress test, lead time, per-archetype, heroes, curves), write the JSON and the plots.

### 154-164
Log the headline numbers.

### 165-168
Entry point.
