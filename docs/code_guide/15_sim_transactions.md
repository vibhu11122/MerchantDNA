source: merchantdna/sim/transactions.py
sha1: 9d9745acdfce
title: Transactions — rendering a merchant's plan into payments
mode: line

The heart of the simulator. For one merchant it draws how many payments happen each day (Poisson around a rate built from the base volume, the daily plan, calendar effects and match effects), then for each payment a time of day, an amount, a payer and a channel. Honest and betting-style payments are generated separately and concatenated. Everything is vectorised in NumPy, which is why 4.7M transactions take about five seconds.

### 1-11
Imports. `profiles` (as `pr`) supplies the sampling helpers; `daily_plan` the per-day multipliers.

### 12-13
Spacing.

### 14-19
`PayerPools`: a dataclass holding the home city of every payer in the three shared pools (bettors, ring payers, travellers). Needed to recover `payer_city` from a raw id.

### 20-21
Spacing.

### 22-31
`make_pools` draws a uniformly random home city for every bettor (four communities × 3,000), every ring payer (10,000 slots per ring) and every traveller (30,000). "Uniform over cities" is what makes bettors look nationwide.

### 32-33
Spacing.

### 34-43
`payer_city_index`: for local ids the city is simply `id // 1_000_000`; for the three pools, look the city up by offset. Returns a city index per transaction.

### 44-45
Spacing.

### 46-55
`_calendar_mult`: honest demand per day. Weekend multiplier from the category; for gyms/tuition, a month-start fee cycle (2.5× in the first five days, 0.75× otherwise); the minor-festival multiplier; then Diwali — the full multiplier on peak days and 40% of the uplift in the rest of the window.

### 56-57
Spacing.

### 58-60
`_legit_payers` draws the payer id for each honest transaction.

### 61-64
Config shortcuts: the per-city payer pool size (200,000), number of cities, the category's repeat probability and the merchant's non-local share.

### 65-66
One uniform random number per transaction, and a default id = a random local walk-in.

### 67-68
With probability `repeat_p`, replace with one of the merchant's regular customers (the `regulars` array drawn once per merchant).

### 69-71
With probability `visitor_p`, a visitor from a random city.

### 72-74
With probability `traveller_share` (3%, 25% for nationwide sellers), a traveller from the shared traveller pool — honest payers who appear at merchants in many cities, so "pays in many cities" is not a fraud-only signal. Return the ids.

### 75-76
Spacing.

### 77-80
`_ring_payers`: random ids from the ring's own pool of 600 shared payers.

### 81-82
Spacing.

### 83-92
`_betting_times`: draw seconds of day from the betting hourly profile, then, on match days, move a share (`wicket_share`, 35%) of transactions to within ten minutes after a random wicket of that day. This is the "burst after wickets" behaviour. The loop runs only over the affected transactions.

### 93-94
Spacing.

### 95-97
`generate_merchant`: all transactions for one merchant.

### 98-104
Setup: config blocks, the category profile, the daily plan, a gamma noise factor per day (shape 20 → about ±22% day-to-day), the mimic flag and the match-day mask.

### 105
Blank.

### 106-109
Daily rates. Honest rate = base × plan × calendar effects × noise × (sports-bar match lift, 1.0 for everyone else). Betting rate = base × plan × match lift (2.5×, 1.0 for the mimic) × noise. Draw the actual daily counts from a Poisson distribution of each rate.

### 110
Blank.

### 111-112
Honest transactions: `np.repeat` expands the per-day counts into one day index per transaction.

### 113-114
Hourly profile (the category's, or the night-owl blend) and a time of day for each.

### 115-117
Amounts from the category lognormal, with the merchant's honest price points and 25% price-tag snapping.

### 118-120
A pool of regular customers sized to the merchant's volume (at least 20), then the payer ids.

### 121-123
Front store (QuickKart): 10% of its honest payments come from the ring's payer pool — the only trace of the ring in its own behaviour.

### 124-125
Card vs UPI and refund flags from the category rates.

### 126
Blank.

### 127-128
Betting transactions: expand the betting day counts.

### 129-130
Times: the mimic uses the honest hourly profile and no wicket bursts; everyone else uses the betting profile (night-heavy) with 35% post-wicket.

### 131-132
Amounts: price-point clustering with the merchant's jitter (0 for all but the mimic).

### 133-135
Payers: the merchant's bettor community base, a fixed set of 400 bettors from that community, and one of them per transaction (so bettors repeat heavily).

### 136-138
Ring members: half of their betting payers come from the ring's shared pool, which is what links ring members in the payer-overlap graph.

### 139-140
A share of bets (`local_cover`) are paid by random locals, diluting the geography signal.

### 141-142
Card share (2%) and refund rate (0.1%) for bets.

### 143
Blank.

### 144-147
Concatenate honest and betting arrays; wrap seconds into a day; build timestamps = date + seconds.

### 148-156
Return one DataFrame with the merchant id, **raw** payer id (hashed later in `run.py`), timestamp, amount as float32, card flag, refund flag and `is_bet` — a ground-truth flag used only by `settlements_for` and never written to disk.

### 157-158
Spacing.

### 159-161
`settlements_for`: one payout row per merchant-day with a settlement delay.

### 162-166
Sign refunds negative, aggregate per merchant-day: payout amount and the share of the day's transactions that were bets.

### 167-168
Which merchants take instant settlement: honest ones that drew it (10%) and fraud ones that drew it (60%).

### 169-171
A fraud merchant settles fast only once betting has started (bet share > 20% that day) — a slow-drift merchant's payouts speed up as it drifts.

### 172-175
Draw slow (24–48 h) and fast (2–6 h) delays, pick per row, round, drop the helper column and return.
