source: merchantdna/sim/heroes.py
sha1: 4a8087ba97b6
title: Heroes — the three demo merchants
mode: line

The three merchants the demo is built around. Only their *behaviour* is fixed here — ids, names, cities, archetype and a few parameters. Their risk scores are never set anywhere; `tests/test_heroes.py` checks both that they land in the expected tiers and that no source file outside the simulator mentions them.

### 1-2
Docstring and future import.

### 3
Blank.

### 4
`HEROES` is a list of dicts; `build_merchants` reads it first, so the heroes always get ids M0000–M0002.

### 5-9
SweetCrust Bakery, Bengaluru: a genuine `festival_surge` bakery with a 10× Diwali peak, a solid base of 60 transactions a day and a clean website. Expected: LOW, cleared by the Innocence Engine.

### 10-16
FreshOven Bakery, Pune: `slow_drift` starting at 50% of the period with a 35-day ramp, full betting intensity (0.8), a website that leaks gaming vocabulary, instant payouts, and bets concentrated on ₹999 (70%) with some 499 and 1999. Expected: HIGH.

### 17-21
QuickKart Store, Mumbai: a `mule_network` member flagged as the ring's **front** (`is_front: True`), joining ring 0. Its own transactions are an ordinary grocery's (80 a day); it shares a device and IP with the ring and a slice of its payers. No website (which must not be penalised). Expected: MEDIUM, "ask the merchant".

### 22
End of the list.
