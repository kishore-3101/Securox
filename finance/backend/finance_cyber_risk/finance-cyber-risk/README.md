# Finance Cyber-Risk Subsystem
### AI-Driven Cyber Risk Detection for Smart City Digital Infrastructure — FINANCE module

This module ingests financial transaction data and produces fraud / anomaly /
AML risk signals for the smart-city risk engine. It is designed to be one
subsystem among several (finance, traffic, energy, water, ...) sharing a
common project shape.

**Status: scaffolding + data validation only. No models have been trained yet.**

---

## 1. Datasets (exactly as found — nothing invented)

### 1.1 Indian Banking Transactions
`data/raw/indian_banking/indian_banking_transactions.csv`

- **Shape:** 550,000 rows × 20 columns
- **Columns:** `transaction_id, customer_id, transaction_date, transaction_time,
  account_type, transaction_type, transaction_amount, transaction_direction,
  account_balance, merchant_category, state, credit_score, has_loan,
  loan_type, emi_amount, transaction_status, channel, kyc_status, is_fraud,
  transaction_hour`
- **Target column:** `is_fraud` — value counts: `0 → 545,127`, `1 → 4,873`
  (highly imbalanced, ~0.89% positive class)
- **Nulls:** only `loan_type` has nulls (377,134 / 550,000) — this is
  structural, not missing data: it's `NaN` whenever `has_loan == 0`.
- **Date range:** `2019-01-01` to `2024-01-01`
- **Duplicates:** 0 duplicate `transaction_id`
- Ships with a companion starter EDA notebook:
  `notebooks/indian-banking-transactions-starter-eda.ipynb` (Kaggle-style
  reference notebook, not part of the production pipeline).

### 1.2 ULB Credit Card Fraud
`data/raw/ulb/creditcard.csv`

- **Shape:** 284,807 rows × 31 columns
- **Columns:** `Time, V1..V28, Amount, Class`
- **Target column:** `Class` — value counts: `0 → 284,315`, `1 → 492`
  (~0.17% positive class)
- **Nulls:** none
- `V1`–`V28` are PCA-transformed features from the original dataset
  publisher. **No semantic meaning is assumed for them anywhere in this
  codebase** — they are used purely as opaque numeric features.

### 1.3 IBM AMLSim
`data/raw/amlsim/AMLSim-master.zip` (kept as an untouched archive)

The zip contains the full AMLSim repository. Two things are inside it worth
calling out explicitly:

1. **Raw simulator output** under `tmp/1K/`:
   - `accounts.csv` (1,446 rows) — columns: `ACCOUNT_ID, CUSTOMER_ID,
     INIT_BALANCE, COUNTRY, ACCOUNT_TYPE, IS_SAR, BANK_ID`
   - `alert_members.csv` (73 rows) — columns: `alertID, reason, accountID,
     isMain, isSAR, modelID, minAmount, maxAmount, startStep, endStep,
     scheduleID, bankID`
   - `normal_models.csv` (16,014 rows) — columns: `modelID, type, accountID,
     isMain, isSAR, scheduleID`
   - `transactions.csv` (7,977 rows) — columns: **`id, src, dst, ttype`
     only**. This is the *graph-generation stage* output (account-to-account
     edges), **it does not contain amount, timestamp, or step columns**.
     The full simulated transaction log with amounts/timestamps is produced
     by AMLSim's Java simulator, which has not been run in this workspace —
     we only have this Python-graph-generator artifact.

2. **A pre-existing `aml_detection/` sub-project already bundled inside the
   zip**, with its own feature engineering, trained models, and metrics
   already computed by someone else in a prior session:
   - `aml_detection/data/processed/full_dataset.csv`,
     `aml_detection/data/features/account_features.csv` /
     `account_labels.csv`
   - Trained model files: `GradientBoosting.pkl`, `LogisticRegression.pkl`,
     `RandomForest.pkl`
   - `aml_detection/outputs/metrics/model_metrics.csv`,
     `feature_importance.csv`, `predictions/suspicious_accounts.csv`,
     `reports/aml_detection_report.html`

   **These are treated as reference material only — not as this project's
   ground truth, not retrained, and not silently reused.** Any metrics
   reported by our own pipeline later will come from code in this repo, run
   by us, and nothing will be copied from that bundled report.

   The zip also bundles a full Python virtualenv
   (`AMLSim-master/amlsim-env/...`) which is not part of the dataset and is
   ignored by our tooling.

---

## 2. Validation

Run:

```bash
python scripts/validate_datasets.py
```

This performs a read-only pass over all three raw sources: shape, dtypes,
null counts, target balance, and (for the AMLSim zip) an inventory of every
CSV found, without extracting or modifying anything on disk. Re-run this any
time a raw file changes.

---

## 3. Project layout

```
finance-cyber-risk/
├── data/
│   ├── raw/            # immutable, exactly as delivered — never edited in place
│   │   ├── indian_banking/
│   │   ├── ulb/
│   │   └── amlsim/
│   ├── processed/      # versioned, pipeline-generated feature tables
│   └── external/       # any future third-party reference data
├── notebooks/          # exploratory notebooks (not production code)
├── src/
│   ├── config/         # dataclass/YAML configs, paths, seeds
│   ├── data/           # loaders + validators per dataset
│   ├── features/       # feature engineering, kept separate per dataset
│   ├── models/
│   │   ├── anomaly/    # unsupervised anomaly detection (e.g. Isolation Forest)
│   │   ├── fraud/      # supervised fraud classifiers (ULB, Indian banking)
│   │   ├── aml/        # AML / SAR classifiers (AMLSim)
│   │   ├── clustering/ # behavioral clustering
│   │   ├── graph/      # account-graph features / GNN-style signals
│   │   └── forecasting/# time-series volume/amount forecasting
│   ├── risk_engine/    # combines model outputs into a unified risk score
│   ├── explainability/ # SHAP / feature-attribution wrappers
│   ├── evaluation/     # metrics, calibration, threshold selection
│   ├── inference/       # inference-time pipeline (loads saved preprocessors)
│   └── utils/          # shared helpers (seeding, logging, I/O)
├── artifacts/
│   ├── models/         # serialized trained models
│   ├── preprocessors/  # serialized fitted scalers/encoders (fit on train only)
│   ├── explainers/     # serialized SHAP explainers etc.
│   └── metrics/        # evaluation reports per model/run
├── api/                # FastAPI service exposing risk-scoring endpoints
├── tests/
├── scripts/            # one-off / operational scripts (validation, ETL, training entrypoints)
├── requirements.txt
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

---

## 4. Engineering rules this project follows

- **No invented facts.** Column names, fraud rates, and metrics in this repo
  and its docs come only from what's actually in the data or from code that
  actually ran — never assumed.
- **No semantic guessing on anonymized features** (ULB `V1`-`V28` stay
  opaque).
- **Raw data is immutable.** Nothing in `data/raw/` is ever edited in place;
  all transformations write to `data/processed/`.
- **Leakage control.** Any scaler/encoder/imputer is fit on the training
  split only, then serialized to `artifacts/preprocessors/` and re-loaded
  (not refit) at inference time.
- **Chronological splitting** for time-based data (Indian banking
  transactions, AMLSim steps) instead of random shuffling.
- **No blind SMOTE on temporal transaction data** — imbalance handling is
  chosen per-dataset (e.g. class weights, cost-sensitive thresholds, or
  SMOTE only on non-temporal / already-static feature tables such as
  per-account graph features, applied after the chronological/graph split).
- **Reproducibility.** A single seed (`RANDOM_SEED` in `.env`) is threaded
  through every stochastic step.
- **Training vs inference separation.** `src/models/*` (training) and
  `src/inference/*` (serving) are separate modules; inference only ever
  loads artifacts, it never fits anything.
- **Modularity.** `src/` is organized so a second smart-city subsystem
  (e.g. traffic, energy) can be added as a sibling package without
  restructuring this one.

---

## 5. Next steps (not yet done)

1. Dataset-specific loaders in `src/data/` (one per source, matching the
   exact schemas above).
2. Feature engineering per dataset in `src/features/`.
3. Chronological train/val/test split design for the Indian banking and
   AMLSim data.
4. Baseline models per subsystem (`fraud`, `aml`, `anomaly`).
5. Risk engine that fuses per-model outputs into one score.
6. API + Docker wiring.
