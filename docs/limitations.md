# Limitations — read before quoting any number

## 1. The data is synthetic
There is no public labelled dataset of payment-aggregator merchants with betting fronts. Everything here runs on a simulator we wrote (`merchantdna/sim/`), and we designed both the fraud and the honest hard cases. That cuts both ways:

- The fraud archetypes are *our* guess at how betting collection looks. Real fronts may use different amounts, split flows across many small merchants, or route through wallets we never see.
- We made the simulator harder after the first run (every fraud scored 94, every honest merchant 0.2) by adding honest night pharmacies, nationwide online sellers, fixed-menu restaurants, sports bars, shared family devices, price-tag snapping and traveller payers. PR-AUC fell from 1.00 to 0.97. On real data expect it to fall much further.
- The cricket league is synthetic (dates, matches, wickets). Diwali dates are real.

**How to read the metrics:** as proof that the *method* separates the cases it was designed for, not as a forecast of production performance.

## 2. Cold-start merchants
A merchant with fewer than 7 active history days has no "own history" view and no volume verdict (the Innocence Engine says "not enough history"). It is scored on peer-relative composition and network signals only. A betting front that is *born* betting looks like a sleeper to us only once it has a few weeks of data; before that, only payer overlap with known rings and website text can catch it.

## 3. Adversarial adaptation
The adaptive-mimic archetype copies a bakery's hours, jitters amounts and avoids match bursts and fast payouts. We still catch 4 of 5 at MEDIUM, through payer-side signals (repeat payers from many cities, overlap with other flagged merchants). An adversary who also diversifies payers — many small, local, non-repeating payers — would slip through this prototype. Over time the strongest defence is the network side (confirmed-case payer pools), which needs real labels.

## 4. Few labels, lumpy scores
The stacker has 80 analyst labels. Scores cluster (many frauds share exactly 82) and the PR-AUC interval is wide (0.93–0.99). QuickKart's MEDIUM depends mainly on payer-side evidence; with ~3 labelled clean front stores the model cannot convict on identity links alone. With a perfectly clean front (3% ring payers instead of 10%) QuickKart drops to LOW. We report this rather than tune it away (`docs/decisions.md`, simulator change 4).

## 5. Honest nationwide sellers
All 16 honest "nationwide online seller" merchants land in MEDIUM (median score 27): their payer geography genuinely looks like betting. The action ladder sends them to "ask merchant to explain", not a hold. Note that the automatic Explain-step checks do *not* clear them either (their payers really do span many cities, so "new branch" and "promotion" fail the geography check); an analyst has to recognise the business model. This is the price of payer-geography features and must be monitored in production — in a real deployment the declared category would include "online / nationwide seller" and the cohort comparison would absorb it.

## 6. Category verifier blind spot
The verifier answers "which of the six categories does this behaviour match best?", not "does it match any?". FreshOven shows "behaves like bakery, 99%" while HIGH. The DNA drift score and composition tests cover this, but the verifier should get an out-of-distribution class in production.

## 7. Privacy
Only hashed payer IDs (splitmix64 of a synthetic ID) and city-level geography are used. The payer-overlap graph works on hashes. No names, phone numbers or account numbers exist in the data. In production the same design holds: the system needs *pseudonymous* payer identity that is stable across merchants, which an aggregator has, and nothing more.

## 8. Human review is mandatory
Every output is a *signal with reasons*, never a verdict. The action ladder recommends; an analyst decides. The highest rung ("Suspend + escalate") is reached only above P ≈ 74% with the default costs, and the costs themselves are a policy choice exposed as sliders. The regulatory framing (PROGA 2025, RBI PA Directions 2025) obliges intermediaries to monitor and act proportionately — not to automate suspension.

## 9. Engineering limits
Single machine, pandas, ~5M transactions in ~3 minutes end to end. The feature code is per-window and recomputes from raw transactions; production would stream daily aggregates. UMAP takes a third of training time and is for the visual only.
