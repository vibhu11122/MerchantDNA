source: merchantdna/features/payer.py
sha1: 1845928d5e95
title: Payer-side features — the hard-to-fake signals
mode: line

A fraudster chooses the hours and the amounts; they do not choose who their customers are. These features describe the payer base: how often the same people pay, how concentrated they are, where they live, and whether they also pay merchants in many other cities. The ablation shows this is the strongest pillar (PR-AUC falls from 0.97 to 0.86 without it).

### 1-7
Imports.

### 8-9
Spacing.

### 10-12
`payer_city_counts`: for each hashed payer in the window, the number of *distinct merchant cities* they paid in. A bettor who pays fronts in Pune, Patna and Kochi scores 3; a local shopper scores 1. Computed over the whole population so it is a property of the payer, not of the merchant.

### 13-14
Spacing.

### 15-21
`payer_features` signature. `first_seen` is the first timestamp each (merchant, payer) pair was ever seen — computed over all history, so "new" means never seen before the window. `roaming` is the series from `payer_city_counts`.

### 22-23
Count transactions per (merchant, payer); a payer is a repeat payer if they paid at least twice in the window.

### 24-25
Look up each pair's first-seen time and mark it new if that is on or after the window start.

### 26
A payer "roams" if they paid in 3 or more merchant cities.

### 27-28
Group per merchant; total transactions per merchant (at least 1 to avoid division by zero).

### 29-36
Per merchant: unique payers, payers per transaction (1 = nobody repeats), the share of transactions made by repeat payers, the new-payer rate, the Herfindahl index of payer shares (Σ share²; high when a few payers dominate), and the share of payers who roam.

### 37
Non-local share: 1 − mean of `is_local`.

### 38-42
Payer-city entropy: shares of each payer city per merchant, then −Σ p log₂ p with zeros ignored. A local bakery has entropy near 0; a nationwide bettor base has entropy near log₂(20).

### 43
Return.
