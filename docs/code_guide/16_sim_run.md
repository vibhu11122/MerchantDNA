source: merchantdna/sim/run.py
sha1: 63c2e5444832
title: Simulator runner — `make data`
mode: line

Wires the simulator together: one seeded random generator, calendar → merchants → pools → transactions → settlements, then the public transaction table with hashed payer ids. Also writes three sanity plots.

### 1-5
Docstring and imports.

### 6-8
Import matplotlib and select the "Agg" backend (draws to files, no display) **before** importing pyplot; this is why the pyplot import comes after and carries a `noqa: E402` (imports not at top).

### 9-11
pyplot, NumPy, pandas.

### 12
Blank.

### 13-20
Project imports: the calendar, merchant and transaction builders, the hashing helper, config/paths, the Parquet writer and the logger.

### 21-22
A module logger named "sim".

### 23-24
Spacing.

### 25-26
`simulate` builds all four tables in memory and returns them; the tests use this directly without touching disk.

### 27-30
Load config, pick the `full` or `small` scale, and create **the** random generator from the seed (42). Every random draw in the simulator comes from this one generator, which is what makes the data deterministic.

### 31
Blank.

### 32-35
Calendar, merchants + hidden plans, the number of rings (highest ring id + 1), and the shared payer pools.

### 36
Blank.

### 37-39
Generate every merchant's transactions, concatenate, sort by time (stable sort keeps determinism), and derive settlements.

### 40
Blank.

### 41-51
The public transaction table: a sequential `txn_id`, `merchant_id` as a categorical (compact in Parquet), the **hashed** payer id (raw ids are dropped here), timestamp, amount, channel ("card"/"UPI"), the payer's city name via `payer_city_index`, and the refund flag. `is_bet` and `payer_raw` do not survive.

### 52-53
Make `match_start` a proper datetime column and return the four tables.

### 54-55
Spacing.

### 56-61
`sanity_plots`: write quick checks to `reports/sim/`. Join archetype onto transactions and add the hour.

### 62
Blank.

### 63-65
Hourly share of transactions per archetype as one line chart.

### 66
Blank.

### 67-73
Six amount histograms (under ₹3,000) for key archetypes — this is where the 499/999/1999 spikes and the mimic's jittered bands are visible.

### 74
Blank.

### 75-84
SweetCrust vs FreshOven: daily transaction counts and hourly share side by side.

### 85-86
Spacing.

### 87-91
`main`: parse `--small`.

### 92-93
Run the simulation inside a timer.

### 94-96
Write each table to `data/<name>.parquet` and log its row count.

### 97-98
Log the archetype mix and draw the plots.

### 99-102
Standard script entry point.
