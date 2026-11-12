# Prompt for generating the MerchantDNA pitch PDF

Paste everything below the line into Claude / ChatGPT / Gamma / any slide or document generator. It is self-contained: every fact, number and design instruction is inside it. Do not let the tool invent numbers; everything it needs is here.

---

You are a senior pitch designer and technical writer. Produce a polished **8-page PDF deck** (one idea per page, landscape, presentation style) for a fintech innovation challenge. Audience: judges from a payments company (PayU) and a business school (IIM Bangalore) who weight **Demonstration 25%, Innovation 25%, Technical soundness 15%, Feasibility 15%, Communication 10%, Q&A 10%**. The deck must be convincing, honest and jargon-free; every number below is real and must be used exactly as given — never invent or round up.

## 1. The problem ("The Bakery That Takes Bets")

A merchant onboards with a payment aggregator using genuine documents — say, as a bakery. Then it uses the account to collect money for illegal online betting. Each payment looks normal (₹499, ₹999, a UPI transfer). At the same time, honest bakeries have real spikes — Diwali can mean 10× sales for a week — which look alarming to simple rules. So today's controls fail in both directions: static rules miss the fraud and punish honest merchants during festivals.

Regulatory pressure makes this urgent: under India's **Promotion and Regulation of Online Gaming Act 2025**, payment intermediaries are barred from facilitating online-money-game transactions, and the **RBI Payment Aggregator Directions (15 Sept 2025)** require continuous monitoring of merchant transactions against the declared business profile. Aggregators need a working system with an audit trail, not a rule list.

## 2. The idea in one line

**MerchantDNA learns what a legitimate business of each category looks like from behaviour, not paperwork. It tests every deviation against legitimate explanations before flagging anyone, and responds proportionately.**

Positioning rules (use this language):
- We never claim to "detect betting". We detect **purpose drift**: behaviour inconsistent with the declared category. Betting is the motivating case.
- **"Signals, not proof."** Every flag shows its evidence. A human analyst decides.
- We turn the RBI monitoring obligation into a working system with an audit trail.

## 3. How it works (architecture)

Three signal pillars → one arbiter → fusion → an action ladder.

**Pillar 1 — Claimed profile.** Does the merchant's website text read like its declared category? (TF-IDF + logistic regression; no website = neutral, never penalised.)

**Pillar 2 — Behaviour.** Does it *behave* like its category? Features over rolling 7-day and 30-day windows: trading hours (24-bin profile, night share), amount mix (median, spread, share at exactly ₹499/999/1999), **payer side** (repeat payers, payers from other cities, payers who also pay merchants in 3+ cities, concentration), timing against cricket matches and wickets, settlement speed, refunds. Everything is compared with peers in the same category and city tier (robust z-scores). Two models: a **category verifier** (LightGBM, trained to predict declared category from behaviour — low probability means "doesn't behave like what it claims") and a **Merchant DNA autoencoder** that compresses behaviour into a 12-number fingerprint; drift = distance from the merchant's own history and from its category's typical DNA. UMAP projects the DNA to a 2-D map for humans.

**Pillar 3 — Network.** A graph of merchants sharing devices, bank accounts, IPs, addresses or GST numbers, with edge weight = rarity (sharing a device used by 2 of 800 merchants is strong; sharing a franchise GST number is weak). A second graph links merchants whose hashed payers overlap. Suspicion propagates to neighbours without any labels. Louvain communities expose rings.

**The Innocence Engine (arbiter).** Before anyone is flagged, the system tries to explain the deviation legitimately. (a) An **expected-volume model**: expected daily volume = the merchant's own usual level × how much its peers moved that day, with a statistical band (quantile regression + conformal calibration). If peers also spiked, a 10× Diwali week is *explained*. (b) **Composition tests**: did the business mix change — hours, amount mix, payer geography — versus its own history and versus peers (Jensen–Shannon distance)? **Core rule: the engine can discount volume-driven risk only. It can never discount a composition change.** *A festival explains more sales. It does not explain ₹999 repeats at midnight from payers in 20 states.*

**Fusion.** Thirty component scores → a small gradient-boosted stacker constrained so that "more anomalous" can only raise risk, trained on a simulated analyst-labelled subset (80 merchants), calibrated to a true probability. **SHAP** gives the top reasons for every score in plain English ("75% of payments are exactly ₹499/999/1999 — peers 0.6%").

**Action ladder.** Monitor → Soft step-up (ask the merchant to explain) → Rolling reserve / settlement hold → Limit reduction → Suspend + escalate. The rung is chosen by **expected cost**: act only if P(drift) × harm of missing it > (1 − P) × cost of disrupting an honest merchant. Costs and analyst capacity are sliders. Before any hold, the merchant can give a reason (festival, new branch, promotion, bulk order); the system **tests the claim against the data** (e.g. "festival" is accepted only if peers also spiked and the business mix is unchanged) and records the result in the report.

## 4. Data (be open about this)

No public labelled dataset exists, so we built a **simulator** and say so on every page: 800 merchants × 120 days ≈ 4.7 million transactions, 6 categories (bakery, grocery, restaurant, electronics, pharmacy, gym/tuition), real Diwali 2026 dates, a synthetic cricket league with wicket timestamps. Honest archetypes include festival-surge bakeries (8–12× at Diwali), growing merchants, new merchants, franchise chains, and deliberate **hard negatives**: night pharmacies, honest nationwide online sellers, restaurants with ₹499/₹999 combos, sports bars busy on match nights, family shops sharing a device. Fraud archetypes (~6%): betting collectors, slow drift (legit, then shifts over 4–6 weeks), sleepers, mule rings with a clean "front" store, and an **adaptive mimic** that copies a bakery's hours, blurs its amounts and avoids fast payouts. Payer IDs are hashed; only city-level geography is used.

## 5. The three demo merchants (scores come from the models, nothing is hard-coded — a test proves it)

| Merchant | Story | Result |
|---|---|---|
| **SweetCrust Bakery** | Genuine bakery, 10× Diwali spike | **Risk 0 / 100, LOW — "Cleared" by the Innocence Engine.** Volume up 3.3×, peers rose up to 10×, only 4 of 30 days above the expected range, business mix unchanged. Action: Monitor. |
| **FreshOven Bakery** | Same paperwork; drifts into collecting bets mid-period | **Risk 82 / 100, HIGH.** 75% of payments at exactly ₹499/999/1999 (peers 0.6%), 12% at midnight–5 am, most payers from other cities, DNA drift 13× its category's typical spread. Not cleared: business mix changed in hours, amounts, payers. Action: Suspend + escalate. |
| **QuickKart Store** | Looks like a normal grocery; shares a device and IP with a mule ring | **Risk 27 / 100, MEDIUM.** Shares device + IP with three merchants scoring 67–83 and 4% of its payers with them. Action: Soft step-up — ask the merchant to explain, not a hold. |

## 6. Results (measured on 720 held-out synthetic merchants the models never saw labels for; 30 of them fraud)

| Method | PR-AUC (90% interval) | Recall at a 2% review budget | False alarms on festival-surge merchants (own threshold) |
|---|---|---|---|
| Static rules (volume ≥3× or night share ≥20%) | 0.20 (0.09–0.30) | 13% | **79%** |
| Static rules + our Innocence gate | 0.26 | 13% | 40% |
| Isolation Forest (generic anomaly detector) | 0.78 (0.64–0.88) | 47% | 0% |
| **MerchantDNA** | **0.97 (0.93–0.99)** | 47% | **0%** |

- At MerchantDNA's own MEDIUM threshold: recall 97%, precision 67%; false alarms on honest merchants 2% — and every one of those is an honest nationwide online seller (a known, documented case).
- **Slow drift** (the FreshOven pattern): caught a median **49 days before static rules** and **14 days before Isolation Forest** (9 of 9 detected).
- **Adaptive mimic stress test:** 4 of 5 mimics still reach MEDIUM or above; static rules and Isolation Forest catch 0 of 5. What still fires is the payer side — hours and amounts can be faked; *who pays* cannot.
- **Ablations (honest):** without payer-side features PR-AUC falls from 0.97 to 0.86 and QuickKart drops to LOW — payers are the strongest pillar. Removing the Innocence Engine or the network barely changes the PR-AUC of the full system; the engine's measured value is elsewhere: bolted onto static rules it halves their festival false alarms (79% → 40%) and guarantees by construction that volume alone never flags an explained surge. The network's value is in investigation (who is linked to whom).

## 7. The working prototype (Demonstration = 25%)

A Streamlit dashboard, six pages, projector-friendly: **Command Center** (KPIs, risk distribution, action queue, review-budget usage), **Merchant Deep Dive** (claimed vs behaved category, score drivers, Innocence verdict, timeline with the expected-volume band and Diwali/match overlays, hour × day heatmap, amount mix vs peers, payer-side table), **Merchant DNA Map** (the signature visual: an animated week-by-week map where FreshOven walks out of the bakery cluster while SweetCrust's volume explodes but its DNA stays put), **Network Graph** (interactive; thicker edge = rarer shared identifier; QuickKart's ring visible), **Investigation Report** (score, SHAP drivers, evidence, innocence assessment, network findings, the merchant's explanation and whether the data supported it, recommended action; export to Markdown/PDF), **Model Lab** (metrics vs baselines, ablations, cost sliders showing where each action becomes worth it, and two live "break it" controls: inject a 10× Diwali spike into a genuine bakery → re-scored in under a second and cleared; make FreshOven mimic a bakery → score drops from 82 to 68 but stays HIGH because the payer signals still fire). The full pipeline (data → features → models → evaluation) runs in **under 3 minutes on a laptop, CPU only**, deterministically. 24 automated tests, including: no label ever reaches a model, and the three demo merchants land in their tiers through the models alone.

## 8. Honesty and limitations (judges trust what you admit)

- Synthetic data: proof of method, not a forecast. Our first simulator was too easy (every fraud scored 94, every honest merchant 0.2); we made it harder on both sides and the PR-AUC fell from 1.00 to 0.97.
- 80 analyst labels: scores are lumpy and intervals are wide; every analyst decision in production is a new label.
- QuickKart's MEDIUM rests more on payer evidence than on the shared device; with a perfectly clean front store it drops to LOW. Documented, not tuned away.
- Honest nationwide online sellers look like betting fronts on payer geography and land in MEDIUM ("ask the merchant"), never a hold.
- A fraudster who also diversifies payers (many small local non-repeating payers) would slip through this prototype; the long-term defence is the network of confirmed-case payer pools.
- Human review is mandatory. Suspension is recommended only above P ≈ 74% with the default costs, and the costs are policy sliders.

## 9. Feasibility and path to production

Drop-in at an aggregator: it needs transaction feeds with pseudonymous payer IDs stable across merchants (which an aggregator has), identifiers from onboarding, and the declared MCC. Production changes: daily aggregate pipeline instead of recompute, a graph store for identifiers, an "other / out-of-distribution" class for the category verifier, thousands of analyst labels with isotonic calibration, per-cohort monitoring of the volume band. The design is parallel by merchant.

## 10. Team

Four people: Product/ML lead (modelling), dev lead (dashboard), data lead (simulator), testing lead (demo and video).

---

## Design and structure instructions for the PDF

Produce exactly **8 pages**, each with a short headline that states the takeaway (not a topic label), at most ~60 words of body text, and one strong visual. Suggested pages:

1. **Title + one-line pitch** — "MerchantDNA: learns what a legitimate business looks like from behaviour, not paperwork." Subtitle with the problem statement name and the regulatory hook.
2. **The problem cuts both ways** — a bakery that takes bets vs a bakery at Diwali; rules fail in both directions (use the 79% festival false-alarm number for rules).
3. **Three pillars + the Innocence Engine** — the architecture diagram; the core rule in a callout: "A festival explains more sales, not different sales."
4. **The Innocence Engine in action** — SweetCrust vs FreshOven side by side: same-looking volume spike, opposite verdicts, with the reasons.
5. **Signals, not proof** — the FreshOven investigation report: score, top drivers in plain English, evidence lines, recommended action; and the merchant "Explain" step.
6. **It works — and it beats the baselines** — the results table (PR-AUC, festival false alarms, lead time, mimic stress test). Include the honest ablation sentence about payer features.
7. **Proportionate action + feasibility** — the action ladder with the expected-cost rule, cost sliders, analyst capacity; what an aggregator needs to deploy it; the regulatory audit trail.
8. **Honest limitations + the demo** — four limitations in one line each; what the judges will see at the stall (DNA map animation, network ring, live "break it" controls); team.

Style: clean, high-contrast, large type (readable on a projector), one accent colour for "risk" (deep red), green for "cleared", amber for "investigate". Use plain English; no equations except the single expected-cost inequality on page 7. Every score shown must have its reasons next to it. Put "All data is synthetic" in the footer of every results page. Do not add stock photos. Do not invent any number, quote, or feature that is not in this prompt.
