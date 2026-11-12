# Kickoff prompt — paste this into Claude Code

> Put `CLAUDE.md` in an empty project folder first, open Claude Code in that folder, and paste everything below the line.

---

You are building **MerchantDNA**, a complete working prototype for a payments-fraud innovation competition. `CLAUDE.md` in this folder is the full spec. Read it completely before doing anything, and treat it as the source of truth.

## How I want you to work

1. **Plan first.** Write `docs/plan.md` with the phases below, the files you'll create in each, and any spec ambiguities, each with the decision you propose. Show me the plan and wait for my OK before writing code.
2. **Build phase by phase.** After each phase: run the tests, run the phase's command, show me the key output (row counts, metrics, a screenshot path), and commit with a clear message. Don't start the next phase while the current one is failing.
3. **Be honest about results.** Never hard-code a hero merchant's score or tune the evaluation to look good. If a hero merchant lands in the wrong tier or MerchantDNA doesn't beat a baseline, tell me, explain why, then fix the simulator or the model properly and document what you changed in `docs/decisions.md`.
4. **Keep it runnable.** CPU-only, the full pipeline under 10 minutes, deterministic with `SEED=42`. Use `--small` mode while developing and the full size before the final eval.
5. **Explain as you go.** I'm an aspiring ML engineer and must defend every choice in front of judges. For each model, add a short "why this method / what it would be in production / known weakness" note to `docs/architecture.md`.

## Phases

**Phase 0 — Setup:** repo layout from CLAUDE.md §11, `requirements.txt`, `config.yaml`, `Makefile`, pytest scaffold, README skeleton.

**Phase 1 — Simulator** (§4): all tables, legitimate and fraud archetypes, the three hero merchants, calendar with Diwali, IPL matches and wickets. Add sanity plots to `reports/sim/`: hourly profile by archetype, amount histograms, and a SweetCrust vs FreshOven comparison. Tests: archetype mix, hero merchants exist, schema is correct.

**Phase 2 — Features** (§5): rolling windows, payer-side features, event alignment, peer-relative z-scores. Test: no leakage of `label`/`archetype`.

**Phase 3 — Signal models** (§6): website classifier, behavioural category verifier, autoencoder DNA + drift, UMAP projection saved to artefacts, rarity-weighted merchant graph + Louvain, payer-overlap graph.

**Phase 4 — Innocence Engine, fusion, actions** (§6–7): expected-volume model with intervals, composition tests, the innocence gate rule (it discounts volume-driven risk only), calibrated stacker + SHAP, expected-cost action ladder, merchant "Explain" verification. Test: the hero merchants land in LOW / HIGH / MEDIUM through the models.

**Phase 5 — Evaluation** (§8): rule and Isolation Forest baselines, PR-AUC, recall@2% budget, FPR on legitimate surge merchants, ablations, adaptive-mimic stress test, detection lead time. Output to `reports/metrics.json` and PNGs. Give me a plain-English summary of the results, including weaknesses.

**Phase 6 — Dashboard** (§9): all 6 Streamlit pages. Priority order if time is short: Merchant Deep Dive → DNA Map (with the animated trajectory) → Investigation Report → Model Lab (cost slider + the two live "break it" controls) → Network Graph → Command Center. Projector-friendly styling, plain-English labels, every score shown with its reasons.

**Phase 7 — Demo polish:** `docs/demo_script.md` (a 2-minute video flow and a 5-minute stall walkthrough), `docs/limitations.md`, a README with one-command setup, and a `make demo` target that rebuilds everything and launches the app. List 10 tough judge questions with answers grounded in our actual metrics in `docs/qa_prep.md`.

## Start now

Read `CLAUDE.md`, then give me `docs/plan.md` and your list of questions/ambiguities. Don't write code until I approve the plan.
