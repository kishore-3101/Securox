"""
Runs the complete Core Cyber Risk Intelligence layer end-to-end on REAL
data already produced by prior stages:
  - Indian Banking: saved Isolation Forest + XGBoost models, test split
  - AMLSim: transaction graph + graph-risk scoring + AML models

Produces:
  - artifacts/config/risk_engine_weights.json
  - artifacts/metrics/propagation_example.json
  - artifacts/metrics/dbscan_incidents.json
  - artifacts/metrics/unified_risk_examples.json
  - artifacts/metrics/risk_engine_documentation.md

No model is retrained here — this stage only combines existing outputs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.config.paths import (
    ARTIFACTS_DIR,
    FEATURE_DICTIONARY_PATH,
    INDIAN_BANKING_PROCESSED_DIR,
    METRICS_DIR,
    PREPROCESSORS_DIR,
    RANDOM_SEED,
    ensure_dirs,
)
from src.data.amlsim_loader import load_amlsim
from src.data.indian_banking_loader import load_indian_banking
from src.data.processed_loader import load_processed_dataset
from src.explainability.full_explanation import build_full_explanation
from src.explainability.shap_explainer import FraudExplainer
from src.features.amlsim_features import engineer_amlsim_account_features
from src.models.aml.aml_classifier import predict_proba as aml_predict_proba
from src.models.anomaly.isolation_forest_model import anomaly_scores
from src.models.clustering.dbscan_incidents import DBSCANIncidentConfig, cluster_incidents
from src.models.fraud.xgboost_model import predict_proba as xgb_predict_proba
from src.models.graph.transaction_graph import load_graph
from src.risk_engine.cyber_var import CyberExposureConfig
from src.risk_engine.dynamic_risk import DEFAULT_WEIGHTS, RISK_LEVEL_THRESHOLDS
from src.risk_engine.graph_risk_scoring import GraphRiskConfig, score_entity
from src.risk_engine.propagation import PropagationConfig, propagate_risk
from src.risk_engine.unified_risk import assess_unified_risk
from src.utils.io import load_object, save_json
from src.utils.seeding import set_global_seed

CONFIG_DIR = ARTIFACTS_DIR / "config"
MODELS_DIR = ARTIFACTS_DIR / "models"
AML_MODELS_DIR = MODELS_DIR / "aml"


def save_risk_engine_config():
    config_payload = {
        "dynamic_risk_weights": DEFAULT_WEIGHTS,
        "risk_level_thresholds": RISK_LEVEL_THRESHOLDS,
        "propagation_defaults": PropagationConfig().__dict__,
        "graph_risk_weights": GraphRiskConfig().weights,
        "cyber_exposure_impact_factors": CyberExposureConfig().impact_factors,
        "dbscan_incident_defaults": {
            "eps": DBSCANIncidentConfig().eps,
            "min_samples": DBSCANIncidentConfig().min_samples,
        },
        "disclaimer": (
            "All weights/thresholds above are ENGINEERING CONFIGURATION set "
            "by initial judgment for this hackathon-scale system. They are "
            "NOT the output of a fitted/validated statistical model and "
            "should be tuned against real incident outcomes before any "
            "production use."
        ),
    }
    save_json(config_payload, CONFIG_DIR / "risk_engine_weights.json")
    return config_payload


def run_amlsim_propagation_and_unified_example():
    print("\n--- AMLSim: graph propagation + unified risk example (REAL data) ---")
    amlsim = load_amlsim()
    graph = load_graph(amlsim.transactions, amlsim.accounts)

    suspicious = graph.find_suspicious_nodes(top_n=20)
    source_entity = int(suspicious.iloc[0]["ACCOUNT_ID"])
    graph_evidence = score_entity(graph, source_entity)

    propagation = propagate_risk(graph, source_entity, graph_evidence["graph_risk_score"])
    save_json(propagation, METRICS_DIR / "propagation_example.json")

    fitted_preproc = load_object(PREPROCESSORS_DIR / "amlsim_preprocessor.joblib")
    account_features = engineer_amlsim_account_features(
        amlsim.accounts, amlsim.transactions, amlsim.alert_members
    )
    row = account_features[account_features["ACCOUNT_ID"] == source_entity]
    aml_prob = None
    if not row.empty:
        X_row = fitted_preproc.pipeline.transform(row[fitted_preproc.output_feature_names])
        best_aml_model = load_object(AML_MODELS_DIR / "aml_logistic_regression.joblib")
        aml_prob = float(aml_predict_proba(best_aml_model, X_row)[0])

    unified = assess_unified_risk(
        entity_id=str(source_entity),
        aml_probability=aml_prob,
        graph_risk_score=graph_evidence["graph_risk_score"],
        propagation_result=propagation,
        financial_exposure=None,
        incident_type="aml_flag",
    )

    explanation = build_full_explanation(
        unified_result=unified,
        shap_explanation=None,
        graph_evidence=graph_evidence,
        raw_transaction_summary={
            "entity_type": "AMLSim account",
            "account_id": source_entity,
            "account_type": amlsim.accounts.loc[amlsim.accounts["ACCOUNT_ID"] == source_entity, "ACCOUNT_TYPE"].iloc[0],
            "country": amlsim.accounts.loc[amlsim.accounts["ACCOUNT_ID"] == source_entity, "COUNTRY"].iloc[0],
        },
    )

    print(f"  source_entity={source_entity}, graph_risk_score={graph_evidence['graph_risk_score']}, "
          f"aml_probability={aml_prob}, blast_radius={propagation['blast_radius']}")
    print(f"  unified risk_score={unified['risk_score']} risk_level={unified['risk_level']}")

    return unified, explanation


def run_indian_banking_unified_example():
    print("\n--- Indian Banking: dynamic risk + cyber exposure + unified example (REAL data) ---")
    fitted_preproc = load_object(PREPROCESSORS_DIR / "indian_banking_preprocessor.joblib")
    dataset = load_processed_dataset(
        INDIAN_BANKING_PROCESSED_DIR, "is_fraud", fitted_preproc.output_feature_names
    )
    fitted_if = load_object(MODELS_DIR / "indian_banking_isolation_forest.joblib")
    fitted_xgb = load_object(MODELS_DIR / "indian_banking_xgboost.joblib")

    test_prob = xgb_predict_proba(fitted_xgb, dataset.test.X)
    test_anomaly = anomaly_scores(fitted_if.model, dataset.test.X)

    idx = int(np.argmax(test_prob))
    transaction_id = dataset.test.ids.iloc[idx]["transaction_id"]
    fraud_prob = float(test_prob[idx])
    anomaly_raw = float(test_anomaly[idx])

    raw = load_indian_banking()
    txn_row = raw.full[raw.full["transaction_id"] == transaction_id].iloc[0]
    financial_exposure = float(txn_row["transaction_amount"])

    unified = assess_unified_risk(
        transaction_id=str(transaction_id),
        fraud_probability=fraud_prob,
        anomaly_score_raw=anomaly_raw,
        financial_exposure=financial_exposure,
        incident_type="high_confidence_fraud_flag" if fraud_prob >= 0.5 else "anomaly_only",
    )

    explainer = FraudExplainer(
        fitted_xgb.model,
        fitted_xgb.feature_names,
        feature_dictionary_path=FEATURE_DICTIONARY_PATH,
        dataset_key="indian_banking",
    )
    shap_explanation = explainer.explain(dataset.test.X[idx], fitted_xgb.threshold, top_n=5).to_dict()

    explanation = build_full_explanation(
        unified_result=unified,
        shap_explanation=shap_explanation,
        graph_evidence=None,
        raw_transaction_summary={
            "transaction_id": str(transaction_id),
            "transaction_amount": financial_exposure,
            "channel": txn_row["channel"],
            "transaction_type": txn_row["transaction_type"],
            "merchant_category": txn_row["merchant_category"],
            "transaction_datetime": f"{txn_row['transaction_date']} {txn_row['transaction_time']}",
            "actual_is_fraud_label_for_reference_only": bool(txn_row["is_fraud"]),
        },
    )

    print(f"  transaction_id={transaction_id}, fraud_probability={fraud_prob:.4f}, "
          f"anomaly_score_raw={anomaly_raw:.4f}, transaction_amount={financial_exposure:.2f}")
    print(f"  unified risk_score={unified['risk_score']} risk_level={unified['risk_level']} "
          f"cyber_exposure={unified['cyber_exposure']}")

    return unified, explanation, dataset, fitted_if, fitted_xgb, test_prob, test_anomaly, raw


def run_dbscan_clustering(dataset, fitted_if, fitted_xgb, test_prob, test_anomaly, raw):
    print("\n--- Indian Banking: DBSCAN incident clustering on REAL flagged transactions ---")
    ids = dataset.test.ids.copy()
    ids["fraud_probability"] = test_prob
    ids["anomaly_score_raw"] = test_anomaly
    ids["risk_score"] = np.clip(test_prob * 100.0, 0, 100)

    flagged = ids[ids["fraud_probability"] >= fitted_xgb.threshold].copy()
    flagged = flagged.merge(
        raw.full[["transaction_id", "transaction_amount", "channel", "transaction_type"]],
        on="transaction_id",
        how="left",
    )
    flagged["amount_log1p"] = np.log1p(flagged["transaction_amount"])
    flagged["time_numeric"] = pd.to_datetime(flagged["transaction_datetime"]).astype("int64") / 1e9

    print(f"  {len(flagged)} flagged transactions passed to DBSCAN")

    config = DBSCANIncidentConfig(
        eps=1.5,
        min_samples=3,
        numeric_cols=("time_numeric", "risk_score", "amount_log1p"),
        categorical_cols=("channel", "transaction_type"),
    )
    result = cluster_incidents(
        flagged,
        event_id_col="transaction_id",
        entity_id_col="customer_id",
        time_col="transaction_datetime",
        risk_score_col="risk_score",
        config=config,
    )
    print(f"  n_clusters={result['n_clusters']}, n_noise(isolated)={result['n_noise']}")
    save_json(result, METRICS_DIR / "dbscan_incidents.json")
    return result


def build_documentation(config_payload, ib_example, aml_example, dbscan_result):
    import json

    lines = ["# Core Cyber Risk Intelligence Layer — Documentation\n"]

    lines.append("## Dynamic Risk Formula\n")
    lines.append(
        "`risk_score = 100 * sum(normalized_signal_i * weight_i) / sum(weight_i for available signals)`\n\n"
        "Signals are first normalized onto a common 0-100 scale (see "
        "`src/risk_engine/dynamic_risk.py::normalize_signal`), then combined "
        "with weights **renormalized over whichever signals are actually "
        "available** for the entity/transaction being scored, so a missing "
        "signal never silently drags the score toward zero.\n"
    )

    lines.append("## Initial Component Weights (engineering configuration, not fitted)\n")
    for k, v in config_payload["dynamic_risk_weights"].items():
        lines.append(f"- `{k}`: {v}")
    lines.append(
        "\nThese weights were set by initial engineering judgment for this "
        "hackathon-scale system — fraud and AML evidence are weighted "
        "highest since they come from supervised models trained directly "
        "on labeled outcomes, while graph/propagation/criticality are "
        "weighted lower since they are unsupervised/structural proxies. "
        "**They are not the output of any statistical fitting procedure "
        "and should be recalibrated against real incident outcomes before "
        "production use.**\n"
    )

    lines.append("## Risk Level Thresholds\n")
    for level, (lo, hi) in config_payload["risk_level_thresholds"].items():
        lines.append(f"- `{level}`: [{lo}, {hi})")

    lines.append("\n## Graph Risk Propagation Methodology\n")
    lines.append(
        "Weighted BFS from a source entity, up to `max_depth` hops "
        f"(default {config_payload['propagation_defaults']['max_depth']}). "
        "At each hop, carried risk is multiplied by "
        f"`decay_per_hop` (default {config_payload['propagation_defaults']['decay_per_hop']}), "
        "a relationship-strength factor derived from the number of actual "
        "transactions between the pair (no amount field exists in the raw "
        "AMLSim data, so transaction *count* is used as the strength proxy, "
        "not monetary value), and a criticality multiplier based on the "
        "neighbor's normalized total_degree. Propagation stops once carried "
        f"risk falls below `min_risk_to_propagate` "
        f"(default {config_payload['propagation_defaults']['min_risk_to_propagate']}). "
        "**This is a simulation for prioritization, not a prediction that "
        "fraud/AML activity will actually spread.**\n"
    )

    lines.append("## Cyber Exposure Estimate Methodology\n")
    lines.append(
        "`estimated_exposure = risk_probability * financial_exposure * impact_factor * propagation_factor`\n\n"
        "- `financial_exposure`: an ACTUAL monetary field from the dataset "
        "(Indian Banking `transaction_amount`) — when no reliable monetary "
        "field exists (ULB opaque V-features, AMLSim's amount-less raw "
        "transactions.csv), this is explicitly `null`/`insufficient_data`, "
        "never invented.\n"
        f"- `impact_factor` (by incident_type): {config_payload['cyber_exposure_impact_factors']}\n"
        "- `propagation_factor`: 1.0-2.0, scaled up when the propagation "
        "engine found meaningfully elevated risk in connected entities.\n\n"
        "**This is an engineering Cyber Exposure Estimate for "
        "prioritization, explicitly NOT regulated financial Value-at-Risk "
        "(no historical loss distribution, backtesting, or regulatory "
        "capital methodology is used).**\n"
    )

    lines.append("## DBSCAN Incident Clustering Configuration\n")
    lines.append(
        f"`eps={config_payload['dbscan_incident_defaults']['eps']}`, "
        f"`min_samples={config_payload['dbscan_incident_defaults']['min_samples']}`, "
        "features: time (numeric, standardized), risk_score (standardized), "
        "log1p(amount) (standardized), channel + transaction_type "
        "(one-hot). Run only on transactions the fraud model already "
        "flagged above its tuned threshold, on the REAL Indian Banking test "
        f"split: found {dbscan_result['n_clusters']} cluster(s) and "
        f"{dbscan_result['n_noise']} isolated (noise) events. **No "
        "clustering accuracy is claimed — there is no ground-truth incident "
        "grouping in this dataset to validate against.**\n"
    )

    lines.append("## Example Unified Risk Outputs (REAL data)\n")
    lines.append("### Indian Banking transaction\n```json")
    lines.append(json.dumps(ib_example, indent=2, default=str))
    lines.append("```\n")
    lines.append("### AMLSim account\n```json")
    lines.append(json.dumps(aml_example, indent=2, default=str))
    lines.append("```\n")

    lines.append("## Limitations\n")
    lines.append(
        "- Weights throughout this layer are initial engineering estimates, "
        "not fitted/validated against real outcomes.\n"
        "- The underlying fraud/AML models this layer consumes are "
        "themselves weak on Indian Banking and AMLSim (see prior stage "
        "reports) — the risk engine cannot manufacture signal that isn't in "
        "the upstream models.\n"
        "- Cyber Exposure is unavailable (by design) for ULB and AMLSim "
        "since no monetary field exists in that raw data.\n"
        "- Propagation and graph-risk scoring only apply to entities present "
        "in the AMLSim transaction graph; Indian Banking/ULB transactions "
        "have no graph representation in this system.\n"
    )

    return "\n".join(lines)


def main():
    set_global_seed(RANDOM_SEED)
    ensure_dirs()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    config_payload = save_risk_engine_config()

    aml_unified, aml_explanation = run_amlsim_propagation_and_unified_example()
    ib_unified, ib_explanation, dataset, fitted_if, fitted_xgb, test_prob, test_anomaly, raw = (
        run_indian_banking_unified_example()
    )
    dbscan_result = run_dbscan_clustering(dataset, fitted_if, fitted_xgb, test_prob, test_anomaly, raw)

    save_json(
        {"indian_banking_example": ib_unified, "amlsim_example": aml_unified},
        METRICS_DIR / "unified_risk_examples.json",
    )
    save_json(ib_explanation, METRICS_DIR / "full_explanation_indian_banking_example.json")
    save_json(aml_explanation, METRICS_DIR / "full_explanation_amlsim_example.json")

    doc = build_documentation(config_payload, ib_unified, aml_unified, dbscan_result)
    (METRICS_DIR / "risk_engine_documentation.md").write_text(doc)

    print("\n=== CORE CYBER RISK INTELLIGENCE LAYER COMPLETE ===")
    print(f"Config -> {CONFIG_DIR / 'risk_engine_weights.json'}")
    print(f"Documentation -> {METRICS_DIR / 'risk_engine_documentation.md'}")


if __name__ == "__main__":
    main()
