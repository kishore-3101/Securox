"""
AI incident commander: concise incident summaries and containment plans.
"""


class AICommander:
    def summarize(self, incident: dict) -> dict:
        severity = incident.get("severity", incident.get("risk_category", "medium"))
        asset = incident.get("asset", "smart_city_core")
        risk = incident.get("risk_score", incident.get("impact_score", 50))
        flags = incident.get("threat_flags", incident.get("contributors", []))
        return {
            "summary": f"{severity.upper()} incident affecting {asset} with estimated risk {risk}/100.",
            "impact": self._impact(asset, float(risk or 0)),
            "recommended_actions": self._actions(flags, asset),
            "containment_priority": "P1" if float(risk or 0) >= 80 else "P2" if float(risk or 0) >= 60 else "P3",
            "forensic_notes": [
                "Preserve event stream and websocket replay buffer.",
                "Correlate source IP, account, device and merchant identifiers.",
                "Export mitigation step timeline after containment.",
            ],
        }

    @staticmethod
    def _impact(asset: str, risk: float) -> str:
        if asset == "finance":
            return "Payment trust degradation, transaction holds and possible citizen complaint surge."
        if asset == "traffic_system":
            return "Signal timing instability, congestion spillover and emergency route delay."
        if risk >= 80:
            return "High blast-radius risk across dependent city services."
        return "Localized disruption risk with monitored downstream dependencies."

    @staticmethod
    def _actions(flags: list[str], asset: str) -> list[str]:
        joined = " ".join(flags).upper()
        if "FRAUD" in joined or asset == "finance":
            return ["Hold suspicious transactions", "Freeze linked mule accounts", "Increase gateway risk scoring"]
        if "TRAFFIC" in joined or asset == "traffic_system":
            return ["Switch signals to adaptive control", "Create green corridor", "Dispatch field traffic unit"]
        return ["Isolate affected asset", "Increase logging", "Notify SOC commander"]


ai_commander = AICommander()
