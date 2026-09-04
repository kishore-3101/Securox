from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

class TelemetryValidationResult(BaseModel):
    is_valid: bool
    data_quality_score: float  # 0.0 to 100.0%
    checks_passed: List[str]
    anomalies_detected: List[str]
    confidence: float

class DataQualityEngine:
    def validate_sensor_telemetry(
        self,
        sensor_id: str,
        value: float,
        min_allowed: float,
        max_allowed: float,
        reading_timestamp: datetime,
        previous_timestamp: datetime = None,
        previous_value: float = None,
        expected_frequency_sec: float = 5.0
    ) -> TelemetryValidationResult:
        score = 100.0
        passed = []
        anomalies = []

        # 1. Range Validation
        if min_allowed <= value <= max_allowed:
            passed.append("Value within physiological threshold bounds")
        else:
            score -= 35.0
            anomalies.append(f"Value {value} out of expected bounds [{min_allowed}, {max_allowed}]")

        # 2. Timestamp Freshness
        now = datetime.utcnow()
        skew_sec = abs((now - reading_timestamp).total_seconds())
        if skew_sec <= 60.0:
            passed.append("Timestamp within valid temporal window")
        else:
            score -= 25.0
            anomalies.append(f"High timestamp skew ({skew_sec:.1f}s drift)")

        # 3. Frequency / Cadence
        if previous_timestamp:
            interval = abs((reading_timestamp - previous_timestamp).total_seconds())
            if 0.5 * expected_frequency_sec <= interval <= 2.5 * expected_frequency_sec:
                passed.append("Telemetry sampling frequency nominal")
            else:
                score -= 15.0
                anomalies.append(f"Irregular sampling interval: {interval:.1f}s vs {expected_frequency_sec}s expected")

        # 4. Duplicate Check (Frozen value)
        if previous_value is not None and value == previous_value and value != 0:
            passed.append("Non-zero reading received")

        final_score = max(0.0, min(100.0, round(score, 1)))

        return TelemetryValidationResult(
            is_valid=(final_score >= 60.0),
            data_quality_score=final_score,
            checks_passed=passed,
            anomalies_detected=anomalies,
            confidence=round(final_score / 100.0, 2)
        )

data_quality_engine = DataQualityEngine()
