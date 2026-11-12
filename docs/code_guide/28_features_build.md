source: merchantdna/features/build.py
sha1: 2debfceecfa7
title: Feature store builder — `make features`
mode: line

Runs every feature family over three kinds of window — the history window, the current window and weekly snapshots — adds the own-history and peer-relative views, and saves everything to `artifacts/`. Also precomputes two tables the dashboard uses so it never scans raw transactions.

### 1-8
Docstring listing the outputs.

### 9-27
Imports: the feature families, the context/window helpers, config and I/O utilities.

### 28-29
Module logger.

### 30-31
Spacing.

### 32-34
`baseline_days`: the history window is the first 37.5% of days (45 of 120).

### 35-36
Spacing.

### 37-43
`window_features` signature and docstring. `roaming` is optional: in normal use it is computed from the window itself; the app's single-merchant re-scoring passes the saved population values so one edited merchant is still compared with everyone else's payers.

### 44-45
Slice the window; compute (or accept) the per-payer city counts.

### 46-47
The window's first timestamp and the settlement rows inside the window.

### 48-57
Run every family and the 19-bin amount histogram (renamed to `a00`–`a18`).

### 58-60
Concatenate side by side, re-index to the full merchant list (merchants with no transactions become rows of NaN), name the index and return.

### 61-62
Spacing.

### 63-68
`fill_missing`: a merchant absent from a window has zero counts, and every other feature is filled with the population median (neutral), never with zero.

### 69-70
Spacing.

### 71-73
`add_relative_views`: the own-history and peer views.

### 74-76
Align the history features and decide who has usable history (at least 7 active days in the baseline).

### 77-79
Volume versus own history = current daily rate / baseline daily rate (baseline floored at 0.5/day). Cold-start merchants get the population median instead of an inflated ratio — an earlier version gave new merchants 64× here, which would have punished them for being new.

### 80-82
Deltas versus own history for the `HISTORY_DELTA` columns (0 for cold starts), plus a `has_history` flag the composition tests use.

### 83-86
Cohort keys, cohort statistics, append the z-scores, return features and the statistics (saved so single-merchant re-scoring can reuse them).

### 87-88
Spacing.

### 89-94
`daily_counts`: count and GMV per merchant per day with dates attached; feeds the expected-volume model and the timeline chart.

### 95-96
Spacing.

### 97-103
`hour_day_cube`: a (merchants × days × 24) array of counts as 16-bit integers for the hour × day heatmap.

### 104-105
Spacing.

### 106-117
`main`: load config and context, the transactions and settlements, the window lengths, and the first-seen index (first timestamp of each merchant–payer pair over all history).

### 118
Blank.

### 119-122
History window (ending on the last baseline day) and current window (ending on the last day), both filled; then the relative views for the current window.

### 123
Blank.

### 124-129
Weekly snapshots: for each as-of day, the same raw features + relative views (always relative to the same history window), tagged with the as-of day and date.

### 130
Blank.

### 131-138
Write the three feature tables and the daily counts; save the cohort statistics, the hour × day cube and the population payer-roaming counts for the current window.

### 139-140
Log the shape and assert that no label-like column slipped into the feature store.

### 141-144
Script entry point.
