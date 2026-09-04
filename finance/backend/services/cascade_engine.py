"""
Cascading failure forecaster for cyber-physical-financial dependencies.
"""

DEPENDENCIES = {
    "finance": ["public_transit", "healthcare", "communications"],
    "public_transit": ["traffic_system", "emergency_svcs"],
    "traffic_system": ["emergency_svcs", "public_safety"],
    "power_grid": ["traffic_system", "healthcare", "communications", "water_supply"],
    "communications": ["finance", "emergency_svcs"],
    "cctv_grid": ["traffic_system", "public_safety"],
}


class CascadeEngine:
    def forecast(self, origin: str, severity: float = 0.8, max_depth: int = 4) -> dict:
        queue = [(origin, min(1.0, severity), 0)]
        visited = set()
        events = []
        while queue:
            asset, score, depth = queue.pop(0)
            if asset in visited or depth > max_depth:
                continue
            visited.add(asset)
            events.append({
                "asset": asset,
                "depth": depth,
                "impact_score": round(score * 100, 1),
                "status": "offline" if score >= 0.9 else "compromised" if score >= 0.7 else "degraded",
                "estimated_delay_minutes": round(depth * 4 + score * 12, 1),
            })
            for child in DEPENDENCIES.get(asset, []):
                next_score = score * (0.62 - depth * 0.06)
                if next_score >= 0.18:
                    queue.append((child, next_score, depth + 1))
        return {"origin": origin, "severity": severity, "events": events, "blast_radius": len(events)}


cascade_engine = CascadeEngine()
