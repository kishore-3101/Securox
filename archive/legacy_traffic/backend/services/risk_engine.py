from typing import List, Dict, Any
from pydantic import BaseModel

class RiskFactor(BaseModel):
    name: str
    impact: float
    description: str
    category: str  # CYBER, TRAFFIC, INFRASTRUCTURE, USER

class RiskScoreReport(BaseModel):
    overall_score: float  # 0.0 to 100.0
    severity: str        # LOW, MEDIUM, HIGH, CRITICAL
    trend: str           # INCREASING, STABLE, DECREASING
    contributing_factors: List[RiskFactor]
    summary: str
    timestamp: str

class RiskEngine:
    def calculate_system_risk(
        self,
        active_critical_incidents: int = 0,
        active_high_incidents: int = 0,
        active_cyber_threats: int = 0,
        max_congestion_score: float = 20.0,
        offline_cameras: int = 0,
        compromised_controllers: int = 0,
        compromised_sensors: int = 0
    ) -> RiskScoreReport:
        """
        Calculates an explainable 0-100 system risk score with weighted factor attribution.
        """
        from datetime import datetime
        base_score = 8.0
        factors: List[RiskFactor] = []

        # 1. Compromised traffic controllers (Safety Critical)
        if compromised_controllers > 0:
            impact = min(40.0, compromised_controllers * 35.0)
            base_score += impact
            factors.append(RiskFactor(
                name="Compromised Signal Controllers",
                impact=round(impact, 1),
                description=f"{compromised_controllers} traffic signal controller(s) exhibiting unauthorized overrides or safety interlock trips.",
                category="CYBER"
            ))

        # 2. Active Cyber Threats
        if active_cyber_threats > 0:
            impact = min(30.0, active_cyber_threats * 10.0)
            base_score += impact
            factors.append(RiskFactor(
                name="Active Cyber Threat Detections",
                impact=round(impact, 1),
                description=f"{active_cyber_threats} unresolved cyber threats (port scans, auth brute force, or exfiltration).",
                category="CYBER"
            ))

        # 3. Severe Traffic Congestion
        if max_congestion_score > 60.0:
            impact = round((max_congestion_score - 50.0) * 0.45, 1)
            base_score += impact
            factors.append(RiskFactor(
                name="High Roadway Congestion",
                impact=impact,
                description=f"Corridor congestion index reached {max_congestion_score:.0f}/100 with severe queue buildup.",
                category="TRAFFIC"
            ))

        # 4. Critical & High Active Incidents
        if active_critical_incidents > 0 or active_high_incidents > 0:
            impact = min(25.0, active_critical_incidents * 15.0 + active_high_incidents * 8.0)
            base_score += impact
            factors.append(RiskFactor(
                name="Correlated Incident Escalations",
                impact=round(impact, 1),
                description=f"{active_critical_incidents} critical and {active_high_incidents} high-severity active security incidents.",
                category="INFRASTRUCTURE"
            ))

        # 5. Offline or Compromised Cameras
        if offline_cameras > 0:
            impact = min(15.0, offline_cameras * 5.0)
            base_score += impact
            factors.append(RiskFactor(
                name="Surveillance Blindspots",
                impact=round(impact, 1),
                description=f"{offline_cameras} optical camera stream(s) currently offline or degraded.",
                category="INFRASTRUCTURE"
            ))

        # 6. Sensor Anomalies
        if compromised_sensors > 0:
            impact = min(12.0, compromised_sensors * 4.0)
            base_score += impact
            factors.append(RiskFactor(
                name="Sensor Telemetry Discrepancies",
                impact=round(impact, 1),
                description=f"{compromised_sensors} roadway sensor(s) reporting stuck or non-physical counts.",
                category="TRAFFIC"
            ))

        final_score = min(100.0, round(base_score, 1))

        if final_score >= 80.0:
            severity = "CRITICAL"
            trend = "INCREASING"
        elif final_score >= 60.0:
            severity = "HIGH"
            trend = "INCREASING"
        elif final_score >= 35.0:
            severity = "MEDIUM"
            trend = "STABLE"
        else:
            severity = "LOW"
            trend = "STABLE"

        summary = (
            f"Overall system risk is {severity} ({final_score}/100) driven by "
            + (", ".join([f.name.lower() for f in factors[:2]]) if factors else "nominal baseline operations.")
        )

        return RiskScoreReport(
            overall_score=final_score,
            severity=severity,
            trend=trend,
            contributing_factors=factors,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )

risk_engine = RiskEngine()
