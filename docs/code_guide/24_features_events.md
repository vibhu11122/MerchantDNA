source: merchantdna/features/events.py
sha1: 64f7d736a35f
title: Event alignment — matches and wickets as a feature, never a rule
mode: line

Betting collectors are busier on match evenings and spike in the minutes after a wicket. We measure that alignment as three numbers per merchant and hand them to the models like any other feature. There is deliberately no "if busy after wickets then flag" rule anywhere: a sports bar is also busy on match nights, and only the combination with other signals should count.

### 1-7
Imports.

### 8-9
Spacing.

### 10-11
`event_features` for one window.

### 12-15
Evening hours (19–23); per transaction, whether its day is a match day and whether it is in the evening; `days` (min/max day per merchant) is computed but not used further — a harmless leftover.

### 16
Blank.

### 17-18
A small frame with, per transaction, whether it is a match-evening transaction or an other-evening transaction.

### 19-21
The days present in the window, how many are match days and how many are not (at least 1 each to avoid division by zero).

### 22-24
`ipl_evening_lift`: evening transactions per match day divided by evening transactions per non-match day, with +0.5 pseudo-counts so tiny merchants do not produce extreme ratios. 1.0 = no match effect.

### 25
Blank.

### 26-28
Daily counts per merchant as a (merchant × day) grid aligned to the window days, and the 0/1 match-day flag per day.

### 29-33
Pearson correlation between each merchant's daily counts and the match-day flag, written out in NumPy: centre both, divide the dot product by the product of norms. One vectorised `@` gives all 800 correlations at once.

### 34
Blank.

### 35-36
For each transaction, look up whether its minute is inside a match and whether it is in a post-wicket window, using the precomputed minute grids from the context.

### 37
The expected post-wicket share of in-match minutes (about 12 wickets × 10 minutes / 210 match minutes ≈ 0.57) — what a merchant with no wicket reaction would show.

### 38-39
Per merchant: number of in-match transactions and how many of those fell in post-wicket windows.

### 40-42
Shrunk lift: add `prior` (20) pseudo-transactions at the expected rate, then divide the observed post-wicket share by the expected share. A merchant with three in-match transactions therefore sits near 1.0 instead of swinging between 0 and 1.75.

### 43
Return.
