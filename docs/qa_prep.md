# Judge Q&A — ten hard questions, answered with our numbers

**1. "Your data is synthetic. Why should we believe any of this?"**
You shouldn't believe the numbers as a forecast; believe the *method*. There is no public labelled dataset for this problem, so we built a simulator and say so on every page. We made it deliberately hard: honest night pharmacies, online sellers with payers across India, restaurants with ₹499 combos, sports bars busy on match nights, family shops sharing a device, fraud merchants that vary in intensity and that mimic bakeries. The first version scored 1.00 PR-AUC; after making it realistic, 0.97 with a 0.93–0.99 bootstrap interval. The pipeline is designed so that real merchant data drops in at the `data/` layer with no model change.

**2. "Isn't this just 'detect betting'? That's a rule."**
No. We never look for betting. We learn what each declared category *does* — hours, amounts, who pays, how fast money leaves — and score deviation from that. Betting is the motivating case the simulator uses; any purpose drift (crypto, lending apps, pharma without licence) would surface the same way if its behaviour differs from the declared business. The static rule baseline *is* the "detect betting" approach (night share, volume) and scores PR-AUC 0.20.

**3. "How do you avoid punishing a bakery at Diwali?"**
The Innocence Engine. For each merchant-day we compute an expected range = own usual volume × how much *peers in the same category and city tier* moved that day, widened by a conformal interval. SweetCrust's 10× spike lands inside that band because every bakery in tier-1 cities surged. Then the rule: the engine may discount *volume* risk only. If hours, amounts or payer geography changed, it refuses. On 77 held-out festival-surge merchants: 0 false alarms, against 79% for static rules.

**4. "What happens when the fraudster copies a bakery's pattern?"**
We built that adversary ("adaptive mimic": copies hours, jitters amounts, avoids match bursts and fast payouts). 4 of 5 still reach MEDIUM; neither baseline catches any. What still fires is the payer side: the same few hundred payers from many cities paying again and again, and overlap with other flagged merchants. Hours and price points are the fraudster's to choose; *who pays* is not. If they also diversify payers, this prototype misses them — honest answer — and the long-term defence is the network of confirmed-case payer pools.

**5. "Why LightGBM, an autoencoder *and* a graph? Isn't one model enough?"**
They see different things. The verifier asks "does this behave like a bakery?" (supervised, categories as labels — no fraud labels needed). The autoencoder gives a compact fingerprint so we can measure *drift* over time without labels. The graph sees what no per-merchant model can: QuickKart is individually clean but shares a device with a ring. The ablation table is honest: drop payer features and PR-AUC falls to 0.86 and QuickKart drops to LOW; drop the network and the PR-AUC barely moves but you lose the explanation. We kept the network because investigations need it, not because the metric demands it.

**6. "How much labelled data do you need?"**
We used 80 analyst labels (10% of merchants, enriched to 26% fraud, labelled by case as real queues are). That is enough for a depth-2 monotone stacker over 30 pre-built signals, because the heavy lifting is unsupervised and peer-relative. The cost: scores are lumpy (many frauds share 82) and the interval is wide. Every analyst decision in production is a new label, so this improves weekly.

**7. "What does the action ladder actually do, and who decides?"**
It picks the cheapest proportionate action by expected cost: P × harm if missed versus (1 − P) × cost of disrupting an honest merchant, per rung. With our defaults, "ask the merchant to explain" starts at P ≈ 5%, a settlement hold at 40%, suspension at 74%. Both costs and analyst capacity are sliders. An analyst makes every decision; the system recommends and records the reasons, including the merchant's own explanation and whether the data supported it. That audit trail is what the RBI Payment Aggregator Directions (Sept 2025) ask for.

**8. "Your QuickKart demo — is that just the shared device?"**
Mostly not, and we say so. The device + IP links put it in the ring's community and raise neighbour risk to 0.66, but with only ~3 labelled front stores the stacker learned to lean on payer evidence: 3% of QuickKart's payers belong to the ring's pool, and its payer geography is off for a Mumbai grocery. When we made the front perfectly clean (ring payers 3% instead of 10%) it dropped to LOW. It is documented in `docs/decisions.md`. In production, confirmed-case links would carry far more weight because there would be thousands of them.

**9. "Where are the false positives?"**
At MEDIUM-or-above on held-out data: 2% of honest merchants, and *all* of them are one archetype — honest nationwide online sellers (16 merchants, median score 27). Their payer geography genuinely looks like betting. They get "ask the merchant to explain", never a hold. The automatic explanation checks do not clear them (their payers really are everywhere), so an analyst has to recognise the business model — in production the declared category would include "online seller" and the peer comparison would absorb it. Night pharmacies, sports bars, fixed-menu restaurants, family shared devices and all 77 festival merchants: zero flagged.

**10. "What would it take to put this in production?"**
(1) Real merchant and transaction feeds with pseudonymous payer IDs stable across merchants — an aggregator already has this. (2) A daily aggregate pipeline instead of per-window recompute. (3) A graph store for identifiers. (4) An out-of-distribution class for the verifier. (5) Thousands of analyst labels and isotonic calibration once there are > 1,000. (6) Per-cohort monitoring of the volume band's coverage. The full pipeline here runs in under 3 minutes on a laptop for 800 merchants and 4.7M transactions; the design is embarrassingly parallel by merchant.

---
*Numbers from `reports/metrics.json`: PR-AUC 0.973 [0.934–0.995] vs Isolation Forest 0.776 and rules 0.197; recall at the 2% review budget 47% (both good methods are budget-bound; at MEDIUM threshold MerchantDNA reaches 97% recall at 67% precision); slow drift caught a median 49 days before rules and 14 days before Isolation Forest.*
