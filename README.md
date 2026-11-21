# MerchantDNA

**Learns what a legitimate business of each category looks like from behaviour, not paperwork. Tests every deviation against legitimate explanations before flagging anyone, and responds proportionately.**

Prototype for the "Follow the Money" Innovation Challenge (CSITM IIM Bangalore × PayU), problem statement *The Bakery That Takes Bets*. All data is synthetic.

## One-command setup

```bash
git clone <repo> merchantdna && cd merchantdna
make setup        # Python 3.11 venv via uv + requirements
make all          # data -> features -> train -> eval   (~3 min on a laptop, CPU only)
make app          # Streamlit dashboard on http://localhost:8501
```

`make demo` runs `all` then `app`. `make test` runs the test suite (needs `make all` first for the hero and page tests). `make guide` rebuilds the code-guide PDF. `make data SMALL=1` uses 120 merchants × 60 days for development.

Requires `uv` (https://docs.astral.sh/uv/) — or create any Python 3.11 venv at `.venv` and `pip install -r requirements.txt`.

## What you get

| Step | Command | Output |
|---|---|---|
| Simulator | `make data` | `data/*.parquet`: 800 merchants, 120 days, ~4.7M transactions, 6 categories, 5 fraud archetypes, 3 fixed demo merchants, sanity plots in `reports/sim/` |
| Features | `make features` | `artifacts/features_*.parquet`: 117 features per merchant per window (7d/30d, own-history and peer-relative) |
| Models | `make train` | `artifacts/`: website classifier, behavioural verifier, DNA autoencoder + UMAP, identity and payer graphs, Innocence Engine, calibrated fusion, SHAP drivers, action ladder, evidence per merchant |
| Evaluation | `make eval` | `reports/metrics.json`, PR curves, ablations, stress test, lead time |
| Dashboard | `make app` | Home + 3 pages: Merchant Story (score, evidence, Innocence check, connections, explain step, report + draft STR), DNA Map, Proof & Try It |

## Headline results (720 held-out synthetic merchants)

| | PR-AUC | Festival-surge false alarms |
|---|---|---|
| Static rules | 0.20 | 79% |
| Isolation Forest | 0.78 | 0% |
| **MerchantDNA** | **0.97** | **0%** |

Slow drift caught a median 49 days before rules. 4 of 5 adaptive mimics still flagged. The three demo merchants reach LOW / HIGH / MEDIUM through the models alone (`tests/test_heroes.py` proves it; nothing is hard-coded).

## Repository

```
config.yaml            every tunable number
merchantdna/sim        synthetic data        merchantdna/models    all models + scoring
merchantdna/features   feature store         merchantdna/decision  action ladder, Explain step, report
merchantdna/eval       baselines, metrics    app/                  Streamlit pages
docs/                  plan, decisions, architecture, limitations, demo script, Q&A, code guide PDF
tests/                 simulator, leakage, hero tiers, app pages
```

Read `docs/decisions.md` for every change we made after seeing a result, and `docs/limitations.md` before quoting a number.
