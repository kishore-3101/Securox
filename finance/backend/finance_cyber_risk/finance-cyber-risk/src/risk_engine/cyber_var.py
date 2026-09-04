"""
Cyber Exposure Estimate.

IMPORTANT: this is an ENGINEERING cyber-risk exposure estimate for
prioritization purposes. It is explicitly NOT regulated financial
Value-at-Risk (VaR) in the market/credit-risk sense — no historical loss
distribution, backtesting, or regulatory capital methodology is used here.
Where this module's output is referred to informally as "Cyber-VaR", that
name means only "a VaR-flavored point estimate of possible exposure", not a
compliant VaR figure.

Formula (documented, not fitted to any target):

    expected_exposure = risk_probability * financial_exposure * impact_factor * propagation_factor

  - risk_probability   : the dynamic risk engine's risk_score / 100 (or a raw model
                          probability if that's all that's available)
  - financial_exposure : an ACTUAL monetary field from the transaction, when one
                          exists (Indian Banking: `transaction_amount`,
                          `account_balance`). ULB/AMLSim entities have no
                          reliable monetary field available in the raw data
                          we have (V1-V28 are opaque; AMLSim's raw
                          transactions.csv has no amount) — in that case
                          financial_exposure is explicitly None and the
                          function refuses to invent a number, returning a
                          documented "insufficient_data" result instead of a
                          silently fabricated one.
  - impact_factor      : a documented, configurable multiplier reflecting how
                          severe a realized incident of this TYPE would be
                          (e.g. confirmed fraud vs AML flag vs generic anomaly).
                          This is an engineering assumption, not fitted data.
  - propagation_factor : 1 + (blast_radius-derived risk / 100), i.e. how much
                          the estimate should scale up because the propagation
                          engine found this risk could plausibly implicate
                          other connected entities. Defaults to 1.0 (no
                          propagation considered) when propagation data isn't
                          supplied.
"""
from dataclasses import dataclass
from typing import Optional

DEFAULT_IMPACT_FACTORS = {
    "confirmed_fraud": 1.0,
    "high_confidence_fraud_flag": 0.7,
    "aml_flag": 0.5,
    "anomaly_only": 0.25,
    "unknown": 0.4,
}


@dataclass
class CyberExposureConfig:
    impact_factors: dict = None

    def __post_init__(self):
        if self.impact_factors is None:
            self.impact_factors = dict(DEFAULT_IMPACT_FACTORS)


def estimate_cyber_exposure(
    risk_probability: float,
    financial_exposure: Optional[float],
    incident_type: str = "unknown",
    propagation_blast_radius: int = 0,
    propagation_avg_downstream_risk: float = 0.0,
    config: Optional[CyberExposureConfig] = None,
) -> dict:
    """
    risk_probability: 0-1 (e.g. dynamic risk_score/100, or a raw model probability)
    financial_exposure: an ACTUAL monetary figure known for this transaction/
        account (e.g. transaction_amount or account_balance from Indian
        Banking). Pass None when no real monetary field exists — this
        function will not substitute a guess.
    incident_type: one of DEFAULT_IMPACT_FACTORS' keys (documents which
        impact multiplier applies and why).
    """
    config = config or CyberExposureConfig()

    if incident_type not in config.impact_factors:
        incident_type = "unknown"
    impact_factor = config.impact_factors[incident_type]

    # propagation_factor >= 1.0: scales exposure up when connected entities
    # are also at meaningfully elevated risk. Capped at 2.0 so a single
    # source incident's exposure estimate can't run away unboundedly.
    propagation_factor = 1.0
    if propagation_blast_radius > 0:
        propagation_factor = min(2.0, 1.0 + (propagation_avg_downstream_risk / 100.0))

    if financial_exposure is None:
        return {
            "estimated_exposure": None,
            "exposure_factor": None,
            "impact_factor": impact_factor,
            "propagation_factor": round(propagation_factor, 3),
            "confidence": "insufficient_data",
            "explanation": (
                "No actual monetary field is available for this entity/transaction "
                "in the underlying dataset (e.g. ULB and AMLSim have no reliable "
                "amount field here). Rather than inventing a financial figure, "
                "this function reports the exposure as unavailable."
            ),
        }

    estimated_exposure = float(risk_probability) * float(financial_exposure) * impact_factor * propagation_factor

    # confidence: a simple, documented heuristic — exposure estimates built
    # from small/near-zero financial figures or very low risk probability are
    # flagged lower-confidence, since the multiplication is more sensitive
    # to noise in that region.
    if risk_probability < 0.1 or financial_exposure <= 0:
        confidence = "low"
    elif risk_probability < 0.4:
        confidence = "medium"
    else:
        confidence = "high"

    return {
        "estimated_exposure": round(estimated_exposure, 2),
        "exposure_factor": round(float(financial_exposure), 2),
        "impact_factor": impact_factor,
        "propagation_factor": round(propagation_factor, 3),
        "confidence": confidence,
        "explanation": (
            f"estimated_exposure = risk_probability ({risk_probability:.3f}) x "
            f"financial_exposure ({financial_exposure:.2f}) x impact_factor "
            f"({impact_factor}, incident_type='{incident_type}') x "
            f"propagation_factor ({propagation_factor:.3f}). This is an "
            "engineering Cyber Exposure Estimate, not regulated financial VaR."
        ),
    }
