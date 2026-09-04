# AML Detection Model Comparison

Target: `is_sar` (accounts.csv IS_SAR, account-level). Features: leakage-safe structural graph/account features only (see artifacts/metrics/feature_dictionary.json -> amlsim). Metrics below are computed on the TEST split; the classification threshold was selected on the VALIDATION split only, for each model independently.

| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC | FN | FP |
|---|---|---|---|---|---|---|---|---|
| Logistic Regression (baseline) | 0.5462 | 0.0526 | 0.0909 | 0.0667 | 0.6082564778216952 | 0.07549617874299039 | 10 | 18 |
| XGBoost | 0.5648 | 0.1176 | 0.1818 | 0.1429 | 0.4997804128238911 | 0.09648242031479175 | 9 | 15 |

**Selected model: logistic_regression**

logistic_regression selected based on validation PR-AUC (0.1095938650372778 vs 0.054938920953120876 for xgboost); this is the appropriate primary metric given how imbalanced the SAR label is.

**Note on sample size**: the AMLSim account-level dataset used here has only 1,446 accounts total (~1,012 train / 216 val / 218 test) with 73 SAR-labeled accounts overall — test-set metrics on this few dozen positive examples should be read as indicative, not as a stable production estimate.
