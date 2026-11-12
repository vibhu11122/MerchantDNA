source: merchantdna/models/rescore.py
sha1: d964c1210efb
title: Re-scoring one merchant — the Model Lab "break it" controls
mode: line

The judges' controls ("inject a Diwali spike", "make FreshOven mimic a bakery") edit one merchant's transactions and run it through the **same** pipeline — features, pillars, gate, stacker — against the stored population statistics. Re-scoring an unedited merchant reproduces its batch score exactly, which is the test that this module is honest.

### 1-5
Docstring.

### 6-20
Imports: the action ladder, feature building blocks, the fusion module, the verdict text and the scorer.

### 21-22
Spacing.

### 23-34
`enrich`: add the same helper columns that `features.windows.load_transactions` adds (date, day index, hour, minute, merchant city, is-local), for a single merchant's rows.

### 35-36
Spacing.

### 37-40
`merchant_features`: the current-window features for one merchant, made relative with **population** statistics.

### 41-43
Config, number of days, window length.

### 44-46
First-seen index from this merchant's own transactions; the roaming count of each payer from the stored population table (payers never seen before count as one city).

### 47-48
Run the full feature pipeline on the one merchant and fill any gaps with the population medians.

### 49-55
Own-history view, mirroring `build.add_relative_views` for one row: history availability, volume ratio (population median for cold starts), deltas, and the history flag.

### 56
Append the peer z-scores using the saved cohort statistics, and return.

### 57-58
Spacing.

### 59-62
`rescore`: the whole pipeline for one merchant.

### 63-64
Enrich and build features.

### 65-67
Replace the merchant's daily counts in the population daily table with the edited counts, so the volume band sees the injected spike.

### 68
Score with the stored references.

### 69-70
Risk score and the innocence verdict.

### 71-74
Return score, tier, action rung, SHAP drivers, the verdict, and the feature and input rows for display.

### 75-77
Spacing and section marker.

### 78-87
`festival_shape`: per-day multipliers that lift each Diwali day to `peak_factor` × the merchant's *usual* day (median of non-Diwali days), with 40% of the extra on the non-peak window days — the same shape the simulator uses. Days that are already above target get a multiplier of 1.

### 88-89
Spacing.

### 90-92
`week_shape`: the same factor on seven ordinary days — a spike no festival explains.

### 93-94
Spacing.

### 95-98
`inject_spike`: more of the same. For each day, extra transactions are resampled from that day's own rows, so amounts, hours and payer cities keep the same mix.

### 99-110
Per day: how many extra rows, sample them with replacement, jitter their timestamps by up to ±10 minutes (clipped to the day), give them fresh payer ids (new customers), and append. Return the enlarged table.

### 111-112
Spacing.

### 113-115
`make_mimic`: the adversarial edit.

### 116-121
From `from_day` on, re-draw every transaction's hour from the bakery's hourly profile, keeping its date.

### 122-126
Jitter amounts that sit exactly on 499 / 999 / 1999 by up to ±`jitter` and return.
