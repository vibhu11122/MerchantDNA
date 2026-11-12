source: merchantdna/eval/ablation.py
sha1: adaa4b10b3f9
title: Ablations — remove one pillar at a time
mode: line

Retrains the fusion stacker on the same labelled merchants with one pillar removed, so the drop in PR-AUC (or the change in a hero's score) shows what that pillar contributes. These are the honest numbers quoted in the Model Lab.

### 1-8
Imports.

### 9-10
Spacing.

### 11-13
`ablation_scores` takes the gated and ungated input tables, the labels, the labelled ids and the config.

### 14-19
Four variants: the full system; no Innocence Engine (the ungated table, so volume inputs are never neutralised); no network (drop the five network columns); no payer features (drop every payer-derived column).

### 20-24
Fit and score each variant with the same `fit_fusion` / `predict_fusion` as production, returning 0–100 scores per variant.
