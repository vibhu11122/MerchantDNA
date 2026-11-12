source: merchantdna/eval/baselines.py
sha1: b3e0b19a22d2
title: Baselines — static rules and Isolation Forest
mode: line

Two things a risk team might use today. Static rules fire on a volume jump or a high night share — the "detect betting" approach. An Isolation Forest is a generic unsupervised anomaly detector over the same features MerchantDNA sees. Both give a score for ranking and a native yes/no flag.

### 1-10
Imports; the feature groups the Isolation Forest uses.

### 11-12
Spacing.

### 13-19
`rules_score`: the score is the larger of (volume ratio / 3) and (night share / 0.20), so it reaches 1.0 exactly when either rule fires. Returns the continuous score (for PR curves) and the boolean flag.

### 20-21
Spacing.

### 22-25
`fit_iforest`: 300 trees on the SHAPE + VOLUME features, with the configured contamination (5%) setting its native threshold.

### 26-27
Spacing.

### 28-32
`iforest_score`: sklearn's `score_samples` is higher for *normal* points, so negate it; `predict == -1` is the native outlier flag.
