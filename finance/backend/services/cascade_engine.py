"""
Securox — Cascading Failure & What-If Simulation Engine (SH-FIN-05 Sections 17 & 18)
Calculates multi-hop downstream failure propagation, service disruption,
and blast-radius forecasting across the canonical 12 Smart City infrastructure nodes.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
backend_dir = PROJECT_ROOT / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from backend.assets.registry import asset_registry, ASSET_REGISTRY
except ImportError:
    try:
        from assets.registry import asset_registry, ASSET_REGISTRY
    except ImportError:
        ASSET_REGISTRY = {}
        asset_registry = None

logger = logging.getLogger("securox.cascade_engine")

# Sector disruption descriptions
SECTOR_DISRUPTIONS = {
    "energy": "Citywide electrical blackout, loss of substation SCADA telemetry, and reliance on emergency diesel reserves.",
    "telco": "Fiber ring severed, cellular packet core failure, and loss of municipal IoT / SCATS telemetry channels.",
    "transport": "Traffic signal desynchronization, major intersection gridlock, and blockage of emergency vehicle green corridors.",
    "healthcare": "Hospital telemetry desynchronization, Electronic Health Record outage, and diversion of trauma ambulances.",
    "utilities": "Pumping reservoir pressure drop, automated valve telemetry failure, and contamination monitoring blackout.",
    "fintech": "Treasury clearing freeze, municipal revenue portal outage, and FASTag toll barrier failures.",
    "emergency": "112 emergency dispatch queue overload and loss of real-time police/ambulance tracking.",
    "civic": "Citizen revenue, property tax, and public utility portals unresponsive.",
    "iot": "Loss of urban environmental, flood, and meteorological sensor streams.",
}


class CascadeEngine:
    """
    Simulates cascading failure paths using BFS traversal of the smart-city
    infrastructure dependency graph.
    """

    def _normalize_asset_id(self, asset_id: str) -> str:
        aid = asset_id.strip().upper()
        # Aliases
        alias_map = {
            "POWER": "POWER_GRID",
            "POWER_GRID": "POWER_GRID",
            "COMMUNICATIONS": "COMM_NETWORK",
            "COMM": "COMM_NETWORK",
            "TELCO": "COMM_NETWORK",
            "COMM_NETWORK": "COMM_NETWORK",
            "TRAFFIC": "TRAFFIC_CONTROL",
            "TRAFFIC_SYSTEM": "TRAFFIC_CONTROL",
            "TRAFFIC_CONTROL": "TRAFFIC_CONTROL",
            "WATER": "WATER_MANAGEMENT",
            "WATER_SUPPLY": "WATER_MANAGEMENT",
            "WATER_MANAGEMENT": "WATER_MANAGEMENT",
            "FINANCE": "FINANCIAL_SERVICES",
            "CORE_BANKING": "FINANCIAL_SERVICES",
            "FINANCIAL_SERVICES": "FINANCIAL_SERVICES",
            "HOSPITAL": "HEALTHCARE",
            "HEALTHCARE": "HEALTHCARE",
            "EMERGENCY": "EMERGENCY_SERVICES",
            "EMERGENCY_SVCS": "EMERGENCY_SERVICES",
            "EMERGENCY_SERVICES": "EMERGENCY_SERVICES",
            "SIGNALS": "TRAFFIC_SIGNALS",
            "TRAFFIC_SIGNALS": "TRAFFIC_SIGNALS",
            "CAMERAS": "TRAFFIC_CAMERAS",
            "CCTV_GRID": "TRAFFIC_CAMERAS",
            "TRAFFIC_CAMERAS": "TRAFFIC_CAMERAS",
            "PORTAL": "CITIZEN_PORTAL",
            "CITIZEN_PORTAL": "CITIZEN_PORTAL",
            "WIFI": "PUBLIC_WIFI",
            "PUBLIC_WIFI": "PUBLIC_WIFI",
            "IOT": "IOT_SENSORS",
            "IOT_SENSORS": "IOT_SENSORS",
        }
        return alias_map.get(aid, aid)

    def forecast(self, origin: str, severity: float = 0.8, max_depth: int = 4) -> dict:
        """
        Standard BFS cascading forecast starting from `origin` node.
        """
        canonical_origin = self._normalize_asset_id(origin)
        queue = [(canonical_origin, min(1.0, severity), 0)]
        visited = set()
        events = []

        while queue:
            current_asset, score, depth = queue.pop(0)
            if current_asset in visited or depth > max_depth:
                continue
            visited.add(current_asset)

            # Lookup asset details
            asset_data = ASSET_REGISTRY.get(current_asset)
            asset_name = asset_data.name if asset_data else current_asset
            criticality = asset_data.criticality if asset_data else 0.70
            sector = asset_data.sector if asset_data else "civic"

            status = "offline" if score >= 0.85 else "compromised" if score >= 0.60 else "degraded"
            events.append({
                "asset_id": current_asset,
                "asset": current_asset,
                "name": asset_name,
                "sector": sector,
                "depth": depth,
                "impact_score": round(score * 100, 1),
                "criticality": criticality,
                "status": status,
                "estimated_delay_minutes": round(depth * 3.5 + score * 8.0, 1),
                "disruption_summary": SECTOR_DISRUPTIONS.get(sector, "Municipal service degraded.")
            })

            # Downstream children from registry
            downstream = []
            if asset_data:
                downstream = asset_data.dependents
            else:
                # Fallback graph
                fallback_deps = {
                    "POWER_GRID": ["COMM_NETWORK", "WATER_MANAGEMENT", "TRAFFIC_CONTROL", "HEALTHCARE"],
                    "COMM_NETWORK": ["TRAFFIC_CONTROL", "EMERGENCY_SERVICES", "FINANCIAL_SERVICES", "HEALTHCARE", "CITIZEN_PORTAL"],
                    "TRAFFIC_CONTROL": ["TRAFFIC_SIGNALS", "TRAFFIC_CAMERAS", "EMERGENCY_SERVICES"],
                    "WATER_MANAGEMENT": ["HEALTHCARE"],
                    "FINANCIAL_SERVICES": ["CITIZEN_PORTAL"],
                }
                downstream = fallback_deps.get(current_asset, [])

            for child in downstream:
                canonical_child = self._normalize_asset_id(child)
                next_score = score * (0.80 - depth * 0.08)
                if next_score >= 0.15:
                    queue.append((canonical_child, next_score, depth + 1))

        return {
            "origin": canonical_origin,
            "severity": severity,
            "events": events,
            "blast_radius": len(events),
            "critical_dependents_count": sum(1 for e in events if e.get("criticality", 0) >= 0.90)
        }

    def simulate_what_if(self, target_asset: str, failure_type: str = "TOTAL_OUTAGE") -> dict:
        """
        Answers 'WHAT IF <Asset> is compromised or fails?' (SH-FIN-05 Section 18).
        Calculates affected assets, risk increase, potential service disruption,
        critical dependencies, and estimated blast radius.
        """
        canonical_target = self._normalize_asset_id(target_asset)
        asset_obj = ASSET_REGISTRY.get(canonical_target)
        name = asset_obj.name if asset_obj else canonical_target
        crit = asset_obj.criticality if asset_obj else 0.85
        sector = asset_obj.sector if asset_obj else "infrastructure"

        severity_map = {
            "TOTAL_OUTAGE": 0.95,
            "SCADA_COMPROMISE": 0.85,
            "DDOS_FLOOD": 0.75,
            "DEGRADED_STATE": 0.50
        }
        sev = severity_map.get(failure_type.upper(), 0.85)

        forecast_res = self.forecast(canonical_target, severity=sev, max_depth=4)
        affected = forecast_res["events"]

        # Risk increase estimate
        base_delta = int(crit * 45.0 + len(affected) * 4.0)
        risk_delta = min(60, max(15, base_delta))

        # Disruption narrative
        primary_disruption = SECTOR_DISRUPTIONS.get(sector, "Municipal service degraded.")
        downstream_names = [e["name"] for e in affected if e["asset_id"] != canonical_target]

        narrative = (
            f"If {name} suffers a {failure_type.replace('_', ' ').title()}, "
            f"{len(affected)} smart-city assets will experience cascading stress. "
            f"{primary_disruption} "
            f"Downstream systems immediately impacted: {', '.join(downstream_names[:4])}."
        )

        upstream_deps = asset_obj.dependencies if asset_obj else []

        return {
            "target_asset": canonical_target,
            "target_name": name,
            "failure_type": failure_type,
            "criticality": crit,
            "sector": sector,
            "risk_increase_delta": risk_delta,
            "estimated_blast_radius": len(affected),
            "affected_assets": affected,
            "upstream_dependencies": upstream_deps,
            "service_disruption_narrative": narrative,
            "immediate_recommendations": [
                f"Activate redundant power / comm links for {name}.",
                f"Isolate boundary routers between {canonical_target} and dependent networks.",
                f"Notify emergency responders and alert operators in downstream sectors: {', '.join(set(e['sector'] for e in affected))}."
            ]
        }


cascade_engine = CascadeEngine()
