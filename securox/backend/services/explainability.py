"""
Explainability helpers for anomaly, fraud and cascade decisions.
"""


class ExplainabilityEngine:
    def explain(self, event: dict) -> dict:
        score = float(event.get("risk_score", event.get("anomaly_score", 0)) or 0)
        factors = event.get("contributors") or event.get("threat_flags") or ["behavioral_deviation"]
        return {
            "decision": event.get("decision", "escalate" if score >= 70 else "monitor"),
            "confidence": event.get("confidence", min(0.99, 0.45 + score / 140)),
            "risk_contributors": factors,
            "reason": event.get("explanation") or f"Risk score {score} derived from {', '.join(map(str, factors))}.",
        }


explainability = ExplainabilityEngine()
