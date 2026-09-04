"""
Securox — Standardized AI Model Inference & Health Interface
Guarantees:
  1. Every model returns: prediction, score, model, version, timestamp, features, important_factors
  2. Non-Ground-Truth Guarantee: ground_truth_claim is strictly False with explicit disclaimer
  3. Latency & performance tracking for health monitoring
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


STANDARD_DISCLAIMER = (
    "AI prediction represents a probabilistic statistical inference, not deterministic ground truth. "
    "All inferences must be contextualized by operational policy, audit baselines, and human review."
)


class ModelInferenceResult(BaseModel):
    """Universal standard output contract for all Securox AI models."""
    model: str
    version: str
    domain: str
    timestamp: str = Field(default_factory=_utcnow)
    prediction: Any
    score: float
    confidence: float
    ground_truth_claim: bool = False
    disclaimer: str = STANDARD_DISCLAIMER
    features: Dict[str, Any] = Field(default_factory=dict)
    important_factors: List[Dict[str, Any]] = Field(default_factory=list)
    latency_ms: float = 0.0
    model_attribution: str = "LIVE INFERENCE"

    model_config = {
        "arbitrary_types_allowed": True,
        "populate_by_name": True
    }


class BaseAIModel(ABC):
    """Abstract base class for all authentic Securox AI models."""

    def __init__(self, model_id: str, model_name: str, domain: str, version: str):
        self.model_id = model_id
        self.model_name = model_name
        self.domain = domain.upper()
        self.version = version
        self.status = "HEALTHY"
        self.total_inferences = 0
        self.total_errors = 0
        self.total_latency_ms = 0.0

    @abstractmethod
    async def _predict_internal(self, inputs: Dict[str, Any]) -> ModelInferenceResult:
        """Subclass implementation of inference logic."""
        pass

    async def predict(self, inputs: Dict[str, Any]) -> ModelInferenceResult:
        """Standardized wrapper executing inference with timing, error handling, and disclaimer enforcement."""
        t0 = time.perf_counter()
        try:
            result = await self._predict_internal(inputs)
            latency = (time.perf_counter() - t0) * 1000.0
            result.latency_ms = round(latency, 2)
            result.ground_truth_claim = False
            result.disclaimer = STANDARD_DISCLAIMER

            self.total_inferences += 1
            self.total_latency_ms += latency
            self.status = "HEALTHY"
            return result
        except Exception as e:
            latency = (time.perf_counter() - t0) * 1000.0
            self.total_errors += 1
            self.status = "DEGRADED"
            return ModelInferenceResult(
                model=self.model_name,
                version=self.version,
                domain=self.domain,
                prediction="ERROR_FALLBACK",
                score=50.0,
                confidence=0.10,
                ground_truth_claim=False,
                disclaimer=f"Inference encountered runtime error: {e}. {STANDARD_DISCLAIMER}",
                features={"error": str(e)},
                important_factors=[{"name": "RUNTIME_ERROR", "impact": 1.0, "details": str(e)}],
                latency_ms=round(latency, 2),
                model_attribution="DEMO"
            )

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Validates model availability, weight files, and resource readiness."""
        pass
