source: merchantdna/models/fusion.py
sha1: 8bb5ff6ca610
title: Fusion — one calibrated probability with reasons
mode: line

Thirty component scores go in; one calibrated probability of purpose drift comes out, with its top drivers in plain English. The stacker is deliberately small (depth-2 trees, 60 of them) and **monotone**: every input is constrained so that "more anomalous" can only raise the risk. It is trained on a simulated analyst-labelled subset of 80 merchants, calibrated on out-of-fold scores, and shifted from the sample's fraud rate to the population's.

### 1-8
Docstring.

### 9-19
Imports: LightGBM, SHAP, isotonic regression and logistic regression (the two calibrators), stratified folds.

### 20
Blank.

### 21-31
The input families. `CLAIMED` (website), `BEHAVIOUR` (verifier + DNA), `COMPOSITION` (the six JS z-scores), `PATTERN` (peer z-scores of the betting tells), `PAYER` (peer z-scores of the payer signals), `VOLUME` (peer z-scores of volume plus the exceed rate — the only family the gate may neutralise), `NETWORK`. `ALL` is their union, in this order.

### 32-34
`STAGE1`: the label-free families used to compute the behavioural suspicion that propagates over the graphs — everything except volume and network.

### 35-37
`PAYER_DERIVED`: every input that comes from the payer side, used by the "no payer features" ablation.

### 38-70
`PLAIN`: the plain-English label for each input, used in the drivers chart and the report. No jargon reaches the screen.

### 71-72
Spacing.

### 73-79
`gate` — the Innocence rule as code. For merchants whose volume is explained, set the five volume inputs to 0 (neutral). Every other column is untouched.

### 80-81
Spacing.

### 82-89
`stage1_score`: a label-free suspicion score in 0–1 for propagation. Percentile-rank each STAGE1 input against the population, average the ranks, then take the percentile of that average. `ref` stores the sorted population values so a single merchant can be ranked later.

### 90-93
Build the reference (sorted column values) if not supplied; the rank of each value is its position in the sorted array divided by the population size.

### 94-98
Average the ranks, store the sorted averages in `ref` the first time, convert each merchant's average to its percentile, and return both.

### 99-100
Spacing.

### 101-108
`select_labelled`: simulate which merchants an analyst team has reviewed. Labels are read **only** here and in evaluation. Analysts work by case: when a reviewed fraud is strongly linked to others, the linked merchants are reviewed too.

### 109-113
Config, a seeded generator, the label pool (heroes excluded), the target size (10% = 80) and the number of frauds (25% of that, capped at half of all frauds so evaluation keeps enough positives).

### 114-121
Walk the frauds in a seeded random order (sorted first so the order does not depend on dictionary order), adding each one's whole strong-link case until the fraud quota is reached.

### 122-124
Fill the rest with honest merchants drawn at random; return the sorted id list (sorted so the stacker's row order is identical run to run).

### 125-126
Spacing.

### 127-135
`_model`: the stacker. Depth 2 (`num_leaves = 4`), 60 trees, learning rate 0.05, at least 8 merchants per leaf, L2 = 5, half the columns per tree, 80% row subsampling, a `+1` monotone constraint on every column, and the deterministic flags.

### 136-137
Spacing.

### 138-141
`fit_fusion`: columns default to `ALL`; the ablations pass a subset.

### 142-146
Out-of-fold **raw** scores (log-odds): five stratified folds, each fold scored by a model trained on the others.

### 147-150
The calibrator, fitted on those out-of-fold scores: isotonic if configured (a monotone step function, better with thousands of labels), otherwise Platt scaling (a logistic curve on the log-odds — the right choice for 80 labels, where isotonic collapses into a handful of steps).

### 151-154
Fit the final stacker on all labelled rows and return it with the calibrator, the columns, the sample's fraud rate, the population prior and the out-of-fold data (kept for diagnostics).

### 155-156
Spacing.

### 157-161
`_calibrate`: apply whichever calibrator was fitted.

### 162-163
Spacing.

### 164-170
`predict_fusion`: raw log-odds → calibrated probability (clipped away from 0 and 1) → prior correction. The labelled sample is 26% fraud but the population is about 5%, so the odds are multiplied by (population odds / sample odds) — Bayes' rule — and converted back to a probability. ×100 gives the risk score.

### 171-172
Spacing.

### 173-176
`explain`: SHAP values from the tree explainer (older SHAP versions return a list per class; take the positive class).

### 177-183
For each merchant, the `top` inputs by absolute contribution, each with its plain-English label, its value and its contribution in log-odds (positive raises risk, negative lowers it). Return a dict keyed by merchant id.
