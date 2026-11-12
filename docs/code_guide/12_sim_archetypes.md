source: merchantdna/sim/archetypes.py
sha1: de9a1f21b33e
title: Archetypes — each merchant's daily plan
mode: line

Every merchant's story over time is reduced to two arrays, one entry per day: how much of its normal business it does (`legit_mult`) and how much betting-style flow it collects (`bet_mult`). The transaction generator multiplies these by the base daily rate, calendar effects and match effects. Keeping the "plot" separate from the "rendering" makes the archetypes easy to read and to extend.

### 1-7
Docstring describing the two arrays and the formula the generator applies to them.

### 8-12
Imports.

### 13
Blank.

### 14-16
`_active`: 1.0 on days on or after the merchant's onboarding day, 0.0 before. Established merchants have `onboard_day = -1`, so they are active every day; a `new_merchant` has a positive onboard day.

### 17-18
Spacing.

### 19-21
`_ramp`: a straight line from 0 at `start` to 1 after `length` days, clipped to [0, 1]. This is the slow-drift shape. `max(length, 1)` avoids division by zero.

### 22-23
Spacing.

### 24-25
`daily_plan` takes the hidden parameter dict `p` for one merchant and returns the two arrays.

### 26-30
Set up: the archetype name, the active mask, legit = 1 everywhere, bet = 0 everywhere, and `w` = the share of the merchant's flow that is betting, also 0 by default. (The comment on line 30 is repeated on line 32; it is harmless.)

### 31
Blank.

### 32
`bw` is the merchant's betting intensity (drawn between 0.3 and 0.8 at merchant creation, 0.8 for FreshOven), so frauds vary in how blatant they are.

### 33-34
A growing merchant's legit multiplier rises linearly from 1 to `growth_total` (1.5–2.5×) across the period. Nothing else changes, so the Innocence Engine should treat it as explained growth.

### 35-36
A betting collector and an adaptive mimic have a constant betting share `bw` from day one. The mimic differs later, in *how* its bets look (hours, jitter), not in how many.

### 37-38
Slow drift: the betting share ramps from 0 to `bw` starting on `drift_start` over `drift_ramp` days (4–6 weeks; FreshOven starts at mid-period and ramps over 35 days).

### 39-43
Sleeper: before `wake_day` the merchant does a trickle of legit business (`dormant_mult` = 10% of normal) and no betting. From `wake_day` it does `1 − bw` legit and a burst of betting (`bw × burst_mult`, 3–5×). This branch returns early because its legit/bet split is not of the `(1 − w, w)` form used below.

### 44-45
A mule ring member (other than the ring's clean "front" store) carries the ring's fixed betting intensity (0.5). The front store keeps `w = 0`: its own transactions stay clean, which is exactly what makes QuickKart hard.

### 46
Blank.

### 47-49
Convert the betting share into the two multipliers: the legit part shrinks by `(1 − w)` and the betting part is `w × bet_scale` (bet_scale 1–2×, so a betting front can be bigger than the cover business). Multiply both by the active mask and return.
