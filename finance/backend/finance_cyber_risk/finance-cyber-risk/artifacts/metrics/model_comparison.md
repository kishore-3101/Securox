# Fraud Detection Model Comparison

All metrics below are computed on the TEST split (never touched during threshold or imbalance-strategy tuning). Thresholds were selected on the VALIDATION split only.


## indian_banking

| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC | FN | FP |
|---|---|---|---|---|---|---|---|---|
| Isolation Forest | -0.0247 | 0.0127 | 0.0679 | 0.0214 | 0.5390831600097798 | 0.010396719159625605 | 673 | 3818 |
| XGBoost | 0.0293 | 0.0619 | 0.0831 | 0.0710 | 0.5240766180773582 | 0.015867476658499892 | 662 | 909 |

**False-negative tradeoff (indian_banking, XGBoost):**

- Chosen threshold 0.0293: recall=0.0831, precision=0.0619, FN=662, FP=909
- Recall-biased threshold (max F2 on val) 0.0226: recall=0.0886, precision=0.0533, FN=658, FP=1137
- The 'recall_biased_threshold_from_val_f2' row uses the threshold that maximized F2 (recall weighted 2x precision) on validation — a meaningful alternative operating point, not the degenerate 'threshold=0' point that maximizing raw recall alone would always select. It catches more fraud (fewer false negatives) at the cost of more false positives (more legitimate transactions flagged for review). In a cybersecurity/fraud context a missed fraud (false negative) is usually costlier than an analyst review of a false positive, so this tradeoff is reported explicitly rather than silently optimizing for F1 alone.


## ulb

| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC | FN | FP |
|---|---|---|---|---|---|---|---|---|
| Isolation Forest | 0.0669 | 0.0611 | 0.5385 | 0.1098 | 0.9383366984550486 | 0.03943506949320338 | 24 | 430 |
| XGBoost | 0.5043 | 0.8444 | 0.7308 | 0.7835 | 0.9803807394854969 | 0.7580661360494774 | 14 | 7 |

**False-negative tradeoff (ulb, XGBoost):**

- Chosen threshold 0.5043: recall=0.7308, precision=0.8444, FN=14, FP=7
- Recall-biased threshold (max F2 on val) 0.2282: recall=0.7500, precision=0.7358, FN=13, FP=14
- The 'recall_biased_threshold_from_val_f2' row uses the threshold that maximized F2 (recall weighted 2x precision) on validation — a meaningful alternative operating point, not the degenerate 'threshold=0' point that maximizing raw recall alone would always select. It catches more fraud (fewer false negatives) at the cost of more false positives (more legitimate transactions flagged for review). In a cybersecurity/fraud context a missed fraud (false negative) is usually costlier than an analyst review of a false positive, so this tradeoff is reported explicitly rather than silently optimizing for F1 alone.
