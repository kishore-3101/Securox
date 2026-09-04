"""
Securox — Digital Twin Engine
Simulates a smart city with inter-connected subsystems.
Supports:
  • Normal-state baseline telemetry
  • Cascading failure propagation when an asset is compromised
  • What-if scenario injection
"""

import asyncio
import logging
import random
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("securox.twin")


# ── asset definitions ─────────────────────────────────────────────────────────
BASE_ASSETS: dict[str, dict] = {
    # Tier 0 — Critical Infrastructure
    "power_grid": {
        "name":         "Power Grid",
        "icon":         "⚡",
        "sector":       "energy",
        "tier":         0,
        "criticality":  1.00,
        "status":       "operational",
        "health":       100,
        "load":         62,
        "risk_score":   5,
        "financial_exposure_cr": 45.0,
        "coordinates":  {"x": 30,  "y": 20},
        "connections":  ["core_banking", "water_supply", "traffic_system", "communications"],
        "inbound_deps": ["power_grid"],
        "outbound_deps": ["core_banking", "water_supply", "traffic_system", "communications"],
    },
    "core_banking": {
        "name":         "Core Banking / Treasury",
        "icon":         "🏦",
        "sector":       "fintech",
        "tier":         0,
        "criticality":  0.98,
        "status":       "operational",
        "health":       100,
        "load":         55,
        "risk_score":   4,
        "financial_exposure_cr": 85.0,
        "coordinates":  {"x": 50,  "y": 25},
        "connections":  ["payment_gateway", "banking_api", "tax_portal"],
        "inbound_deps": ["power_grid"],
        "outbound_deps": ["payment_gateway", "banking_api", "tax_portal"],
    },
    "payment_gateway": {
        "name":         "Digital Payment Gateway",
        "icon":         "💳",
        "sector":       "fintech",
        "tier":         0,
        "criticality":  0.97,
        "status":       "operational",
        "health":       100,
        "load":         68,
        "risk_score":   5,
        "financial_exposure_cr": 62.5,
        "coordinates":  {"x": 75,  "y": 25},
        "connections":  ["upi_gateway", "fastag_infra", "metro_payment"],
        "inbound_deps": ["core_banking"],
        "outbound_deps": ["upi_gateway", "fastag_infra", "metro_payment"],
    },
    "tax_portal": {
        "name":         "Municipal Revenue & Tax System",
        "icon":         "🏛️",
        "sector":       "municipal",
        "tier":         0,
        "criticality":  0.96,
        "status":       "operational",
        "health":       100,
        "load":         52,
        "risk_score":   4,
        "financial_exposure_cr": 38.0,
        "coordinates":  {"x": 45,  "y": 45},
        "connections":  ["citizen_auth", "utility_billing"],
        "inbound_deps": ["core_banking"],
        "outbound_deps": ["citizen_auth", "utility_billing"],
    },
    "banking_api": {
        "name":         "Banking API Gateway",
        "icon":         "🔌",
        "sector":       "fintech",
        "tier":         0,
        "criticality":  0.95,
        "status":       "operational",
        "health":       100,
        "load":         61,
        "risk_score":   6,
        "financial_exposure_cr": 50.0,
        "coordinates":  {"x": 70,  "y": 45},
        "connections":  ["upi_gateway", "identity_provider"],
        "inbound_deps": ["core_banking"],
        "outbound_deps": ["upi_gateway", "identity_provider"],
    },

    # Tier 1 — High Criticality
    "upi_gateway": {
        "name":         "UPI Payment Gateway",
        "icon":         "📱",
        "sector":       "fintech",
        "tier":         1,
        "criticality":  0.90,
        "status":       "operational",
        "health":       100,
        "load":         74,
        "risk_score":   6,
        "financial_exposure_cr": 28.5,
        "coordinates":  {"x": 85,  "y": 45},
        "connections":  ["citizen_services"],
        "inbound_deps": ["payment_gateway", "banking_api"],
        "outbound_deps": ["citizen_services"],
    },
    "fastag_infra": {
        "name":         "FASTag Toll Infrastructure",
        "icon":         "🚗",
        "sector":       "transit",
        "tier":         1,
        "criticality":  0.88,
        "status":       "operational",
        "health":       100,
        "load":         65,
        "risk_score":   5,
        "financial_exposure_cr": 14.2,
        "coordinates":  {"x": 20,  "y": 50},
        "connections":  ["traffic_system"],
        "inbound_deps": ["payment_gateway"],
        "outbound_deps": ["traffic_system"],
    },
    "metro_payment": {
        "name":         "Metro Transit Ticketing",
        "icon":         "🚇",
        "sector":       "transit",
        "tier":         1,
        "criticality":  0.86,
        "status":       "operational",
        "health":       100,
        "load":         58,
        "risk_score":   4,
        "financial_exposure_cr": 11.8,
        "coordinates":  {"x": 15,  "y": 70},
        "connections":  ["traffic_system"],
        "inbound_deps": ["payment_gateway"],
        "outbound_deps": ["traffic_system"],
    },
    "utility_billing": {
        "name":         "Smart Utility Billing API",
        "icon":         "💡",
        "sector":       "utilities",
        "tier":         1,
        "criticality":  0.84,
        "status":       "operational",
        "health":       100,
        "load":         46,
        "risk_score":   3,
        "financial_exposure_cr": 16.0,
        "coordinates":  {"x": 55,  "y": 65},
        "connections":  ["water_supply"],
        "inbound_deps": ["tax_portal"],
        "outbound_deps": ["water_supply"],
    },
    "identity_provider": {
        "name":         "Citizen Identity Provider (IAM)",
        "icon":         "🆔",
        "sector":       "identity",
        "tier":         1,
        "criticality":  0.82,
        "status":       "operational",
        "health":       100,
        "load":         59,
        "risk_score":   4,
        "financial_exposure_cr": 22.0,
        "coordinates":  {"x": 65,  "y": 65},
        "connections":  ["citizen_auth"],
        "inbound_deps": ["banking_api"],
        "outbound_deps": ["citizen_auth"],
    },

    # Tier 2 — Important Services & Cyber-Physical Assets
    "water_supply": {
        "name":         "Smart Water Infrastructure",
        "icon":         "💧",
        "sector":       "utilities",
        "tier":         2,
        "criticality":  0.78,
        "status":       "operational",
        "health":       100,
        "load":         44,
        "risk_score":   4,
        "financial_exposure_cr": 8.5,
        "coordinates":  {"x": 35,  "y": 70},
        "connections":  ["healthcare"],
        "inbound_deps": ["power_grid", "utility_billing"],
        "outbound_deps": ["healthcare"],
    },
    "healthcare": {
        "name":         "Hospital & Health Billing",
        "icon":         "🩺",
        "sector":       "healthcare",
        "tier":         2,
        "criticality":  0.75,
        "status":       "operational",
        "health":       100,
        "load":         55,
        "risk_score":   6,
        "financial_exposure_cr": 19.4,
        "coordinates":  {"x": 75,  "y": 75},
        "connections":  [],
        "inbound_deps": ["water_supply", "power_grid"],
        "outbound_deps": [],
    },
    "traffic_system": {
        "name":         "Traffic System & CCTV Network",
        "icon":         "🚦",
        "sector":       "traffic",
        "tier":         2,
        "criticality":  0.70,
        "status":       "operational",
        "health":       100,
        "load":         71,
        "risk_score":   5,
        "financial_exposure_cr": 9.2,
        "coordinates":  {"x": 25,  "y": 80},
        "connections":  ["emergency_svcs"],
        "inbound_deps": ["power_grid", "fastag_infra", "metro_payment"],
        "outbound_deps": ["emergency_svcs"],
    },
    "citizen_auth": {
        "name":         "Citizen Portal Auth Gateway",
        "icon":         "🔑",
        "sector":       "identity",
        "tier":         2,
        "criticality":  0.72,
        "status":       "operational",
        "health":       100,
        "load":         50,
        "risk_score":   4,
        "financial_exposure_cr": 12.0,
        "coordinates":  {"x": 50,  "y": 85},
        "connections":  ["citizen_services"],
        "inbound_deps": ["tax_portal", "identity_provider"],
        "outbound_deps": ["citizen_services"],
    },
    "emergency_svcs": {
        "name":         "Emergency Services Dispatch",
        "icon":         "🚨",
        "sector":       "public_safety",
        "tier":         2,
        "criticality":  0.88,
        "status":       "operational",
        "health":       100,
        "load":         33,
        "risk_score":   5,
        "financial_exposure_cr": 7.0,
        "coordinates":  {"x": 38,  "y": 90},
        "connections":  [],
        "inbound_deps": ["traffic_system"],
        "outbound_deps": [],
    },
    "citizen_services": {
        "name":         "Citizen Digital Portal",
        "icon":         "🌐",
        "sector":       "citizen",
        "tier":         2,
        "criticality":  0.72,
        "status":       "operational",
        "health":       100,
        "load":         60,
        "risk_score":   4,
        "financial_exposure_cr": 6.8,
        "coordinates":  {"x": 68,  "y": 90},
        "connections":  [],
        "inbound_deps": ["upi_gateway", "citizen_auth"],
        "outbound_deps": [],
    },
    "iot_gateways": {
        "name":         "IoT Sensor Gateways",
        "icon":         "📡",
        "sector":       "iot",
        "tier":         3,
        "criticality":  0.45,
        "status":       "operational",
        "health":       100,
        "load":         40,
        "risk_score":   3,
        "financial_exposure_cr": 2.5,
        "coordinates":  {"x": 88,  "y": 88},
        "connections":  [],
        "inbound_deps": [],
        "outbound_deps": [],
    },
}

STATUS_LEVELS = ["operational", "degraded", "compromised", "offline"]


class DigitalTwin:
    """
    Maintains the live state of the smart-city digital twin.
    Thread-safe via asyncio.Lock.
    """

    def __init__(self):
        self._state: dict[str, dict] = deepcopy(BASE_ASSETS)
        self._events: list = []
        self._lock   = asyncio.Lock()
        self._active_scenario: str | None = None

    # ── state access ──────────────────────────────────────────────────────────
    async def get_state(self) -> dict:
        async with self._lock:
            return {
                "assets": deepcopy(self._state),
                "events": self._events[-20:],
                "active_scenario": self._active_scenario,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    async def update_asset_risk(self, asset: str, risk_score: float) -> None:
        async with self._lock:
            if asset in self._state:
                self._state[asset]["risk_score"] = round(risk_score, 1)
                # Derive status from risk
                if risk_score >= 80:
                    self._state[asset]["status"] = "compromised"
                elif risk_score >= 50:
                    self._state[asset]["status"] = "degraded"
                else:
                    self._state[asset]["status"] = "operational"
                # Degrade health proportionally
                self._state[asset]["health"] = max(
                    0, round(100 - risk_score * 0.8, 1)
                )

    # ── tick: inject small random noise for liveness ──────────────────────────
    async def tick(self) -> None:
        async with self._lock:
            for asset_id, asset in self._state.items():
                if asset["status"] == "operational":
                    noise = random.uniform(-0.5, 0.5)
                    asset["load"] = round(
                        max(10, min(95, asset["load"] + noise)), 1
                    )

    # ── scenario: propagate compromise ───────────────────────────────────────
    async def propagate_attack(self, origin_asset: str,
                                attack_type: str,
                                severity: float) -> list[dict]:
        """
        Simulates cascading failure starting from origin_asset.
        severity: 0–1 multiplier.
        Returns list of propagation event dicts.
        """
        events = []
        visited: set[str] = set()
        queue: list[tuple[str, float, int]] = [(origin_asset, severity, 0)]

        async with self._lock:
            self._active_scenario = attack_type

        while queue:
            asset_id, sev, depth = queue.pop(0)
            if asset_id in visited or depth > 5:
                continue
            visited.add(asset_id)

            async with self._lock:
                if asset_id not in self._state:
                    continue
                asset = self._state[asset_id]
                impact_score = round(sev * 100, 1)
                prev_status  = asset["status"]

                if sev >= 0.8:
                    asset["status"] = "compromised"
                elif sev >= 0.4:
                    asset["status"] = "degraded"

                asset["health"]     = max(0, round(asset["health"] - sev * 60, 1))
                asset["risk_score"] = min(100, round(impact_score, 1))

                event = {
                    "id":        str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "asset":     asset_id,
                    "asset_name": asset["name"],
                    "type":      "propagation",
                    "attack_type": attack_type,
                    "depth":     depth,
                    "severity":  round(sev, 3),
                    "status_change": f"{prev_status} → {asset['status']}",
                    "impact_score": impact_score,
                }
                events.append(event)
                self._events.append(event)

            # Propagate to connected assets with attenuated severity
            for neighbour in BASE_ASSETS.get(asset_id, {}).get("connections", []):
                attenuated = sev * random.uniform(0.4, 0.7)
                if attenuated > 0.1:
                    queue.append((neighbour, attenuated, depth + 1))

            await asyncio.sleep(0.05)   # slight delay for realistic streaming

        return events

    # ── reset ─────────────────────────────────────────────────────────────────
    async def reset(self) -> None:
        async with self._lock:
            self._state          = deepcopy(BASE_ASSETS)
            self._events         = []
            self._active_scenario = None
        logger.info("Digital twin reset to baseline.")


# ── singleton ─────────────────────────────────────────────────────────────────
digital_twin = DigitalTwin()
