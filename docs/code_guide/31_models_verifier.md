source: merchantdna/models/verifier.py
sha1: c78ccd94f870
title: Behavioural category verifier
mode: line

Trains a classifier to predict the *declared category* from behaviour alone (the SHAPE features: hours, amounts, payers, events, settlement — never volume). The declared category of other merchants is the training label, so no fraud labels are needed. For each merchant, P(declared | behaviour) answers "does it behave like what it claims?". Known limitation: it answers "which of the six?" rather than "any of them?", which is why the DNA drift score exists alongside it.

### 1-6
Docstring.

### 7-16
Imports: LightGBM, stratified folds, and the SHAPE column list.

### 17-18
Spacing.

### 19-24
`make_model`: a small multiclass LightGBM. `deterministic=True`, `force_row_wise=True` and `n_jobs=1` make training bit-for-bit reproducible (multithreaded LightGBM on small data is not); the remaining hyper-parameters come from the config.

### 25-26
Spacing.

### 27-28
`fit_verifier` trains on the history-window features so the labels describe how merchants behaved *before* any drift.

### 29-32
Declared category per merchant, the sorted class list, five stratified folds, and holders for the fold models and the fold map.

### 33-36
For each fold: fit on the training part's SHAPE features, keep the model, and remember which fold each held-out merchant belongs to.

### 37
Return the five models, the merchant → fold map and the class list. There is no single "final" model: every merchant is always scored by the model that excluded it (cross-fitting).

### 38-39
Spacing.

### 40-45
`score_verifier` scores any feature table indexed by merchant id — the current window, or the weekly snapshots where ids repeat.

### 46-48
An empty output frame, a probability matrix, and each row's fold.

### 49-52
For each fold model, predict probabilities for the rows that belong to that fold.

### 53-56
Look up the column of each row's declared category; `verifier_p_declared` is that probability and `verifier_mismatch` its complement.

### 57-59
Also report the most likely category and its probability ("behaves like grocery, 71%") for the dashboard. Return.
