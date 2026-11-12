# How to read this guide

This document walks through the MerchantDNA prototype file by file. For the core pipeline (simulator, features, models, Innocence Engine, fusion, decision, evaluation) every line is covered. For configuration, the Makefile, utilities, tests and the Streamlit pages the code is explained block by block.

Each chapter starts with what the file is for, then shows the code in numbered blocks with the explanation under each block. The builder (`tools/build_code_guide.py`) checks that every annotation matches the file it describes, so this guide is always in step with the code.

## The problem in one paragraph

A merchant signs up with a payment aggregator as a bakery, with genuine documents, then uses the account to collect money for illegal betting. Each payment looks normal. At the same time, honest bakeries have Diwali spikes that look alarming to simple rules. MerchantDNA learns what a legitimate business of each category *does* — when it trades, what amounts it takes, who pays it, how fast it cashes out — and scores **purpose drift**: behaviour inconsistent with the declared category. Before flagging anyone it tries to explain the deviation legitimately (did peers spike too? is the business mix unchanged?). It then recommends a proportionate action. Signals, not proof; a human decides.

## Architecture

```
config.yaml ──► merchantdna/sim/        synthetic merchants, transactions, settlements, calendar
                       │
                merchantdna/features/   7d / 30d windows, payer-side features, peer z-scores
                       │
       ┌───────────────┼──────────────────┐
  CLAIMED PROFILE   BEHAVIOUR          NETWORK
  website.py        verifier.py        network.py
                    dna_autoencoder.py
       └───────────────┼──────────────────┘
                innocence.py            expected-volume band + composition tests
                       │
                fusion.py               monotone stacker, calibration, SHAP
                       │
                decision/ladder.py      expected-cost action rung
                decision/explain_step.py merchant's claimed reason, tested
                       │
                eval/                   baselines, metrics, ablations
                app/                    Streamlit dashboard (reads artifacts only)
```

The glue is `models/scoring.py` (turns features into component scores) and `models/train.py` (fits everything in order and writes the artefacts).

## Reading order

1. `config.yaml` — every number the code uses.
2. `sim/` — calendar, profiles, archetypes, heroes, merchants, transactions, run.
3. `features/` — windows, then each feature family, then build.
4. `models/` — website, verifier, dna_autoencoder, network, innocence, fusion, scoring, rescore, train.
5. `decision/` — ladder, explain_step, report.
6. `eval/` — baselines, metrics, ablation, run.
7. `app/`, `tests/`, `utils/`, `Makefile`.

## Glossary of methods used

- **Poisson / gamma noise.** Daily transaction counts are drawn from a Poisson distribution whose rate is itself jittered by a gamma factor (an "overdispersed" Poisson), which gives realistic day-to-day variation.
- **Lognormal.** Basket amounts are drawn as exp(normal): always positive, skewed right, like real ticket sizes.
- **splitmix64.** A fast bit-mixing hash used to pseudonymise payer ids so raw ids never leave the simulator.
- **Fano factor.** Variance divided by mean of counts. A Poisson stream has Fano = 1 whatever its volume; bursts push it above 1. Used as a volume-independent burstiness measure.
- **HHI (Herfindahl–Hirschman index).** Sum of squared shares. High when a few payers account for most payments.
- **Shannon entropy.** Measures how spread out a distribution is (amount bins, payer cities).
- **Robust z-score.** (x − median) / (1.4826 × median absolute deviation). Like a z-score but not thrown off by outliers; the 1.4826 scales MAD to a standard deviation for normal data.
- **TF-IDF + logistic regression.** Word counts weighted by rarity, fed to a linear classifier. The standard baseline for text classification.
- **Out-of-fold / cross-fitting.** Split merchants into K folds; score each fold with a model trained on the other K−1. No merchant is scored by a model that saw it.
- **LightGBM.** Gradient-boosted decision trees. Fast, handles mixed features, supports multiclass, quantile objectives and monotone constraints.
- **Monotone constraint.** Forces a tree model so that increasing an input can only increase the output. Here: "more anomalous" can only raise risk, never lower it.
- **Autoencoder / bottleneck.** A neural network trained to reproduce its input through a narrow middle layer. The middle layer (12 numbers) is a compressed "DNA" of the behaviour.
- **UMAP.** Projects high-dimensional points to 2-D while keeping neighbours together. Used only for the map visual.
- **IDF rarity weight.** log(N / holders): sharing something rare (a device used by 2 merchants out of 800) is strong evidence; sharing something common is weak.
- **Louvain communities.** A graph algorithm that groups nodes that are densely connected to each other.
- **Jaccard similarity.** |A ∩ B| / |A ∪ B|; used for payer overlap between two merchants.
- **Quantile regression.** Predicts the 5th / 50th / 95th percentile instead of the mean, giving a band rather than a point.
- **Split conformal prediction.** Hold out a calibration set, measure how far outside the predicted band the truth falls, and widen the band by that quantile so the band has the promised coverage.
- **Jensen–Shannon distance.** A symmetric, bounded (0–1) measure of how different two probability distributions are. Used for hourly profile, amount mix and payer geography.
- **Platt (sigmoid) calibration.** Fit a logistic curve from raw model scores to observed outcome rates so the output is a true probability. Preferred over isotonic regression when there are few labels.
- **Prior correction.** The labelled sample has 26% fraud; the population has ~5%. Bayes' rule shifts the calibrated odds accordingly.
- **SHAP.** Attributes a model's output to each input (Shapley values). Used to list the top drivers of each score in plain English.
- **Expected cost decision.** Choose the action with the highest P × benefit − (1 − P) × cost. The costs are policy parameters.
- **PR-AUC (average precision).** Area under the precision–recall curve; the right metric when positives are rare.
- **Isolation Forest.** An unsupervised anomaly detector that isolates points with random splits; outliers are isolated in fewer splits.
