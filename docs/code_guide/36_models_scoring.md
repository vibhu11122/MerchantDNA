source: merchantdna/models/scoring.py
sha1: fd8c8a281186
title: Scoring — from a window's features to fusion inputs
mode: line

One function, `components`, turns a feature table into every component score and the gated fusion input table. The same function serves three callers: the whole population as of today, every weekly snapshot, and a single edited merchant in the Model Lab. For the last case it receives the population reference statistics (`refs`) computed in the first.

### 1-6
Docstring.

### 7-19
Imports: the fusion module (as `F`), and the scoring functions of each pillar.

### 20-21
Spacing.

### 22-42
`Bundle`: a dataclass holding every fitted model and reference table the scorer needs — the label-free merchant table, cohort keys, calendar, history features, the website table and model, the verifier, the autoencoder with history codes, category centroids and spreads, the volume model, both graphs, the communities, the fusion model (filled in after training) and `refs` (filled in after the first population scoring). It is saved as `artifacts/bundle.joblib` and loaded by the app.

### 43
Blank.

### 44-46
`declared`: shortcut to the declared category series.

### 47-48
Spacing.

### 49-55
`components` signature and docstring.

### 56-58
`single` is True when reference statistics were supplied (one-merchant mode).

### 59-64
The pillars in turn: verifier scores, DNA drift and codes, composition tests (using stored peer profiles in single mode), daily volume bands (using the stored peer uplift table in single mode), and the volume verdict.

### 65
Blank.

### 66-69
Assemble the fusion inputs in `F.ALL` order: website mismatch, verifier mismatch, the three drift numbers, the six composition z-scores, every `z_` column that fusion uses, and the exceed rate.

### 70-71
Keep an ungated copy (for the ablation), then apply the Innocence gate.

### 72
Label-free stage-1 suspicion (population percentiles; in single mode the stored sorted values).

### 73-76
Network features: in single mode they are looked up from the stored population table (editing one merchant's transactions does not change who it shares a device with); otherwise computed by propagating stage-1 suspicion over the graphs.

### 77-78
Append the network columns to both tables.

### 79-81
Return everything: the gated and ungated inputs, each pillar's outputs, the bands and the reference statistics for later single-merchant scoring.

### 82-83
Spacing.

### 84-86
`risk`: the calibrated probability × 100.
