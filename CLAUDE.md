# MerchantDNA — Project Brief for Claude Code

> Read this whole file before writing any code. It is the source of truth for scope, design and naming.

## 1. Context

- **Competition:** "Follow the Money" Innovation Challenge, CSITM IIM Bangalore × PayU.
- **Problem statement:** "The Bakery That Takes Bets". Merchants onboard with genuine documents (for example as a bakery), then use their payment account to collect money for prohibited activity such as illegal betting. Individual transactions look normal. Legitimate businesses also change, for example with festival spikes, so aggressive controls hurt honest merchants.
- **Judging:** Round 1 is an 8-slide deck plus a 2-minute video, and technical teams must show a working prototype. Round 2 (26 Nov 2026) is a live stall demo. Its weights are Demonstration/PoC 25%, Innovation 25%, Technical soundness 15%, Feasibility 15%, Communication 10% and Q&A 10%.
- **Team:** 4 people. The Product/ML lead owns modeling, the dev lead owns the Streamlit dashboard, the data lead owns the simulator, and the testing lead owns the demo and video.

## 2. One-line pitch

**MerchantDNA learns what a legitimate business of each category looks like from behaviour, not paperwork. It then tests every deviation against legitimate explanations before flagging anyone, and responds proportionately.**

Positioning rules (use these in UI copy and docs):
- Never claim "we detect betting". We detect **purpose drift**, meaning behaviour that is inconsistent with the declared category. Betting is the motivating case, and a human analyst decides.
- "Signals, not proof." Every flag shows its evidence.
- Regulatory hook: under the Promotion and Regulation of Online Gaming Act 2025, payment intermediaries are barred from facilitating online-money-game transactions. RBI's Payment Aggregator Directions (15 Sep 2025) require continuous monitoring of merchant transactions against business profiles. MerchantDNA turns that obligation into a working system with an audit trail.

## 3. Architecture (3 signal pillars, 1 arbiter, 1 action layer)

```
Synthetic data ──► Feature store (7d / 30d windows, peer-relative)
                        │
     ┌──────────────────┼────────────────────┐
     ▼                  ▼                    ▼
 CLAIMED PROFILE     BEHAVIOUR (merchant    NETWORK
 - website text      + payer side)          - rarity-weighted
   classifier        - category verifier      merchant graph
 - declared MCC      - drift embeddings     - payer-overlap
                       (autoencoder)          graph
     └──────────────────┼────────────────────┘
                        ▼
              INNOCENCE ENGINE (arbiter)
     expected-volume model + composition tests
                        ▼
        FUSION (calibrated stacker + SHAP)
                        ▼
     ACTION LADDER (expected-cost decision)
                        ▼
   Investigation report + Merchant "Explain" step
```

## 4. Synthetic data simulator (`merchantdna/sim/`)

No public labelled dataset exists for this problem, so we simulate one and say so openly in the pitch.

**Scale:** configurable. Default is 800 merchants × 120 days and about 3–5M transactions, generated in under 2 minutes. `--small` mode uses 120 merchants × 60 days for development. Use a fixed seed (`SEED=42`) so results are deterministic.

**Categories (with realistic price and time profiles):** bakery, grocery, restaurant, electronics, pharmacy, gym_or_tuition. The gym_or_tuition category legitimately uses fixed price points, which makes it a hard negative.

**Tables (write as Parquet to `data/`):**
- `merchants`: merchant_id, name, declared_category, city, onboard_date, has_website, website_text, device_ids, bank_account_hash, ip_cluster, address_hash, gstin_hash, is_franchise, `label` (ground truth, used ONLY for evaluation), `archetype`.
- `transactions`: txn_id, merchant_id, payer_id_hash, timestamp, amount, channel (UPI/card), payer_city, is_refund.
- `settlements`: merchant_id, date, payout_amount, payout_delay_hours.
- `calendar`: date, is_diwali_window, other festivals, ipl_match (bool), match_start, synthetic wicket timestamps.

**Legitimate archetypes:** normal steady merchant; festival-surge bakery (8–12× volume in the Diwali window, but the same amount mix, hours and payer mix as its peers); growing merchant (gradual organic growth); new merchant (short history); franchise chains (shared address or GST across outlets, which should be a weak link); merchants with no website (common and must not be penalised).

**Fraud archetypes (about 4–6% of merchants):**
1. `betting_collector`: amounts cluster on 499/999/1999, night-heavy, bursts during IPL match windows and after wickets, high payer repeat rate, payers spread nationwide, fast payouts, payers overlapping with other fraud merchants.
2. `slow_drift`: legitimate at first, then shifts towards the betting profile over 4–6 weeks.
3. `sleeper`: dormant or low volume, then a sudden burst.
4. `mule_network`: 3–6 merchants sharing a device, bank account or IP, with a common payer pool.
5. `adaptive_mimic`: copies a bakery's hourly profile and adds amount jitter. This is the stress test, so signals must come from the payer and network side.

**Hero merchants (fixed IDs, always generated):**
- `SweetCrust Bakery`: genuine, with a Diwali 10× spike. **Expected result: LOW risk, cleared by the Innocence Engine.**
- `FreshOven Bakery`: declared a bakery, has gaming-ish website text, ₹999 repeats, midnight activity, drift starting mid-period. **Expected result: HIGH risk.**
- `QuickKart Store`: looks individually normal, but shares a device and identifier with a mule ring. **Expected result: MEDIUM risk, "Investigate".**

⚠️ These outcomes must **emerge from the models**. Never hard-code a hero merchant's score. If an outcome is wrong, fix the simulator parameters or the model and document the change.

## 5. Features (`merchantdna/features/`)

Compute features per merchant over rolling 7d and 30d windows, plus a "current window vs own history" view.
- **Volume and time:** txn count, GMV, 24-bin hourly profile, night share (00–05), weekday profile, burstiness (Fano factor / max-minute concentration), growth rate.
- **Amount:** mean/median/IQR, amount entropy, top-price-point share, round-amount share, share at 499/999/1999.
- **Payer side (key):** unique payers, repeat-payer rate, new-payer rate, payer concentration (HHI), payer geo-dispersion vs merchant city, share of payers also seen at flagged merchants.
- **Event alignment:** correlation of activity with IPL match windows and post-wicket windows. Compute this only as a feature, never as a standalone rule.
- **Settlement:** payout velocity, payout delay, refund rate.
- **Peer-relative:** z-score of each feature against the merchant's declared-category cohort in the same city tier and calendar window.

## 6. Models (`merchantdna/models/`)

| Component | Method | Output |
|---|---|---|
| Website/identity | TF-IDF + logistic regression on `website_text`. Missing website → neutral, no penalty. | P(declared category given text) |
| **Behavioural category verifier** | LightGBM multiclass predicting category from behaviour features only. Train on early-window data. | P(declared category given behaviour). A low value means "doesn't behave like what it claims". |
| **Drift / DNA embedding** | Autoencoder per window (PyTorch, or sklearn MLPRegressor if simpler). Use the 8–16 dim bottleneck as the "Merchant DNA". | Drift = distance from own history + distance from category centroid. UMAP 2D projection for visuals. |
| **Network** | NetworkX graph. Edge weight = rarity (IDF-style) of the shared attribute: device and bank are strong, address and GST are weak (franchises). Louvain communities. Separate payer-overlap graph (merchant–merchant edge if they share many hashed payers). | Community risk, neighbour risk, payer-overlap score |
| **Innocence Engine** | (a) Expected-volume model: LightGBM on calendar + own-history + peer-cohort features, with conformal or quantile intervals. (b) Composition tests: Wasserstein / Jensen-Shannon on amount distribution, hourly profile and payer mix vs the same merchant last comparable period and vs peers in the same window. | `volume_explained` (bool + reason), `composition_shift` per dimension, human-readable explanation |
| **Fusion** | Gradient-boosted stacker over component scores, trained on a simulated "analyst-labelled" subset (~10% of merchants). Calibrate with isotonic regression. SHAP for explanations. | Calibrated P(purpose drift), 0–100 risk score, top drivers |

**Innocence rule (core design decision):** the Innocence Engine can discount *volume-driven* risk only. It **cannot** discount composition anomalies (price-point clustering, night share, payer overlap, network links). A festival explains more sales. It does not explain ₹999 repeats at midnight from payers spread across 20 states.

## 7. Action ladder (`merchantdna/decision/`)

Rungs: `Monitor` → `Soft step-up (ask merchant to explain / re-verify)` → `Rolling reserve / settlement hold` → `Limit reduction` → `Suspend + escalate`.

The rung is chosen by expected cost: act if `P(drift) × harm_if_missed > (1 − P(drift)) × cost_of_disrupting_legit`. The costs and analyst review capacity are configurable parameters in the UI.

**Merchant "Explain" step:** before any hold, the merchant can pick a reason (festival, new branch, promotion, bulk order, other). The system checks the claim against data (for example "festival" is accepted only if peers in the same window also spiked and composition is unchanged) and records the result in the report.

## 8. Evaluation (`merchantdna/eval/`)

- **Baselines:** (1) static rules (volume threshold, night-share threshold); (2) plain Isolation Forest; (3) full MerchantDNA.
- **Metrics:** PR-AUC, recall at a fixed review budget (top 2% of merchants), precision at that budget, **false-positive rate on legitimate surge merchants (the headline number)**, detection lead time in days for `slow_drift`.
- **Ablation:** full system without the Innocence Engine, without the network, and without payer-side features.
- **Stress test:** recall on `adaptive_mimic` only.
- Write all results to `reports/metrics.json` and `reports/*.png`. The dashboard reads from these and never recomputes on page load.

## 9. Dashboard (`app/`, Streamlit, multipage)

1. **Command Center:** KPI tiles (total, high/medium/low, pending investigation), risk distribution, action-ladder queue, review-budget usage.
2. **Merchant Deep Dive:** pick a merchant. Show claimed vs behaviour-predicted category, hourly heatmap, amount histogram vs category peers, payer-side metrics, IPL/event overlay timeline, and the Innocence verdict with its reasons.
3. **Merchant DNA Map:** UMAP scatter coloured by category. An animated trajectory shows FreshOven leaving the bakery cluster while SweetCrust's volume spikes but it stays inside the cluster. **This is the signature visual.**
4. **Network Graph:** interactive graph (pyvis or streamlit-agraph). Edge thickness = rarity weight, with communities highlighted and QuickKart's ring visible.
5. **Investigation Report:** risk score, SHAP drivers, evidence list, innocence assessment, network findings, the merchant's explanation and whether it was verified, the recommended action rung, and export to PDF/markdown.
6. **Model Lab (for judges):** metrics vs baselines, ablation table, PR curves, a cost slider (miss cost, disruption cost, analyst capacity) that shows the optimal threshold and queue size, and two live controls:
   - "Inject Diwali spike" into a genuine bakery, then re-score and show it cleared.
   - "Make FreshOven mimic a bakery" (jitter amounts, shift hours), then re-score and show which signals still fire.

UI copy: plain English, no jargon in headings, every score shown with its reasons.

## 10. Tech stack and conventions

- Python 3.11. Packages: pandas, numpy, pyarrow, scikit-learn, lightgbm, shap, networkx, umap-learn, scipy, plotly, streamlit, pyvis (or streamlit-agraph), torch (optional), pytest.
- Keep it CPU-only. A full pipeline (data → train → eval) must run in **under 10 minutes on a laptop**.
- Code style: type hints, small pure functions, docstrings on public functions, configuration in `config.yaml`, and no magic numbers buried in code.
- Every model artefact is saved to `artifacts/` with joblib. The app loads artefacts and never trains on startup.
- Tests: the simulator generates the expected archetype mix, there is no feature leakage (the `label` column never reaches the models), the hero merchants land in their expected tiers, and the app pages import without error.

## 11. Repo layout

```
merchantdna/
  CLAUDE.md
  README.md
  config.yaml
  Makefile            # make data | features | train | eval | app | all | test
  requirements.txt
  merchantdna/
    sim/  features/  models/  decision/  eval/  utils/
  app/
    Home.py
    pages/1_Command_Center.py ... 6_Model_Lab.py
  data/  artifacts/  reports/
  tests/
  docs/ demo_script.md  architecture.md  limitations.md
```

## 12. Definition of done

- `make all && make app` works from a fresh clone.
- The three hero merchants reach their expected tiers through the models alone, with a test that proves it.
- `reports/metrics.json` shows MerchantDNA beating both baselines on PR-AUC and a lower FPR on surge merchants. If it doesn't, report the honest numbers and investigate why.
- Every page loads in under 3 seconds and works on a projector (large fonts, high contrast).
- `docs/limitations.md` honestly covers synthetic data, cold-start merchants, adversarial adaptation, privacy (hashed payer IDs only) and the need for human review.
