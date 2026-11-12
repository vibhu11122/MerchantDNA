source: merchantdna/models/train.py
sha1: 7c179f9e2105
title: Training orchestrator — `make train`
mode: line

Fits every model in order, scores the population, fits the fusion stacker on the simulated analyst subset, builds the evidence for every merchant, scores the weekly snapshots, projects the DNA codes with UMAP, and writes all artefacts. Labels are read in exactly one place (line 148) and deleted seven lines later.

### 1-5
Docstring with the order of operations.

### 6-30
Imports from every part of the project.

### 31-33
Logger and the hero ids (used only to *exclude* them from the labelled set and to log their results).

### 34-35
Spacing.

### 36-48
`load_inputs`: the label-free merchant table with city tier, the calendar, the three feature tables, the last 30 days of transactions (merchant, payer, timestamp only — for the payer-overlap graph) and the daily counts.

### 49-50
Spacing.

### 51-54
`fit_bundle`: cohort keys first.

### 55-58
Website classifier and behavioural verifier, each timed.

### 59-62
Autoencoder trained on history features **and** snapshot features (so it has seen festival-period shapes), the history codes, and the category centroids and spreads.

### 63-66
Expected-volume model, trained on days before the scoring window.

### 67-70
Identity graph, payer-overlap graph over the recent window, Louvain communities.

### 71-72
Assemble the bundle (fusion and refs are filled in later).

### 73-74
Spacing.

### 75-78
`network_findings`: the plain-English link list for a merchant's report.

### 79-83
The six strongest identity links; mention those involving a device or bank, or with total strength above 2, with the neighbour's name, risk score and link strength.

### 84-86
Up to three payer-overlap links with their Jaccard share. Return.

### 87-88
Spacing.

### 89-94
`build_evidence`: per-merchant evidence dicts; cohort medians for the evidence sentences.

### 95-103
For each merchant: its public row, features, volume verdict and composition results; the innocence verdict; the evidence dict for the Explain step (volume facts, features, shifted dimensions and the growth of the average ticket); the website probability.

### 104-121
The evidence record: identity, score, tier, rung, what it behaves like, SHAP drivers, peer-relative evidence sentences, the innocence verdict, network findings, the website verdict with the words pulling away from the declared category, and the pre-computed result of every possible merchant explanation.

### 122
Return.

### 123-124
Spacing.

### 125-134
`score_snapshots`: for each weekly as-of day, run `components` on that snapshot's features and keep the risk score (plus night share, for the lead-time diagnostics) and the DNA codes.

### 135-136
Spacing.

### 137-146
`main`: load, fit, and score the current window; store the population references on the bundle.

### 147
Blank.

### 148-149
**The only place labels are read.** Choose the analyst-labelled subset: 10% of merchants, enriched in fraud, by strong-link case, heroes excluded.

### 150-155
Fit fusion on the labelled rows, score everyone, choose actions, compute SHAP drivers — then delete the labels so nothing below can touch them.

### 156
Blank.

### 157-168
Evidence, and the `scores` table: identity, score, tier, probability, action columns, all fusion inputs, verifier outputs, volume verdict fields, innocence status, stage-1 suspicion, community, website flag and whether the merchant was in the labelled set (evaluation excludes those).

### 169
Blank.

### 170-179
Weekly snapshot scores and codes; UMAP fitted once on history codes plus all snapshot codes; the trajectory table (one "History" frame with no score, then one frame per snapshot) with 2-D coordinates and category.

### 180
Blank.

### 181-189
Write the artefacts: scores, gated and ungated fusion inputs, daily bands, snapshot scores, trajectory, evidence JSON, the labelled id list, and the bundle.

### 190-194
Log the three heroes and the tier counts.

### 195-198
Entry point.
