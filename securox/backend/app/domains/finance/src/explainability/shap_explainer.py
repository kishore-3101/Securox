"""
Per-transaction SHAP explanations for the final XGBoost fraud model.

Feature descriptions come only from artifacts/metrics/feature_dictionary.json
(produced by the data-preparation stage) — we never invent a meaning for a
feature that isn't documented there. Raw, opaque features (ULB's V1-V28) are
reported by name only, with no assigned meaning, exactly as that dictionary
describes them.
"""
import re
from dataclasses import dataclass
from typing import Optional

import numpy as np
import shap

from src.utils.io import load_json


def _base_feature_name(processed_name: str) -> str:
    """
    Map a processed/one-hot column name back to the original feature it came
    from, e.g. 'cat__channel_Mobile_App' -> 'channel',
    'num__cust_amount_mean_so_far' -> 'cust_amount_mean_so_far'.
    """
    name = re.sub(r"^(cat__|num__|scaled__|passthrough__)", "", processed_name)
    return name


def _lookup_description(base_name: str, feature_dictionary: dict, dataset_key: str) -> str:
    if not feature_dictionary or dataset_key not in feature_dictionary:
        return "No description available in the feature dictionary."
    ds = feature_dictionary[dataset_key]
    for bucket in ["original_features", "generated_features"]:
        entries = ds.get(bucket, {})
        if base_name in entries:
            return entries[base_name].get("purpose", "No purpose documented.")
    # For one-hot categorical columns, the base_name may be "channel_Mobile_App"
    # -> strip the trailing value and try again against the original column.
    if "_" in base_name:
        candidate = base_name.rsplit("_", 1)[0]
        for bucket in ["original_features", "generated_features"]:
            entries = ds.get(bucket, {})
            if candidate in entries:
                return entries[candidate].get("purpose", "No purpose documented.")
    return "No description available in the feature dictionary."


@dataclass
class TransactionExplanation:
    fraud_probability: float
    predicted_class: int
    threshold_used: float
    top_features: list  # list of dicts: feature, value, shap_value, direction, description
    human_readable_summary: str

    def to_dict(self) -> dict:
        return {
            "fraud_probability": self.fraud_probability,
            "predicted_class": self.predicted_class,
            "threshold_used": self.threshold_used,
            "top_contributing_features": self.top_features,
            "human_readable_explanation": self.human_readable_summary,
        }


class FraudExplainer:
    def __init__(self, xgb_model, feature_names: list, feature_dictionary_path=None, dataset_key: str = "indian_banking"):
        self.explainer = shap.TreeExplainer(xgb_model)
        self.feature_names = feature_names
        self.dataset_key = dataset_key
        self.feature_dictionary = load_json(feature_dictionary_path) if feature_dictionary_path else {}
        self.model = xgb_model

    def explain(self, x_row: np.ndarray, threshold: float, top_n: int = 5) -> TransactionExplanation:
        x_row = np.asarray(x_row).reshape(1, -1)
        prob = float(self.model.predict_proba(x_row)[0, 1])
        predicted_class = int(prob >= threshold)

        shap_values = self.explainer.shap_values(x_row)
        if isinstance(shap_values, list):  # some SHAP versions return [class0, class1]
            shap_values = shap_values[-1]
        shap_row = np.asarray(shap_values).reshape(-1)

        order = np.argsort(-np.abs(shap_row))[:top_n]
        top_features = []
        for idx in order:
            processed_name = self.feature_names[idx]
            base_name = _base_feature_name(processed_name)
            description = _lookup_description(base_name, self.feature_dictionary, self.dataset_key)
            contribution = float(shap_row[idx])
            top_features.append(
                {
                    "feature": processed_name,
                    "value": float(x_row[0, idx]),
                    "shap_value": contribution,
                    "direction": "increases_fraud_risk" if contribution > 0 else "decreases_fraud_risk",
                    "magnitude": abs(contribution),
                    "description": description,
                }
            )

        summary = self._build_summary(prob, predicted_class, threshold, top_features)
        return TransactionExplanation(
            fraud_probability=prob,
            predicted_class=predicted_class,
            threshold_used=float(threshold),
            top_features=top_features,
            human_readable_summary=summary,
        )

    @staticmethod
    def _build_summary(prob, predicted_class, threshold, top_features) -> str:
        verdict = "flagged as FRAUD" if predicted_class == 1 else "NOT flagged as fraud"
        lines = [
            f"This transaction was {verdict} with a predicted fraud probability of "
            f"{prob:.3f} (decision threshold: {threshold:.3f})."
        ]
        if top_features:
            lines.append("The most influential factors were:")
            for f in top_features:
                direction = "pushed the risk UP" if f["shap_value"] > 0 else "pushed the risk DOWN"
                lines.append(
                    f"  - {f['feature']} = {f['value']:.4g} {direction} "
                    f"(impact magnitude {f['magnitude']:.4f}). {f['description']}"
                )
        return "\n".join(lines)
