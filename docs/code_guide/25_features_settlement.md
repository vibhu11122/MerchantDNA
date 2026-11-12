source: merchantdna/features/settlement.py
sha1: 5c8f795359c0
title: Settlement and payment-mix features
mode: line

How fast money leaves and how it arrives. Betting fronts cash out within hours; most honest shops settle on T+1 or T+2 — but 10% of honest merchants in the simulation also use instant settlement, so this is evidence, not proof.

### 1-6
Imports.

### 7-8
Spacing.

### 9-10
`settlement_features` takes the window's transactions `w` and the window's settlement rows `s`.

### 11-15
Per merchant from the settlement table: mean payout delay in hours and the share of payouts settled within 12 hours.

### 16-18
From the transactions: refund rate and card share (the rest is UPI). Betting flows are almost entirely UPI with near-zero refunds.

### 19
Return.
