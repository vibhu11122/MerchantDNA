# MerchantDNA — architecture and model notes

For each component: **why this method**, **what it would be in production**, and **known weakness**. Numbers are from `reports/metrics.json` (800 synthetic merchants, 720 held out for evaluation).

## Data flow

```
config.yaml ─► sim/      ─► data/{merchants,transactions,settlements,calendar}.parquet
                             │
             features/   ─► artifacts/features_{baseline,current,snapshots}.parquet
                             │       + daily_counts, hour_day_counts, cohort_stats
             models/train ─► artifacts/{bundle.joblib, scores.parquet, evidence.json,
                             │          dna_trajectory, volume_bands, snapshot_scores}
             eval/run    ─► reports/metrics.json + *.png
             app/        ─► reads artifacts/ and reports/ only (never trains)
```

Three windows per merchant: **history** (first 45 days), **current** (last 30 days, as of 11 Nov 2026) and **weekly snapshots** (trailing 30 days every 7 days, for the trajectory and lead time).

## 1. Feature store (`merchantdna/features/`)

| Family | Examples | Why |
|---|---|---|
| Volume | count, GMV, growth 7d vs 30d, daily Fano, volume vs own history | What a static rule sees. Deliberately kept separate so the Innocence Engine can neutralise it. |
| Time | 24-bin hourly profile, night share (00–05), evening share, weekend share, within-hour burst index | Betting flows are night-heavy and bursty; bakeries are not. |
| Amount | median, log-IQR, entropy, top-price share, exact 499/999/1999 share, near-price-point share, 19-bin histogram | Bets cluster on fixed top-up amounts. |
| Payer side | unique payers, repeat share, new-payer rate, HHI, non-local share, payer-city entropy, share of payers who pay in 3+ cities | The hardest thing to fake: who pays. |
| Event alignment | match-evening lift, correlation with match days, post-wicket lift (shrunk with a pseudo-count) | A feature, never a rule. |
| Settlement | payout delay, fast-payout share, refund rate, card share | Betting fronts cash out fast. |
| Relative views | ratio vs own history, deltas vs own history, robust z-score vs cohort (category × city tier) | A gym's fixed prices are normal *for gyms*. |

Robust z = (x − cohort median) / (1.4826 × MAD). Cold-start merchants (< 7 active history days) get a neutral history view rather than a penalty.

## 2. Claimed profile: website classifier (`models/website.py`)

- **Method:** TF-IDF (unigrams + bigrams) → multinomial logistic regression predicting the *declared* category from website text. Out-of-fold predictions, so no merchant is scored by a model that saw its own text. Output: `website_mismatch` = 1 − P(declared | text). No website → cohort median (neutral).
- **Production:** crawl the merchant's declared URL and app-store listing; a small sentence-embedding model; add a "gaming vocabulary" detector maintained by compliance.
- **Weakness:** text is cheap to fake. In our run it ends up with ~0 weight in the stacker because behaviour is far more informative. It still appears in the report as context ("words pulling away from bakery: jackpot, odds, withdrawal").

## 3. Behavioural category verifier (`models/verifier.py`)

- **Method:** LightGBM multiclass on the SHAPE features (hours, amounts, payers, events, settlement — never volume) trained on the history window, cross-fitted in 5 folds so every merchant is scored by a model that never saw it. Output: P(declared | behaviour) and "behaves like".
- **Production:** same, trained on millions of merchants with MCC labels; retrain monthly.
- **Weakness (important for Q&A):** it answers "which of the six categories?" not "is it any of them?". A betting front that no longer looks like *any* category still gets assigned the closest one — FreshOven shows "behaves like bakery, 99%" even at HIGH risk. That is why the DNA drift score exists. In production, add an "other / out-of-distribution" class or use the autoencoder's reconstruction error as the OOD signal.

## 4. Merchant DNA: autoencoder + drift (`models/dna_autoencoder.py`)

- **Method:** sklearn `MLPRegressor` with layers 32 → **12** → 32 (tanh) trained to reconstruct the standardised SHAPE features. The 12-unit bottleneck is read by running the first layers forward by hand. Drift self = distance between the current code and the merchant's history code; drift category = distance to the declared category's median code; both divided by the category's typical spread. UMAP (fitted once on history + snapshot codes) gives the 2-D map.
- **Production:** a sequence model over daily feature vectors (GRU or small transformer) producing the embedding; nearest-neighbour search for "merchants whose DNA looks like known fronts".
- **Weakness:** UMAP distances are only locally meaningful; the 2-D picture is for humans, scoring uses the 12-D code. The autoencoder is unsupervised, so it also flags honest-but-unusual businesses (night pharmacies) — the stacker learns to down-weight those from labels.

## 5. Network pillar (`models/network.py`)

- **Method:** identity graph with edge weight = attribute strength × IDF rarity: `strength × log(N / holders)`. Device and bank are strong (1.0), IP 0.4, address and GST 0.15 (franchises legitimately share them). Louvain communities. A separate payer-overlap graph links merchants whose unique payer sets have Jaccard ≥ 0.02 with ≥ 5 shared payers (payers seen at > 50 merchants are dropped as noise). Risk propagates **label-free**: each merchant inherits the behavioural suspicion of its neighbours — but only neighbours in the top 20% of suspicion pass anything on, so a typical neighbour contributes zero.
- **Production:** graph database (device fingerprint, bank, UPI VPA, PAN, phone, email, IP), and personalised PageRank from confirmed cases.
- **Weakness:** the measured lift is small here (PR-AUC 0.973 with vs 0.973 without), because ring members already look suspicious on their own. Its value is in explaining QuickKart and prioritising investigations. With ~3 labelled "clean front stores", the stacker cannot learn to convict on links alone — see limitations.

## 6. Innocence Engine (`models/innocence.py`)

### (a) Expected-volume model
Expected count for merchant *m* on day *d* = own usual rate × median uplift of peers (same category and city tier) on day *d*. LightGBM **quantile regression** (q05, q50, q95) models the residual in log space from calendar flags, own history level and day of month; the band is widened by the spread of peer uplifts that day (p5–p95) and by a **split-conformal** correction fitted on 14 held-out days, so the band has the promised coverage. `volume_explained` = at most 15% of window days above the upper band.

### (b) Composition tests
Jensen–Shannon distance (base 2, in [0, 1]) of three distributions — hourly profile, 19-bin amount histogram and payer geography (local / other-city / multi-city) — against the merchant's own history and against the cohort's mean profile now. Each distance is robust-z-scored within the cohort; a dimension "shifts" when z > 3 and JS > 0.05.

### The gate (`fusion.gate`)
If volume is explained, the **volume family only** (`z_cnt_short`, `z_vol_ratio_hist`, `z_growth_short_vs_long`, `z_daily_fano`, `exceed_rate`) is set to 0 before fusion. Nothing else is touched. *A festival explains more sales, not different sales.*

- **Production:** the same model at merchant-day granularity with holiday calendars by state, marketing-event feeds from the merchant, and a proper conformal pipeline with per-cohort coverage monitoring.
- **Weakness:** it needs peers. A category with 5 merchants in a tier has a noisy band. When peers are *also* fraudulent (a whole cohort of fronts) the band would absorb the fraud; that is why composition tests are never discounted.

## 7. Fusion (`models/fusion.py`)

- **Method:** 30 component scores → LightGBM stacker, depth 2, 60 trees, every input **monotone-increasing** (more anomalous can only raise risk), L2 = 5, 50% column sampling. Trained on a simulated analyst-labelled subset (80 merchants, labelled by *case*: when a fraud is strongly linked, its ring is labelled with it). Calibrated with sigmoid (Platt) scaling on out-of-fold raw scores, then shifted from the sample's 26% fraud rate to the 5% population prior with Bayes' rule. SHAP (TreeExplainer) gives the top drivers per merchant in plain English.
- **Production:** thousands of analyst labels per month, isotonic calibration once there are > 1,000, periodic re-calibration against confirmed cases, champion/challenger.
- **Weakness:** 80 labels. The bootstrap interval on PR-AUC is 0.93–0.99 and scores cluster (many frauds share the score 82) because a depth-2 tree ensemble has few distinct leaves. More labels → smoother scores.

## 8. Action ladder and Explain step (`decision/`)

Net benefit of rung *r* = P × harm × prevented_r − (1 − P) × disruption cost × disruption_r. Choose the rung with the highest net benefit; "Monitor" is 0. With defaults (harm ₹5 lakh, disruption ₹6 lakh): Soft step-up from P ≥ 4.6%, settlement hold ≥ 40%, limit reduction ≥ 61.5%, suspend ≥ 74%. Analyst capacity caps the review queue by net benefit.

The merchant's claimed reason is tested: "festival" needs peers to have spiked (≥ 1.3×), volume inside the band, and no composition shift. The result is recorded in the report either way.

## 9. Evaluation (`eval/`)

Baselines: static rules (volume ≥ 3× own history OR night share ≥ 20%), the same rules with the innocence gate, and an Isolation Forest on raw features. All metrics on the 720 merchants outside the labelled set.

| | PR-AUC | Recall @ 2% budget | Festival-surge false alarms (own threshold) |
|---|---|---|---|
| Static rules | 0.20 | 13% | 79% |
| Rules + innocence gate | 0.26 | 13% | 40% |
| Isolation Forest | 0.78 | 47% | 0% |
| MerchantDNA | **0.97** | 47% | **0%** |

Slow drift: detected a median 49 days before the rules and 14 days before Isolation Forest (9/9). Adaptive mimic: 4 of 5 reach MEDIUM (baselines: 0 of 5). The review budget (2% = 14 merchants) is the binding constraint on recall for both good methods; at MerchantDNA's own MEDIUM threshold recall is 97% at 67% precision.
