# Design decisions and changes log

Every place where we interpreted the spec, or changed the simulator or a model after seeing a result, is recorded here with the reason. The rule we followed: **never hard-code a hero merchant's score. If an outcome is wrong, fix the simulator or the model, and write the change down.**

## Spec interpretations

| # | Question | Decision | Why |
|---|---|---|---|
| 1 | A 120-day window cannot contain both the real IPL (Mar–May) and Diwali (Oct–Nov). | Real Diwali 2026 dates (window 30 Oct–10 Nov, peak 6–9 Nov), plus a **synthetic** T20 league on about 40% of days, with 12 wicket timestamps per match. | Diwali is the legitimate surge we must not punish. The cricket league only has to exist and be realistic. We say openly that it is synthetic. |
| 2 | What is "now"? | Every merchant is scored as of 11 Nov 2026. "Current" = last 30 days (last 7 for short-term volume). "History" = the first 37.5% of days (45 days at full scale). Weekly snapshots of trailing 30-day windows feed the trajectory and the lead-time metric. | The Diwali spike must fall inside the scoring window, or the Innocence Engine would have nothing to explain. |
| 3 | With 10% of 800 merchants labelled there are only ~4 frauds. | The analyst-labelled subset is 10% of merchants, enriched to ~25% fraud (analyst queues are enriched in practice). Hero merchants are always excluded. Evaluation uses only the other 90%. | A stacker cannot learn from 4 positives. |
| 4 | How does the Innocence Engine "discount volume only"? | Fusion inputs are split into families. If `volume_explained` is true, only the volume family (`z_cnt_short`, `z_vol_ratio_hist`, `z_growth_short_vs_long`, `z_daily_fano`, `exceed_rate`) is set to the neutral value 0. Composition, payer, pattern, website and network inputs are never touched. | This is the core rule in CLAUDE.md §6, written as code (`fusion.gate`). |
| 5 | Tiers and actions | Tiers (for humans): LOW < 15 ≤ MEDIUM < 50 ≤ HIGH. Actions come from expected cost (§7) and are independent of tiers. | Analysts read a tier at a glance, and the ladder decides the proportionate action. Both are configurable. |
| 6 | Lead time for `slow_drift` | Lead = the day a baseline first flags the merchant minus the day MerchantDNA first reaches MEDIUM (weekly snapshots). "Never flagged" counts as one week after the end. | We have no ground-truth "drift became obvious" field in the public data, so we compare against what a real team would otherwise use. |

## Simulator changes after seeing results

1. **Volume trimmed** (base daily txns about −25%). The first full run produced 6.0M transactions; the spec targets 3–5M. Now about 4.7M.
2. **The first version was far too easy.** Every fraud scored 94 and every honest merchant 0.2 (PR-AUC = 1.0). A judge would rightly not believe that. We made both sides realistic:
   - *Honest hard negatives:* night-owl restaurants and 24h pharmacies, nationwide online sellers (45% non-local payers), fixed-menu restaurants with ₹499/₹999 combos, sports bars that are busy on match evenings, and honest merchants that share a device (family shops).
   - *Honest noise:* 25% of honest amounts snap to common price tags (x99, x49, so ₹499 and ₹999 appear in honest data too), 3% of honest payments come from travellers who pay in many cities, and 10% of honest merchants use instant settlement.
   - *Fraud heterogeneity:* betting share varies 30–80% per merchant, price-point clustering strength 40–100%, local "cover" payers 20–60%, and only 60% of frauds take fast payouts. Bettors come from 4 separate communities, not one pool.
   - *Adaptive mimic:* copies the bakery's hours, uses ±15% jitter around price points, avoids match bursts and fast payouts.
3. **More mule rings** (1.2% → 2% of merchants, betting collectors 1.8% → 1.4%), so there are about 4 rings, each with a clean "front store".
4. **Front stores (QuickKart) – an experiment we report honestly.** By design, 10% of a front store's payers come from the ring's shared nationwide payer pool. We tried 3% (a perfectly clean front). QuickKart then scored 9.7 (LOW), because the identity links alone moved it only about 3 points. With only about 3 labelled front stores, the supervised stacker cannot learn "clean but strongly linked" from identity links alone. We kept the original 10% design value. QuickKart therefore reaches MEDIUM mainly through **payer-side** evidence (payer geography + payer overlap with the ring), and the identity links appear in its report as the explanation. See `limitations.md`.

## Model changes after seeing results

1. **Burstiness feature vectorised** (the lambda aggregation took 32 s per window, now 0.4 s).
2. **Cold-start merchants:** a new merchant without history had `vol_ratio_hist` = 64×. Now merchants with fewer than 7 active history days get a neutral history view (`has_history = 0`), and the volume model treats them as "not enough history".
3. **Peer band p10–p90 → p5–p95.** Surge bakeries are about 25% of the bakery cohort, so p90 sat in the *middle* of the honest surge group, and half of the honest surge bakeries (including SweetCrust, 5 of 30 days above the band) were "unexplained". "Within the range peers experienced" is better read as p5–p95.
4. **Calibration isotonic → sigmoid (Platt).** With 80 labels, isotonic regression turned into a 4-step function (all frauds got exactly the same score). The literature (Niculescu-Mizil & Caruana 2005) recommends sigmoid calibration below about 1,000 calibration points. Isotonic remains a config option.
5. **Stacker regularised** (60 trees, `min_child_samples` 8, L2 = 5, 50% feature sampling). The un-regularised stacker saturated at P = 0 or 1.
6. **Network propagation uses "excess suspicion".** The stage-1 suspicion was an average percentile, so a *typical* neighbour passed on about 0.5. Every merchant's neighbour risk was about 0.48, and there was no contrast. Now only neighbours in the top 20% of behavioural suspicion pass suspicion on. Ring members score about 0.74 and others about 0.05.
7. **Case-based analyst labels.** Analysts label cases, not single merchants: when a labelled fraud is strongly linked (shared device or bank) to others, the whole case is labelled. This is how real investigation queues work, and it gives the stacker examples of front stores.
8. **Determinism.** LightGBM runs single-threaded with `deterministic=True`, and the labelled set is sorted. Before this, Python's per-run string-hash ordering changed the stacker's row order and moved QuickKart between 25 and 38.
9. **Action costs.** With `cost_disrupt_legit` = ₹40k, the expected-cost ladder put settlement holds on anyone above P = 3%. We set the cost of wrongly disrupting an honest merchant to ₹6 lakh (churn, lost lifetime value, complaints) against ₹5 lakh harm per missed betting front per cycle. Resulting ladder: Monitor < 4.6% < Soft step-up < 40% < Reserve < 61.5% < Limit < 74% < Suspend. Both costs are sliders in the Model Lab (now under *Proof & Try It → For technical judges*).

## What the ablations taught us (reported, not hidden)

- **Payer-side features are the strongest pillar.** Without them, PR-AUC falls from 0.97 to 0.86, and QuickKart falls from 27 to 5.
- **The Innocence Engine barely changes the stacker's PR-AUC**, because the stacker already learned from the labels that raw volume is not predictive. Its measured value is elsewhere. Applied to static volume rules, it halves their false-positive rate on festival merchants (79% → 40%). It also guarantees by construction that volume alone can never push an explained surge merchant up, and it produces the evidence for the merchant "Explain" step.
- **The identity network adds little measurable lift in this simulation**, because most ring members are already caught by their own behaviour. Its value is in the investigation (who is linked to whom), plus the limitation above.

## Demo changes for Round 2 (21 Nov 2026)

1. **Six dashboard pages → Home + 3.** A 5-minute stall walkthrough could not cover six dense pages. Command Center became the Home KPIs and a top-10 queue. Deep Dive, Network Graph and Investigation Report merged into one **Merchant Story** page. Model Lab became **Proof & Try It**: headline numbers and the two live controls, with PR curves, ablation, per-archetype rates and cost sliders moved into a collapsed expander. No model, artefact or metric changed.
2. **Auto-drafted STR** (`merchantdna/decision/str_report.py`). It is a template, not an LLM, so it works offline and is reproducible. It is built only from the evidence bundle, public merchant fields (hashed identifiers) and current-window features, and never reads ground truth (tested). It describes purpose drift, not a crime. The download stays disabled until an analyst ticks "I have reviewed this draft".
