# MerchantDNA — Build Plan (prototype)

## Context
The folder holds only `CLAUDE.md` (the spec) and `KICKOFF_PROMPT.md`. We need a working prototype for the PayU × IIM-B "Follow the Money" challenge (live demo on **26 Nov 2026**, 14 days away). It must detect *purpose drift* (e.g. a "bakery" collecting betting money) without hurting honest merchants with festival spikes. The prototype must run end to end on a laptop (CPU, under 10 min, `SEED=42`). After the code is done, we also produce a **PDF that explains the code**: every line for the core ML/data modules, and block by block for config, Makefile and Streamlit layout (the user chose this depth).

User decisions: autoencoder = **sklearn MLPRegressor**; **build all phases without stopping**. I stop only on a failure that needs the user's decision, and I commit after each phase.

Prototype mindset: simple, readable, explainable code. Keep each module small. Don't over-engineer. Choose clarity over cleverness, because the user must defend every line in front of judges.

## Environment
- The system Python is 3.14 (numba/umap/shap wheels are risky on it). Create a **Python 3.11 venv with `uv venv --python 3.11 .venv`**. The Makefile uses `.venv/bin/python`.
- Deps: pandas, numpy, pyarrow, scikit-learn, lightgbm, shap, networkx (built-in Louvain), umap-learn, scipy, plotly, streamlit, pyvis, pyyaml, joblib, pytest. For the PDF: `markdown` + `weasyprint` (fallback `fpdf2` if the pango libs are missing).
- Run `git init` and commit at the end of each phase.

## Spec ambiguities → decisions (to record in `docs/decisions.md`)
1. **Calendar realism:** a 120-day window can't contain both the real IPL (Mar–May) and Diwali (Oct–Nov). → Use a *synthetic* calendar: start 2026-07-15, a T20-league match schedule (~45 match evenings with wicket timestamps), and the Diwali window at days ~95–105. Say openly that it's synthetic.
2. **Scoring date:** score every merchant "as of" the last day. "Current" = last 7d/30d. "History" = days 0–45 (the baseline). Also compute weekly snapshots (rolling 7d every 7 days) for drift lead time and the animated DNA trajectory.
3. **Too few labels for the stacker:** 10% of 800 merchants is 80, with only ~4 frauds. → The analyst-labelled subset is 10% of merchants, sampled the way an analyst queue would be (enriched to ~25% fraud). Hero merchants are always excluded. The stacker is a shallow LightGBM (depth 2, monotone constraints) + isotonic calibration via CV. Evaluate only on the other 90%.
4. **Innocence gate implementation:** before fusion, split component inputs into *volume family* (volume z, growth, volume burst) and *composition family* (amount, hour, payer, network, website, verifier). If `volume_explained=True`, set the volume-family inputs to neutral peer values. Composition inputs are never touched (CLAUDE.md §6 rule).
5. **Tiers:** LOW < 30 ≤ MEDIUM < 70 ≤ HIGH on the 0–100 calibrated score. Thresholds live in `config.yaml`. QuickKart's MEDIUM has to come from network/payer-overlap signals while its own behaviour stays clean. If it doesn't emerge, tune the *simulator* (ring strength), not the score, and log the change.
6. **`slow_drift` lead time** = the first weekly snapshot where the score crosses MEDIUM, minus the day the simulated drift became "obvious" (night share > 2× peers).

## Repo layout (per CLAUDE.md §11)
```
config.yaml  Makefile  requirements.txt  README.md
merchantdna/
  utils/   config.py io.py logging.py
  sim/     calendar.py profiles.py merchants.py transactions.py archetypes.py heroes.py run.py
  features/ windows.py volume_time.py amount.py payer.py events.py settlement.py peer.py build.py
  models/  website.py verifier.py dna_autoencoder.py network.py innocence.py fusion.py train.py
  decision/ ladder.py explain_step.py
  eval/    baselines.py metrics.py ablation.py run.py
app/  Home.py  theme.py  pages/1_Command_Center.py … 6_Model_Lab.py
tests/ test_sim.py test_leakage.py test_heroes.py test_app_imports.py
docs/ plan.md decisions.md architecture.md limitations.md demo_script.md qa_prep.md
tools/build_code_guide.py   docs/code_guide/*.md   → docs/MerchantDNA_Code_Guide.pdf
```
Makefile targets: `data features train eval app all test demo guide`.

## Phases (built straight through)

**Phase 0 — Setup.** Venv, requirements, `config.yaml` (scale, seed, category profiles, archetype shares, costs, tiers), Makefile, pytest scaffold, README skeleton, and `docs/plan.md` (a copy of this plan).

**Phase 1 — Simulator** (`merchantdna/sim/`). Vectorised numpy generation per merchant: daily counts ~ Poisson(base × weekday × festival × growth), hour sampled from a 24-bin category profile, amount from a category lognormal mixture with price points. Payers come from a hashed pool per city tier. Fraud archetypes modify these generators (price-point clustering at 499/999/1999, night profile, IPL/wicket bursts, a shared payer pool, fast payouts). The mule ring shares device/bank/IP. `adaptive_mimic` copies the bakery hours and adds amount jitter, but keeps a nationwide repeat-payer pool. Three hero merchants have fixed IDs. `--small` = 120×60. Output: Parquet in `data/` plus sanity plots in `reports/sim/`. Target: full size in under 2 min.

**Phase 2 — Features** (`merchantdna/features/`). Windowed features as in §5 (volume/time, amount, payer-side, event alignment, settlement), the current vs own-history view, and peer z-scores by category × city tier × window. The weekly snapshot table feeds the DNA trajectory. `label`/`archetype` are dropped at load and asserted absent.

**Phase 3 — Signal models.** TF-IDF + LR on website text (missing → neutral 0.5). LightGBM multiclass verifier trained on baseline-window features → P(declared | behaviour). MLPRegressor autoencoder (bottleneck 12) on standardised features; the bottleneck is computed manually from the weights. Drift = distance to own history + distance to category centroid. UMAP 2D fitted once, then `.transform` the snapshots. NetworkX graph with IDF rarity weights on shared device/bank/IP/address/GST, Louvain communities, neighbour risk. Payer-overlap graph (Jaccard on hashed payers). All saved to `artifacts/` with joblib.

**Phase 4 — Innocence, fusion, actions.** Expected-volume model: LightGBM quantile (q05/q50/q95) on merchant-day (calendar flags, own trailing mean, peer same-day uplift) → `volume_explained` + reason. Composition tests: Jensen-Shannon (hour, amount bins, payer geo) and Wasserstein (amount) vs own baseline and vs peers in the same window → per-dimension shift + human-readable text. Then the gate (decision 4), the stacker + isotonic, SHAP drivers, the expected-cost ladder (rung costs and analyst capacity from config), and the merchant "Explain" verifier (festival claim accepted only if peers also spiked AND composition is unchanged). Output: `artifacts/scores.parquet` + per-merchant evidence JSON. Test: SweetCrust LOW, FreshOven HIGH, QuickKart MEDIUM, all from the models.

**Phase 5 — Evaluation.** Baselines: static rules (volume + night thresholds) and plain Isolation Forest. Metrics: PR-AUC, recall/precision@top 2%, FPR on legit surge merchants (headline), slow_drift lead time, ablations (no innocence / no network / no payer features), adaptive_mimic recall. Output: `reports/metrics.json`, PR-curve and ablation PNGs. Numbers are reported honestly. If we lose, investigate and log it in `docs/decisions.md`.

**Phase 6 — Dashboard** (Streamlit, read-only from artifacts/reports). Shared `theme.py` (large fonts, high contrast). Pages: Deep Dive → DNA Map (Plotly animated frames: FreshOven leaves the bakery cluster, SweetCrust stays) → Investigation Report (markdown export; PDF via the same renderer) → Model Lab (cost sliders → threshold/queue; "Inject Diwali spike" and "Make FreshOven mimic" re-score only that merchant through the saved pipeline, fast) → Network (pyvis HTML embed) → Command Center.

**Phase 7 — Polish.** `demo_script.md` (2-min video + 5-min stall), `limitations.md`, `qa_prep.md` (10 judge questions with answers using our real metrics), `architecture.md` with "why / production version / weakness" per model, `make demo`.

**Phase 8 — Code Guide PDF.** For each source file, `docs/code_guide/<module>.md` holds the annotations keyed by line ranges: line by line for sim/features/models/decision/eval, block by block for utils/app/config/Makefile/tests. `tools/build_code_guide.py` reads the *actual* source, renders the line-numbered code next to its explanations (it fails if an annotation's line range no longer matches the file, so the PDF can't drift from the code), and adds an intro chapter (architecture diagram, data flow, glossary of ML terms: TF-IDF, LightGBM, autoencoder, UMAP, Louvain, JS divergence, Wasserstein, conformal/quantile, isotonic, SHAP, expected cost). Output: `docs/MerchantDNA_Code_Guide.pdf` (~80–120 pages). `make guide` rebuilds it.

## Verification
- `make test`: archetype mix within tolerance, schema check, no `label`/`archetype` in any model input, hero tiers, all 6 app pages import.
- `time make all` on full scale < 10 min; check `reports/metrics.json` (MerchantDNA PR-AUC > both baselines; surge FPR lower).
- `make app`: open each page with the `run` skill/browser, check load < 3 s, take screenshots of the DNA Map and the two Model Lab controls.
- `make guide`: the PDF builds and spot-checked line numbers match the source.

## Risks
- QuickKart landing exactly in MEDIUM is the most fragile outcome. Tune the ring parameters in the sim and document it.
- 3 GB of free RAM: generate transactions per merchant chunk and keep amounts as float32/int types.
