source: merchantdna/features/amount.py
sha1: 3a06e75af229
title: Amount features — ticket size and price-point clustering
mode: line

Betting top-ups cluster on fixed amounts (₹499, ₹999, ₹1,999); a bakery's basket amounts are spread out. These features capture both the shape of the amount distribution and the clustering, while also recording a 19-bin histogram used later by the composition tests and the dashboard.

### 1-7
Imports.

### 8-9
Spacing.

### 10-13
`_entropy`: Shannon entropy in bits of a probability vector, ignoring zero entries (log of 0 is undefined). High entropy = amounts spread over many bins.

### 14-15
Spacing.

### 16-21
`amount_histogram`: assign each amount to one of the configured bins (`np.digitize` returns 1-based bin numbers, hence `−1`, clipped to the valid range), cross-tabulate per merchant, make sure every bin column exists, and convert to shares.

### 22-23
Spacing.

### 24-27
`amount_features`: the configured price points and the raw amounts as an array.

### 28-34
One row per transaction with: log(1 + amount) (so means and quantiles are robust to huge tickets), whether the amount is exactly a price point, whether it is within 10% of one (catches the mimic's jitter), and whether it is "round" (multiple of 50, or ends in 99 — common price-tag patterns).

### 35-43
Per merchant: mean and median ticket (computed in log space then transformed back with `expm1`), the log inter-quartile range (spread), and the three shares.

### 44-46
`top_price_share`: the share of transactions at the single most common exact amount. Gyms have a high value legitimately (fixed fees), which makes them the hard negative they were designed to be.

### 47-49
Entropy of the amount histogram per merchant, then return.
