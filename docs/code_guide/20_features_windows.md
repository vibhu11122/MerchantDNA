source: merchantdna/features/windows.py
sha1: e0661a4d2948
title: Windows — loading transactions and slicing time
mode: line

Every feature family receives the transactions of one time window plus a `FeatureContext` with the reference data it needs. This module builds that context, loads the transactions once with the helper columns every family uses, and slices windows by day index.

### 1-10
Imports. `read_merchants_for_models` is the label-free merchant view — the only merchant loader the feature and model code is allowed to use.

### 11-12
Spacing.

### 13-20
`FeatureContext`: the config, the merchant reference table (id, category, city, tier — **no labels**), the calendar, and two boolean minute grids of shape (days × 1440): `post_wicket[d, m]` is True if minute `m` of day `d` is within ten minutes after a wicket, `match_minutes[d, m]` if a match is on. Precomputing these lets the event features index them directly.

### 21-22
Spacing.

### 23-25
`city_tiers`: map city name → tier (1 metro, 2 smaller) from the config's city list.

### 26-27
Spacing.

### 28-31
`build_context`: take the four public merchant columns needed for features and add the tier.

### 32-38
Load the calendar and prepare empty minute grids; read the post-wicket span (10 minutes) and the match start/end minutes.

### 39-44
Fill the grids: for each match day, mark the match minutes and the ten minutes after each wicket. Return the context.

### 45-46
Spacing.

### 47-49
`load_transactions`: read the full transaction table (about 4.7M rows).

### 50-54
Derived columns, in compact integer types to save memory: the calendar date, `day_idx` (days since the first simulated day), hour, and minute of day.

### 55-57
The merchant's own city, and `is_local` = the payer's city equals the merchant's city. Converting both to plain string arrays before comparing avoids pandas trying to align two different categoricals.

### 58
Return.

### 59-60
Spacing.

### 61-63
`window`: the transactions whose `day_idx` lies in the `length` days ending on `end_day` (inclusive). Every window in the project goes through this one function.

### 64-65
Spacing.

### 66-69
`snapshot_days`: as-of days every `every` days counting **backwards** from the last day, so the final snapshot always equals the scoring day; sorted ascending for the trajectory.
