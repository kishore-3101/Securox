"""
AML DETECTION model training + evaluation pipeline.

Uses the already-processed AMLSim account-level features/splits produced by
scripts/run_data_pipeline.py (data/processed/amlsim/, fitted preprocessor in
artifacts/preprocessors/amlsim_preprocessor.joblib). Trains a Logistic
Regression baseline and an XGBoost model, evaluates both, and selects the
better one based on validation/test evidence — no metric is fabricated.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.paths import (
    AMLSIM_PROCESSED_DIR,
    ARTIFACTS_DIR,
    METRICS_DIR,
    PREPROCESSORS_DIR,
    RANDOM_SEED,
    ensure_dirs,
)
from src.data.processed_loader import load_processed_dataset
from src.evaluation.metrics import evaluate_at_threshold
from src.models.aml.aml_classifier import fit_and_tune_aml_model, predict_proba
from src.utils.io import load_object, save_json, save_object
from src.utils.seeding import set_global_seed

AML_MODELS_DIR = ARTIFACTS_DIR / "models" / "aml"


def run_model(model_name: str, dataset):
    print(f"\n--- AMLSim: {model_name} ---")
    fitted = fit_and_tune_aml_model(
        model_name, dataset.train.X, dataset.train.y, dataset.val.X, dataset.val.y, dataset.feature_names
    )
    print(f"  threshold={fitted.threshold:.4f} (optimized for {fitted.threshold_metric} on val)")

    results = {}
    for split_name, split in [("train", dataset.train), ("val", dataset.val), ("test", dataset.test)]:
        prob = predict_proba(fitted, split.X)
        report = evaluate_at_threshold(split.y, prob, fitted.threshold)
        results[split_name] = report.to_dict()
        print(
            f"  [{split_name}] precision={report.precision:.4f} recall={report.recall:.4f} "
            f"f1={report.f1:.4f} pr_auc={report.pr_auc} roc_auc={report.roc_auc} "
            f"FN={report.fn} FP={report.fp}"
        )

    save_object(fitted, AML_MODELS_DIR / f"aml_{model_name}.joblib")
    return fitted, results


def build_comparison_markdown(results: dict, best_model_name: str, best_model_reason: str) -> str:
    lines = ["# AML Detection Model Comparison\n"]
    lines.append(
        "Target: `is_sar` (accounts.csv IS_SAR, account-level). Features: "
        "leakage-safe structural graph/account features only (see "
        "artifacts/metrics/feature_dictionary.json -> amlsim). Metrics below "
        "are computed on the TEST split; the classification threshold was "
        "selected on the VALIDATION split only, for each model "
        "independently.\n"
    )
    lines.append("| Model | Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC | FN | FP |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for model_name, label in [("logistic_regression", "Logistic Regression (baseline)"), ("xgboost", "XGBoost")]:
        r = results[model_name]["test_metrics"]
        th = results[model_name]["threshold"]
        lines.append(
            f"| {label} | {th:.4f} | {r['precision']:.4f} | {r['recall']:.4f} | "
            f"{r['f1']:.4f} | {r['roc_auc']} | {r['pr_auc']} | "
            f"{r['confusion_matrix']['fn']} | {r['confusion_matrix']['fp']} |"
        )
    lines.append(f"\n**Selected model: {best_model_name}**\n")
    lines.append(best_model_reason)
    lines.append(
        "\n**Note on sample size**: the AMLSim account-level dataset used "
        "here has only 1,446 accounts total (~1,012 train / 216 val / 218 "
        "test) with 73 SAR-labeled accounts overall — test-set metrics on "
        "this few dozen positive examples should be read as indicative, not "
        "as a stable production estimate.\n"
    )
    return "\n".join(lines)


def main():
    set_global_seed(RANDOM_SEED)
    ensure_dirs()
    AML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    fitted_preproc = load_object(PREPROCESSORS_DIR / "amlsim_preprocessor.joblib")
    dataset = load_processed_dataset(
        AMLSIM_PROCESSED_DIR, "is_sar", fitted_preproc.output_feature_names
    )
    print(f"AMLSim dataset: train={len(dataset.train.y)} val={len(dataset.val.y)} "
          f"test={len(dataset.test.y)}, features={dataset.feature_names}")

    results = {}
    fitted_models = {}
    for model_name in ["logistic_regression", "xgboost"]:
        fitted, model_results = run_model(model_name, dataset)
        fitted_models[model_name] = fitted
        results[model_name] = {
            "threshold": fitted.threshold,
            "threshold_metric": fitted.threshold_metric,
            "test_metrics": model_results["test"],
            "val_metrics": model_results["val"],
            "train_metrics": model_results["train"],
        }

    # Select the better model based on validation PR-AUC first (most
    # appropriate for this level of imbalance), tie-broken by test PR-AUC.
    def val_pr_auc(name):
        v = results[name]["val_metrics"]["pr_auc"]
        return v if v is not None else -1

    best_model_name = max(results, key=val_pr_auc)
    other_model_name = "xgboost" if best_model_name == "logistic_regression" else "logistic_regression"
    best_val = results[best_model_name]["val_metrics"]["pr_auc"]
    other_val = results[other_model_name]["val_metrics"]["pr_auc"]
    best_model_reason = (
        f"{best_model_name} selected based on validation PR-AUC "
        f"({best_val} vs {other_val} for {other_model_name}); this is the "
        "appropriate primary metric given how imbalanced the SAR label is."
    )
    print(f"\nBest AML model: {best_model_name} — {best_model_reason}")

    save_json(results, METRICS_DIR / "aml_results.json")
    md = build_comparison_markdown(results, best_model_name, best_model_reason)
    (METRICS_DIR / "aml_comparison.md").write_text(md)

    print("\n=== AML MODEL TRAINING + EVALUATION COMPLETE ===")
    print(f"Models -> {AML_MODELS_DIR}")
    print(f"Metrics -> {METRICS_DIR / 'aml_results.json'}")
    print(f"Comparison report -> {METRICS_DIR / 'aml_comparison.md'}")
    return results


if __name__ == "__main__":
    main()
