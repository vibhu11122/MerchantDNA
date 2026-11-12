source: merchantdna/eval/metrics.py
sha1: 92b4d3784388
title: Metric helpers
mode: line

The numbers in `reports/metrics.json`: PR-AUC with a bootstrap interval, flags at a fixed review budget, and precision / recall / false-positive rates for any flag set, including the headline false-positive rate on legitimate festival-surge merchants.

### 1-6
Imports: average precision (= PR-AUC) and the precision–recall curve from sklearn.

### 7-8
Spacing.

### 9-13
`pr_auc_ci`: a seeded generator, arrays, and a list for bootstrap replicates.

### 14-17
300 bootstrap resamples (with replacement); compute average precision on each that contains at least one positive.

### 18-19
The point estimate plus the 5th and 95th percentiles of the replicates — a 90% interval that shows how uncertain 30 positives make the number.

### 20-21
Spacing.

### 22-25
`budget_flags`: True for the top `budget` share (2% → 14 merchants) by score. This is "what analysts can actually review".

### 26-27
Spacing.

### 28-34
`flag_metrics`: true and false positives, then precision, recall, the false-positive rate over all honest merchants, and the false-positive rate restricted to the festival-surge merchants (the headline number from CLAUDE.md §8).

### 35-36
Spacing.

### 37-40
`pr_curve`: the curve points for plotting in the Model Lab.
