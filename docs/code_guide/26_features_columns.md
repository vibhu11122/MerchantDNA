source: merchantdna/features/columns.py
sha1: e45ac3a27bb1
title: Feature groups — every model names its inputs
mode: line

A single place that defines which columns belong to which family. Models import these lists instead of guessing column names, so you can read exactly what each model sees — and the test suite can assert that no label-like column is ever in any group.

### 1-2
Docstring and future import.

### 3
Blank.

### 4-5
The 24 hourly-share columns and the 19 amount-histogram columns.

### 6
Blank.

### 7-15
The named families: time-of-day, amount, payer-side, event alignment, settlement, and volume. `vol_ratio_hist` (volume vs own history) is produced later by `build.add_relative_views` but belongs to the volume family.

### 16
Blank.

### 17-18
`SHAPE`: everything that describes *how* a merchant does business, excluding volume. This is what the category verifier and the DNA autoencoder consume. Keeping volume out means a bigger bakery is not a different bakery.

### 19
Blank.

### 20-22
`PEER_Z`: the columns that get a robust z-score against the cohort (all shape families plus four volume measures).

### 23
Blank.

### 24-26
`HISTORY_DELTA`: the columns whose change versus the merchant's own history is kept as an explicit feature.

### 27-28
`LABEL_LIKE`: the two ground-truth columns that must never reach a model. `tests/test_leakage.py` checks every group and every saved feature table against this set.
