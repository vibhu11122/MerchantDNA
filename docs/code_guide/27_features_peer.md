source: merchantdna/features/peer.py
sha1: 090d9c9e420c
title: Peer-relative view — robust z-scores within a cohort
mode: line

A gym with fixed prices is normal *for a gym*; a restaurant open at midnight is normal *for restaurants in a metro*. Every feature is therefore compared with the merchant's cohort: same declared category and same city tier, in the same window. Medians and MADs are used instead of means and standard deviations so that the fraud merchants inside a cohort do not drag the "normal" level towards themselves.

### 1-5
Imports.

### 6-7
The 1.4826 constant: for normally distributed data, median absolute deviation × 1.4826 equals one standard deviation, so the z-scores are on the familiar scale.

### 8-9
Spacing.

### 10-12
`cohort_key`: a string such as `bakery|1` per merchant.

### 13-14
Spacing.

### 15-17
`cohort_stats`: attach the cohort key to the chosen feature columns.

### 18-19
Median and scaled MAD per cohort and column.

### 20-22
Floor the MAD at 10% of the feature's global standard deviation: a feature that is identical for almost every merchant in a cohort (night share = 0 for all bakeries) would otherwise have MAD = 0 and turn any tiny deviation into a z of ±10. Return both tables stacked under "median" and "mad".

### 23-24
Spacing.

### 25-27
`peer_z`: look up each merchant's cohort key.

### 28-30
Pull the cohort's median and MAD rows for every merchant, compute (x − median) / MAD, and clip to ±10 so the tree models and the stacker never see absurd values.

### 31
Return as `z_<column>` columns.
