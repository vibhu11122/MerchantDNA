source: merchantdna/models/innocence.py
sha1: 2d432031e455
title: Innocence Engine — explain before you flag
mode: line

The arbiter. Part (a) asks whether a merchant's extra *volume* is explained by what its peers did on the same days (a festival lifts every bakery). Part (b) asks whether the *composition* of its business changed (hours, amount mix, payer geography). The rule, stated in the docstring and enforced in `fusion.gate`: the engine may discount volume-driven risk only; it never discounts a composition shift. A festival explains more sales, not different sales.

### 1-12
Docstring: the two parts and the core rule.

### 13-21
Imports, including the hourly and amount-histogram column lists used by the composition tests.

### 22
Blank.

### 23-25
`MODEL_FEATURES`: the inputs of the expected-volume model — category code, five calendar flags, the merchant's own usual level (log) and day of month. `CAL_COLS` are the calendar flags among them.

### 26-28
Spacing and a section marker.

### 29-30
`reference_rates`: each merchant's "usual" daily volume, measured on days before `end_day`.

### 31
The first day each merchant had any transactions (so days before onboarding are not counted as zeros).

### 32-34
Keep days before `end_day`, on or after the merchant's first active day, and outside the Diwali window (so a festival does not inflate "usual").

### 35-37
Mean count and number of reference days per merchant, plus the first day; merchants with no reference days get rate 0 and 0 days.

### 38-39
Spacing.

### 40-42
`peer_uplift`: for each cohort and day, how much peers moved relative to their own usual — the low, median and high quantile across the cohort.

### 43-44
Join each merchant-day with its reference rate; keep merchants with enough history and a non-zero rate.

### 45-47
If nobody has enough history yet (early snapshots), return an empty table with the right columns so callers still work.

### 48-51
Uplift = today's count / usual rate; per (cohort, day) take the 5th, 50th and 95th percentiles (the band is configured as p5–p95), name them, and floor at 0.05 so a quiet day never produces a zero multiplier.

### 52-53
Spacing.

### 54-56
`_design`: assemble model inputs and the baseline for a set of merchant-day rows.

### 57-59
Attach the reference rate, the cohort key, and the peer uplift quantiles for that cohort-day (1.0 when no peer information exists).

### 60-63
Calendar flags as integers and day of month, looked up by day index.

### 64-65
Category code (an integer the tree model can split on) and the log of the usual rate.

### 66-67
The baseline in log space: `log(1 + usual × peer median uplift)`. The model's target `y` is the residual: log(1 + actual) minus the baseline. The model therefore only has to learn what the peer median does not already explain.

### 68
Return.

### 69-70
Spacing.

### 71-73
`fit_volume_model` trains on the days *before* the scoring window.

### 74-79
The last 14 pre-window days are held out for conformal calibration; reference rates are measured before that; keep merchants with at least 14 reference days and drop their pre-onboarding days.

### 80-83
Category codes, peer uplift table on the history, the design matrix, and the split into training rows and calibration rows.

### 84
Blank.

### 85-90
One LightGBM **quantile** regressor per requested quantile (0.05, 0.5, 0.95), deterministic. Each predicts that quantile of the residual given the calendar and the merchant's level.

### 91-93
On the calibration rows, the predicted low and high edges, widened by the peer spread: the low edge drops by log(p50 / p_lo), the high edge rises by log(p_hi / p50). This is where "some bakeries surge 10× at Diwali" enters the band.

### 94-96
Split-conformal score: how far outside the band the truth fell (negative when inside). `qhat` is its (1 − 2 × 0.05) = 90th percentile; adding it to both edges guarantees about 90% coverage on days like the calibration days. Return everything needed to score.

### 97-98
Spacing.

### 99-106
`volume_bands`: the expected count and band for every merchant-day in the scoring window. `peers` may be passed in so a single re-scored merchant is judged against the stored population table.

### 107-113
Window start, reference rates as of the window start, the window's rows, the peer table (computed if not supplied), and the design matrix.

### 114-115
Predicted low and high residual quantiles.

### 116-118
Back to counts: expected = exp(baseline) − 1; lower and upper edges apply the quantile, the peer-spread widening and the conformal margin, then undo the log.

### 119-122
`above` = the actual count exceeded the upper edge; `active` = the merchant existed that day. Return the useful columns and the peer table.

### 123-124
Spacing.

### 125-129
`volume_verdict`: turn the daily bands into one verdict per merchant, using active days only.

### 130-137
Per merchant: the share and number of days above the band, the number of window days, the largest peer median and high uplift seen (for the explanation text), and the reference-day count; aligned to the feature table.

### 138-139
Merchants absent from the bands have exceed rate 0; fewer than 14 reference days means cold start.

### 140-141
`volume_up`: the window's volume is at least 1.5× the merchant's own history (and it is not a cold start).

### 142-143
`volume_explained`: at most 15% of days above the band — or cold start, where there is nothing to judge. Return.

### 144-146
Spacing and section marker.

### 147-155
`js_distance`: the Jensen–Shannon distance between rows of two probability matrices. Normalise both, take the midpoint `m`, compute the two KL divergences against `m` (base 2, ignoring zero cells), average and take the square root. Result in [0, 1]; 0 means identical distributions.

### 156-157
Spacing.

### 158-162
`payer_geo`: a 3-bin "distribution" of payer geography — local, non-local but not roaming, and roaming (payers who pay in many cities). Roaming is capped by the non-local share so the three parts sum to 1.

### 163-164
Spacing.

### 165
The three tested dimensions and the columns that hold each (payers is computed by `payer_geo`).

### 166-167
Spacing.

### 168-169
`_dist`: the distribution matrix for a dimension.

### 170-171
Spacing.

### 172-179
`composition_tests` compares the current window with the merchant's own history and with its cohort now; `ref` carries population statistics so one merchant can be re-scored alone.

### 180-184
Config, cohort keys, who has history, the output frame, and a fresh reference dict.

### 185-193
For each dimension: the current and historical distributions; the cohort's mean profile (computed, or taken from `ref`); the JS distance to own history (0 for cold starts) and to the cohort profile.

### 194-203
Robust z-score of every JS distance within the cohort (median and MAD, computed or taken from `ref`; +0.01 avoids division by zero), clipped to ±10. "Big" is therefore relative to how much merchants of that category normally vary.

### 204-207
A dimension has shifted if either the self-comparison or the peer-comparison has z > 3 **and** an absolute JS distance above 0.05 (so a cohort with near-zero spread cannot fire on noise).

### 208
Return the tests and the reference statistics.

### 209-211
Spacing and section marker.

### 212-214
`verdict`: the plain-English assessment for one merchant; which dimensions shifted.

### 215-227
The volume sentence for the four cases: cold start; volume not up; up and explained (quotes the peers' uplift and the days-above count); up and not explained.

### 228-230
The composition sentence: unchanged, or the list of shifted dimensions with the rule spelled out.

### 231-239
The status: "Cleared" only when volume was up, explained, and nothing shifted; "Not cleared: business mix changed" whenever anything shifted; "Not cleared: unexplained volume"; otherwise "Nothing to explain". Return the pieces.
