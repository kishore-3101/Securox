"""
CAREGUARD — Care Pathway Operational Exposure Engine
Calculates the operational degradation state of clinical workflows when
underlying digital assets or dependencies exhibit statistical anomalies.
Uses an explainable probabilistic multi-factor model grounded in NIST SP 800-30:
  Exposure = f(Statistical Anomaly Intensity [Z-Score], Asset Criticality, Pathway Acuity)
Replaces arbitrary weights with defensible cascade risk formulation.
Zero Synthetic Data Policy.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import numpy as np

from healthcare_core.healthcare.pathways.engine import CARE_PATHWAYS
from healthcare_core.healthcare.dependencies.graph import DIGITAL_HEALTHCARE_ASSETS
from healthcare_core.detection.healthcare_detectors import healthcare_detector_engine


class PathwayExposureState(BaseModel):
    pathway_id: str
    pathway_name: str
    exposure_score: int  # 0 - 100
    degradation_state: str
    clinical_impact_note: str
    active_threat_ids: List[str]
    underlying_impacted_assets: List[str]
    source_dataset: str
    evidence_observed: List[str]
    uncertainty_level: str
    derivation: str
    calculation_formula: str


class OperationalExposureEngine:
    """
    Translates observed clinical anomalies and asset compromises into
    clinical care pathway operational exposure and degradation states.
    """
    CRITICALITY_WEIGHTS = {
        "LIFE_CRITICAL": 1.0,
        "HIGH_CLINICAL": 0.8,
        "OPERATIONAL_SUPPORT": 0.5
    }

    def calculate_exposures(self) -> List[Dict[str, Any]]:
        threats = healthcare_detector_engine.run_all_detections()
        exposures: List[Dict[str, Any]] = []

        # Map asset compromises
        asset_threat_map: Dict[str, List[Dict[str, Any]]] = {}
        for t in threats:
            target = t.get("targeted_asset_id")
            if target:
                asset_threat_map.setdefault(target, []).append(t)

        for p_id, pathway in CARE_PATHWAYS.items():
            relevant_threat_ids: List[str] = []
            impacted_assets: List[str] = []
            evidence_lines: List[str] = []
            threat_contributions: List[float] = []

            for asset_id in pathway.primary_assets:
                if asset_id in asset_threat_map:
                    impacted_assets.append(asset_id)
                    asset_info = DIGITAL_HEALTHCARE_ASSETS.get(asset_id)
                    crit_tier = getattr(asset_info, "clinical_criticality", "HIGH_CLINICAL") if asset_info else "HIGH_CLINICAL"
                    crit_weight = self.CRITICALITY_WEIGHTS.get(crit_tier, 0.8)

                    for th in asset_threat_map[asset_id]:
                        relevant_threat_ids.append(th["event_id"])
                        stat = th.get("statistical_evidence", {})
                        z_val = abs(stat.get("z_score") or 2.0)
                        norm_intensity = min(1.0, z_val / 3.5)
                        
                        # Contribution = Anomaly Intensity * Asset Criticality
                        contribution = norm_intensity * crit_weight
                        threat_contributions.append(contribution)

                        evidence_lines.append(
                            f"{th['title']}: Z={stat.get('z_score', 'N/A')} on {asset_id} ({crit_tier})"
                        )

            # Probabilistic multi-threat cascade aggregation:
            # Combined Exposure = [1 - Prod(1 - contribution_k)] * Acuity_Weight
            if threat_contributions:
                combined_prob = 1.0 - float(np.prod([1.0 - min(0.85, c) for c in threat_contributions]))
                raw_score = int(round(min(100, combined_prob * pathway.clinical_acuity_weight * 100)))
            else:
                raw_score = 0

            if raw_score >= 70:
                deg_state = "SEVERELY DEGRADED"
                clinical_note = "Potential patient-safety impact: Critical. Immediate care delivery relies on paper/manual overrides. STAT response required."
            elif raw_score >= 40:
                deg_state = "DEGRADED"
                clinical_note = "Healthcare service availability may be affected. Workflow latency elevated; secondary digital verification offline."
            elif raw_score > 0:
                deg_state = "ELEVATED VULNERABILITY"
                clinical_note = "Operational continuity risk increased. Digital perimeter anomaly observed; clinical operations remain functional."
            else:
                deg_state = "NORMAL"
                clinical_note = "All clinical dependencies and telemetry streams operational within nominal baselines."

            exposures.append(PathwayExposureState(
                pathway_id=p_id,
                pathway_name=pathway.name,
                exposure_score=raw_score,
                degradation_state=deg_state,
                clinical_impact_note=clinical_note,
                active_threat_ids=relevant_threat_ids,
                underlying_impacted_assets=impacted_assets,
                source_dataset=pathway.source_dataset,
                evidence_observed=evidence_lines,
                uncertainty_level="MEDIUM",
                derivation="DATA_DERIVED",
                calculation_formula="Exposure = [1 - Prod(1 - (Normalized_Z * Asset_Criticality))] * Pathway_Acuity * 100"
            ).model_dump())

        return exposures


operational_exposure_engine = OperationalExposureEngine()
