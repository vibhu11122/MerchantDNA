source: merchantdna/sim/profiles.py
sha1: 0c8e42b6963e
title: Profiles — sampling hours, amounts and payer ids
mode: line

Small, pure sampling functions shared by the transaction generator. They encode the two behaviours the whole project is about: how an honest shop's amounts and hours look, and how betting top-ups look.

### 1-4
Docstring, future-annotations import, NumPy.

### 5
Blank.

### 6-10
Payer id layout. Raw payer ids are integers built so that the *city* of a payer can be recovered from the id. Local payers of city `c` are `c * 1_000_000 + k`. Three further pools live above those: honest travellers (from 40 million), nationwide bettors (from 50 million) and the shared payer pool of each mule ring (from 60 million, 10,000 ids per ring). These raw ids are hashed before they leave the simulator (see `hash_ids`).

### 11-12
Spacing.

### 13-16
`normalise`: turn any list of non-negative weights (such as the 24 hourly weights in the config) into probabilities that sum to 1.

### 17-18
Spacing.

### 19-22
`sample_seconds_of_day`: draw an hour for each of `n` transactions from the 24-bin profile, then a uniform offset inside that hour. Returns seconds after midnight.

### 23-24
Spacing.

### 25-28
`sample_legit_amounts` signature. `median` and `sigma` describe a lognormal; `price_points` is an optional dict of fixed prices with their shares (gyms and tuition centres use these); `tags` and `tag_share` let a share of honest amounts snap to common price tags such as 499 or 999, so that fixed prices are not a free giveaway of fraud.

### 29
Lognormal draw: `median × exp(sigma × N(0,1))`, rounded to whole rupees.

### 30-33
Optional price-tag snapping. Choose which transactions snap, then replace each with the nearest tag. `amounts[snap, None] - t[None, :]` builds a (n_snap × n_tags) difference matrix; `argmin(axis=1)` finds the nearest tag per transaction.

### 34-38
Optional fixed price points: with total probability equal to the sum of the shares, replace the amount with one of the fixed prices, drawn in proportion to their shares.

### 39
Never return an amount below ₹10.

### 40-41
Spacing.

### 42-48
`sample_betting_amounts`: betting top-ups cluster on the configured price points (499 / 999 / 1999 with shares); the rest are "cover" amounts that look like the merchant's declared business. `jitter` lets the adaptive mimic blur the price points (for example 999 becomes anything from 849 to 1149).

### 49
Start every amount as a normal cover purchase.

### 50-53
Decide which transactions land on a price point (probability = sum of shares) and pick the point for each.

### 54-55
If jitter is requested, multiply each picked price by a random factor in [1 − jitter, 1 + jitter] and round.

### 56-57
Overwrite the chosen positions and return.

### 58-59
Spacing.

### 60-66
`hash_ids`: the splitmix64 finaliser. Add a large odd constant, then three rounds of xor-shift-multiply. It is deterministic (so the same payer hashes the same everywhere, which the payer-overlap graph needs) and not reversible in practice. The result is viewed as signed 64-bit integers so pandas/Parquet handle it natively.
