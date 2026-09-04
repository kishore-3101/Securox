"""
Smart city health index engine.
"""


class CityHealthEngine:
    def calculate(self, twin_state: dict, traffic_stats: dict, fraud_alerts: list[dict]) -> dict:
        assets = twin_state.get("assets", {})
        risks = [float(a.get("risk_score", 0)) for a in assets.values()] or [0]
        avg_risk = sum(risks) / len(risks)
        cyber_health = max(0, round(100 - avg_risk, 1))

        junctions = traffic_stats.get("junctions", {})
        congestion = [
            float(j.get("congestion_index", 0))
            for j in junctions.values()
        ] or [0]
        traffic_health = max(0, round(100 - sum(congestion) / len(congestion), 1))
        financial_stability = max(0, round(100 - min(100, len(fraud_alerts) * 8), 1))
        emergency_readiness = max(0, round((cyber_health * 0.35) + (traffic_health * 0.45) + 20, 1))
        city_stability = round(
            cyber_health * 0.32 + financial_stability * 0.28 + traffic_health * 0.25 + emergency_readiness * 0.15,
            1,
        )
        return {
            "city_stability_index": city_stability,
            "cyber_health": cyber_health,
            "financial_stability": financial_stability,
            "traffic_health": traffic_health,
            "cctv_uptime": 98.4,
            "emergency_readiness": min(100, emergency_readiness),
            "citizen_trust_score": round((city_stability + financial_stability) / 2, 1),
        }


city_health_engine = CityHealthEngine()
