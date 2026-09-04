"""
FRAUD DETECTION + MODEL EVALUATION pipeline.

Trains, on top of the already-processed/validated data layer:
  - Indian Banking: Isolation Forest (unsupervised) + XGBoost (supervised)
  - ULB:            Isolation Forest (unsupervised) + XGBoost (supervised)

All imbalance-handling and threshold decisions are made on VALIDATION data
only; the TEST split is touched exactly once per model, at final evaluation.
No SMOTE is applied anywhere. is_fraud/Class is never passed to .fit() for
either Isolation Forest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from src.config.paths import (
    ARTIFACTS_DIR,
    FEATURE_DICTIONARY_PATH,
    INDIAN_BANKING_PROCESSED_DIR,
    METRICS_DIR,
    RANDOM_SEED,
    ULB_PROCESSED_DIR,
    ensure_dirs,
)
from src.data.processed_loader import load_processed_dataset
from src.evaluation.metrics import evaluate_at_threshold
from src.explainability.shap_explainer import FraudExplainer
from src.models.anomaly.isolation_forest_model import (
    anomaly_scores,
    fit_and_tune_isolation_forest,
    predict as if_predict,
)
from src.models.fraud.xgboost_model import (
    fit_and_tune_xgboost,
    predict as xgb_predict,
    predict_proba,
)
from src.utils.io import load_object, save_json, save_object
from src.utils.seeding import set_global_seed

MODELS_DIR = ARTIFACTS_DIR / "models"


def _load_dataset(processed_dir, preprocessor_path, target_col):
    fitted_preproc = load_object(preprocessor_path)
    return load_processed_dataset(processed_dir, target_col, fitted_preproc.output_feature_names)


def run_isolation_forest(dataset_name: str, dataset):
    print(f"\n--- {dataset_name}: Isolation Forest (unsupervised) ---")
    fitted_if = fit_and_tune_isolation_forest(
        dataset.train.X, dataset.val.X, dataset.val.y, dataset.feature_names
    )

    results = {}
    for split_name, split in [("train", dataset.train), ("val", dataset.val), ("test", dataset.test)]:
        scores = anomaly_scores(fitted_if.model, split.X)
        report = evaluate_at_threshold(split.y, scores, fitted_if.threshold)
        results[split_name] = report.to_dict()
        print(f"  [{split_name}] precision={report.precision:.4f} recall={report.recall:.4f} "
              f"f1={report.f1:.4f} pr_auc={report.pr_auc} roc_auc={report.roc_auc}")

    save_object(fitted_if, MODELS_DIR / f"{dataset_name}_isolation_forest.joblib")
    return fitted_if, results


def run_xgboost(dataset_name: str, dataset):
    print(f"\n--- {dataset_name}: XGBoost (supervised) ---")
    fitted_xgb = fit_and_tune_xgboost(
        dataset.train.X, dataset.train.y, dataset.val.X, dataset.val.y, dataset.feature_names
    )
    print("  scale_pos_weight candidates (validation PR-AUC):")
    for c in fitted_xgb.scale_pos_weight_search:
        print(f"    {c['name']}: pr_auc={c['val_pr_auc']}, roc_auc={c['val_roc_auc']}")
    print(f"  selected scale_pos_weight={fitted_xgb.scale_pos_weight_used}, "
          f"threshold={fitted_xgb.threshold:.4f} (optimized for {fitted_xgb.threshold_metric} on val)")

    results = {}
    for split_name, split in [("train", dataset.train), ("val", dataset.val), ("test", dataset.test)]:
        prob = predict_proba(fitted_xgb, split.X)
        report = evaluate_at_threshold(split.y, prob, fitted_xgb.threshold)
        results[split_name] = report.to_dict()
        print(f"  [{split_name}] precision={report.precision:.4f} recall={report.recall:.4f} "
              f"f1={report.f1:.4f} pr_auc={report.pr_auc} roc_auc={report.roc_auc} "
              f"FN={report.fn} FP={report.fp}")

    # False-negative tradeoff analysis: what happens at a recall-biased
    # alternative threshold (lower threshold -> catch more fraud, more FPs)?
    val_prob = predict_proba(fitted_xgb, dataset.val.X)
    from src.evaluation.metrics import search_best_threshold
    # F2 weights recall higher than precision without collapsing to the
    # trivial "threshold=0 -> recall=1.0" degenerate point that maximizing
    # raw recall alone would always pick.
    recall_biased_threshold, recall_biased_report, _ = search_best_threshold(
        dataset.val.y, val_prob, metric="f2"
    )
    test_prob = predict_proba(fitted_xgb, dataset.test.X)
    recall_biased_test_report = evaluate_at_threshold(dataset.test.y, test_prob, recall_biased_threshold)

    fn_tradeoff = {
        "chosen_threshold": {
            "threshold": fitted_xgb.threshold,
            "test_recall": results["test"]["recall"],
            "test_precision": results["test"]["precision"],
            "test_fn": results["test"]["confusion_matrix"]["fn"],
            "test_fp": results["test"]["confusion_matrix"]["fp"],
        },
        "recall_biased_threshold_from_val_f2": {
            "threshold": recall_biased_threshold,
            "test_recall": recall_biased_test_report.recall,
            "test_precision": recall_biased_test_report.precision,
            "test_fn": recall_biased_test_report.fn,
            "test_fp": recall_biased_test_report.fp,
        },
        "note": "The 'recall_biased_threshold_from_val_f2' row uses the "
        "threshold that maximized F2 (recall weighted 2x precision) on "
        "validation — a meaningful alternative operating point, not the "
        "degenerate 'threshold=0' point that maximizing raw recall alone "
        "would always select. It catches more fraud (fewer false negatives) "
        "at the cost of more false positives (more legitimate transactions "
        "flagged for review). In a cybersecurity/fraud context a missed "
        "fraud (false negative) is usually costlier than an analyst review "
        "of a false positive, so this tradeoff is reported explicitly rather "
        "than silently optimizing for F1 alone.",
    }

    save_object(fitted_xgb, MODELS_DIR / f"{dataset_name}_xgboost.joblib")
    return fitted_xgb, results, fn_tradeoff


def run_shap_demo(dataset_name: str, fitted_xgb, dataset, n_examples: int = 3):
    print(f"\n--- {dataset_name}: SHAP explainability demo (test set) ---")
    explainer = FraudExplainer(
        fitted_xgb.model,
        fitted_xgb.feature_names,
        feature_dictionary_path=FEATURE_DICTIONARY_PATH,
        dataset_key=dataset_name,
    )
    prob = predict_proba(fitted_xgb, dataset.test.X)
    pred = (prob >= fitted_xgb.threshold).astype(int)

    # pick a true positive, a false negative (if any), and a false positive (if any)
    y = dataset.test.y
    idx_tp = np.where((pred == 1) & (y == 1))[0]
    idx_fn = np.where((pred == 0) & (y == 1))[0]
    idx_fp = np.where((pred == 1) & (y == 0))[0]

    examples = {}
    for label, idx_array in [("true_positive_example", idx_tp), ("false_negative_example", idx_fn), ("false_positive_example", idx_fp)]:
        if len(idx_array) == 0:
            examples[label] = None
            continue
        i = int(idx_array[0])
        explanation = explainer.explain(dataset.test.X[i], fitted_xgb.threshold, top_n=5)
        examples[label] = explanation.to_dict()
        print(f"  {label} (row {i}): prob={explanation.fraud_probability:.3f} "
              f"predicted_class={explanation.predicted_class}")

    # global top features via mean |SHAP| over a sample of test rows
    sample_n = min(500, dataset.test.X.shape[0])
    sample_idx = np.random.default_rng(RANDOM_SEED).choice(dataset.test.X.shape[0], sample_n, replace=False)
    shap_vals = explainer.explainer.shap_values(dataset.test.X[sample_idx])
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[-1]
    mean_abs_shap = np.abs(shap_vals).mean(axis=0)
    top_global_idx = np.argsort(-mean_abs_shap)[:10]
    global_top_features = [
        {"feature": fitted_xgb.feature_names[i], "mean_abs_shap": float(mean_abs_shap[i])}
        for i in top_global_idx
    ]
    print("  global top features by mean |SHAP|:")
    for f in global_top_features:
        print(f"    {f['feature']}: {f['mean_abs_shap']:.5f}")

    return {"examples": examples, "global_top_features": global_top_features}


def build_comparison_markdown(all_results: dict) -> str:
    lines = ["# Fraud Detection Model Comparison\n"]
    lines.append(
        "All metrics below are computed on the TEST split (never touched "
        "during threshold or imbalance-strategy tuning). Thresholds were "
        "selected on the VALIDATION split only.\n"
    )
    for dataset_name in ["indian_banking", "ulb"]:
        lines.append(f"\n## {dataset_name}\n")
        lines.append("| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC | FN | FP |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for model_key, model_label in [("isolation_forest", "Isolation Forest"), ("xgboost", "XGBoost")]:
            r = all_results[dataset_name][model_key]["test_metrics"]
            th = all_results[dataset_name][model_key]["threshold"]
            lines.append(
                f"| {model_label} | {th:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | "
                f"{r['f1']:.4f} | {r['roc_auc']} | {r['pr_auc']} | "
                f"{r['confusion_matrix']['fn']} | {r['confusion_matrix']['fp']} |"
            )
        if "false_negative_tradeoff" in all_results[dataset_name]["xgboost"]:
            fn = all_results[dataset_name]["xgboost"]["false_negative_tradeoff"]
            lines.append(f"\n**False-negative tradeoff ({dataset_name}, XGBoost):**\n")
            lines.append(
                f"- Chosen threshold {fn['chosen_threshold']['threshold']:.4f}: "
                f"recall={fn['chosen_threshold']['test_recall']:.4f}, "
                f"precision={fn['chosen_threshold']['test_precision']:.4f}, "
                f"FN={fn['chosen_threshold']['test_fn']}, FP={fn['chosen_threshold']['test_fp']}"
            )
            lines.append(
                f"- Recall-biased threshold (max F2 on val) {fn['recall_biased_threshold_from_val_f2']['threshold']:.4f}: "
                f"recall={fn['recall_biased_threshold_from_val_f2']['test_recall']:.4f}, "
                f"precision={fn['recall_biased_threshold_from_val_f2']['test_precision']:.4f}, "
                f"FN={fn['recall_biased_threshold_from_val_f2']['test_fn']}, FP={fn['recall_biased_threshold_from_val_f2']['test_fp']}"
            )
            lines.append(f"- {fn['note']}\n")

    return "\n".join(lines)


def main():
    set_global_seed(RANDOM_SEED)
    ensure_dirs()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    ib_dataset = _load_dataset(
        INDIAN_BANKING_PROCESSED_DIR,
        ARTIFACTS_DIR / "preprocessors" / "indian_banking_preprocessor.joblib",
        "is_fraud",
    )
    ulb_dataset = _load_dataset(
        ULB_PROCESSED_DIR,
        ARTIFACTS_DIR / "preprocessors" / "ulb_preprocessor.joblib",
        "Class",
    )

    all_results = {}

    for dataset_name, dataset in [("indian_banking", ib_dataset), ("ulb", ulb_dataset)]:
        fitted_if, if_results = run_isolation_forest(dataset_name, dataset)
        fitted_xgb, xgb_results, fn_tradeoff = run_xgboost(dataset_name, dataset)
        shap_demo = run_shap_demo(dataset_name, fitted_xgb, dataset)

        all_results[dataset_name] = {
            "isolation_forest": {
                "threshold": fitted_if.threshold,
                "threshold_metric": fitted_if.threshold_metric,
                "test_metrics": if_results["test"],
                "val_metrics": if_results["val"],
                "train_metrics": if_results["train"],
            },
            "xgboost": {
                "threshold": fitted_xgb.threshold,
                "threshold_metric": fitted_xgb.threshold_metric,
                "scale_pos_weight_used": fitted_xgb.scale_pos_weight_used,
                "scale_pos_weight_search": fitted_xgb.scale_pos_weight_search,
                "test_metrics": xgb_results["test"],
                "val_metrics": xgb_results["val"],
                "train_metrics": xgb_results["train"],
                "false_negative_tradeoff": fn_tradeoff,
            },
            "shap": shap_demo,
        }

    save_json(all_results, METRICS_DIR / "model_results.json")
    md = build_comparison_markdown(all_results)
    (METRICS_DIR / "model_comparison.md").write_text(md)

    print("\n=== FRAUD MODEL TRAINING + EVALUATION COMPLETE ===")
    print(f"Models -> {MODELS_DIR}")
    print(f"Metrics -> {METRICS_DIR / 'model_results.json'}")
    print(f"Comparison report -> {METRICS_DIR / 'model_comparison.md'}")
    return all_results


if __name__ == "__main__":
    main()
