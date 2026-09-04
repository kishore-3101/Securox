"""
Securox — Smart City Asset Registry
Defines the canonical 12 smart-city digital infrastructure assets,
their criticality ratings, geographic sectors, dependency graph topology,
and operational status.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional


@dataclass
class SmartCityAsset:
    asset_id: str
    name: str
    type: str
    criticality: float                 # 0.0 to 1.0 (Criticality multiplier)
    criticality_tier: str              # CRITICAL, HIGH, MEDIUM, LOW
    location: str
    sector: str                        # energy, transportation, healthcare, civic, fintech, telco
    status: str = "healthy"            # healthy, degraded, compromised, offline
    dependencies: List[str] = field(default_factory=list)      # Upstream dependencies
    dependents: List[str] = field(default_factory=list)        # Downstream dependents (affected if this fails)
    ip_subnets: List[str] = field(default_factory=list)
    protocols: List[str] = field(default_factory=list)
    coordinates: Dict[str, float] = field(default_factory=dict)
    financial_exposure_cr: float = 10.0 # Base monetary exposure in ₹ Crores

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── Canonical Smart City 12-Asset Registry ────────────────────────────────────
ASSET_REGISTRY: Dict[str, SmartCityAsset] = {
    # 1. Municipal Power Grid
    "POWER_GRID": SmartCityAsset(
        asset_id="POWER_GRID",
        name="Municipal Power Grid & SCADA",
        type="power_grid",
        criticality=1.00,
        criticality_tier="CRITICAL",
        location="Zone-0 Central Power Substation",
        sector="energy",
        status="healthy",
        dependencies=[],
        dependents=["COMM_NETWORK", "WATER_MANAGEMENT", "TRAFFIC_CONTROL", "HEALTHCARE"],
        ip_subnets=["10.10.0.0/24"],
        protocols=["MODBUS", "DNP3", "IEC-60870-5-104"],
        coordinates={"lat": 12.9716, "lng": 77.5946},
        financial_exposure_cr=120.0
    ),

    # 2. Telecommunications Core
    "COMM_NETWORK": SmartCityAsset(
        asset_id="COMM_NETWORK",
        name="Communication Network Core",
        type="communication_network",
        criticality=0.95,
        criticality_tier="CRITICAL",
        location="Zone-1 Telco Exchange & Fiber Ring",
        sector="telco",
        status="healthy",
        dependencies=["POWER_GRID"],
        dependents=["TRAFFIC_CONTROL", "EMERGENCY_SERVICES", "FINANCIAL_SERVICES", "HEALTHCARE", "CITIZEN_PORTAL"],
        ip_subnets=["10.20.0.0/24"],
        protocols=["BGP", "OSPF", "MPLS", "DNS"],
        coordinates={"lat": 12.9780, "lng": 77.5990},
        financial_exposure_cr=85.0
    ),

    # 3. Healthcare Infrastructure
    "HEALTHCARE": SmartCityAsset(
        asset_id="HEALTHCARE",
        name="Healthcare & Hospital Telemetry Core",
        type="healthcare",
        criticality=0.98,
        criticality_tier="CRITICAL",
        location="Zone-2 Victoria Super-Speciality Hospital",
        sector="healthcare",
        status="healthy",
        dependencies=["POWER_GRID", "COMM_NETWORK", "WATER_MANAGEMENT"],
        dependents=["EMERGENCY_SERVICES"],
        ip_subnets=["10.30.0.0/24"],
        protocols=["HL7", "DICOM", "HTTPS"],
        coordinates={"lat": 12.9640, "lng": 77.5850},
        financial_exposure_cr=95.0
    ),

    # 4. Emergency Services Dispatch
    "EMERGENCY_SERVICES": SmartCityAsset(
        asset_id="EMERGENCY_SERVICES",
        name="Emergency Services & 112 Dispatch",
        type="emergency_services",
        criticality=0.98,
        criticality_tier="CRITICAL",
        location="Central Police & Ambulance Command",
        sector="emergency",
        status="healthy",
        dependencies=["COMM_NETWORK", "TRAFFIC_CONTROL"],
        dependents=[],
        ip_subnets=["10.40.0.0/24"],
        protocols=["SIP", "RTP", "HTTPS", "TETRA"],
        coordinates={"lat": 12.9750, "lng": 77.5910},
        financial_exposure_cr=75.0
    ),

    # 5. Traffic Control System
    "TRAFFIC_CONTROL": SmartCityAsset(
        asset_id="TRAFFIC_CONTROL",
        name="Traffic Control System (SCATS/ITMS)",
        type="traffic_control",
        criticality=0.90,
        criticality_tier="HIGH",
        location="Traffic Management Center (TMC)",
        sector="transportation",
        status="healthy",
        dependencies=["POWER_GRID", "COMM_NETWORK"],
        dependents=["TRAFFIC_SIGNALS", "TRAFFIC_CAMERAS", "EMERGENCY_SERVICES"],
        ip_subnets=["10.50.0.0/24"],
        protocols=["NTCIP", "HTTP", "SNMP"],
        coordinates={"lat": 12.9730, "lng": 77.6010},
        financial_exposure_cr=55.0
    ),

    # 6. Smart Traffic Signals
    "TRAFFIC_SIGNALS": SmartCityAsset(
        asset_id="TRAFFIC_SIGNALS",
        name="Adaptive Traffic Signals (Intersection 4B)",
        type="traffic_signals",
        criticality=0.88,
        criticality_tier="HIGH",
        location="Silk Board & MG Road Corridors",
        sector="transportation",
        status="healthy",
        dependencies=["TRAFFIC_CONTROL", "POWER_GRID"],
        dependents=["TRAFFIC_CONTROL"],
        ip_subnets=["10.50.1.0/24"],
        protocols=["NTCIP", "MODBUS_TCP"],
        coordinates={"lat": 12.9170, "lng": 77.6230},
        financial_exposure_cr=35.0
    ),

    # 7. Traffic Surveillance Cameras
    "TRAFFIC_CAMERAS": SmartCityAsset(
        asset_id="TRAFFIC_CAMERAS",
        name="Traffic Cameras & Edge ANPR Vision",
        type="traffic_cameras",
        criticality=0.82,
        criticality_tier="HIGH",
        location="Corridor 01 to 08 CCTV Grid",
        sector="transportation",
        status="healthy",
        dependencies=["COMM_NETWORK", "POWER_GRID"],
        dependents=["TRAFFIC_CONTROL"],
        ip_subnets=["10.50.2.0/24"],
        protocols=["RTSP", "ONVIF", "HLS"],
        coordinates={"lat": 12.9810, "lng": 77.6080},
        financial_exposure_cr=28.0
    ),

    # 8. Financial Services Gateway
    "FINANCIAL_SERVICES": SmartCityAsset(
        asset_id="FINANCIAL_SERVICES",
        name="Financial Services & Payment Gateway",
        type="financial_services",
        criticality=0.96,
        criticality_tier="CRITICAL",
        location="Municipal Treasury & UPI Clearing Gateway",
        sector="fintech",
        status="healthy",
        dependencies=["POWER_GRID", "COMM_NETWORK"],
        dependents=["CITIZEN_PORTAL"],
        ip_subnets=["10.60.0.0/24"],
        protocols=["ISO-8583", "HTTPS", "mTLS"],
        coordinates={"lat": 12.9700, "lng": 77.6100},
        financial_exposure_cr=150.0
    ),

    # 9. Water SCADA & Quality
    "WATER_MANAGEMENT": SmartCityAsset(
        asset_id="WATER_MANAGEMENT",
        name="Water Management & Reservoir SCADA",
        type="water_management",
        criticality=0.85,
        criticality_tier="HIGH",
        location="Cauvery Water Pumping Station",
        sector="civic",
        status="healthy",
        dependencies=["POWER_GRID", "COMM_NETWORK"],
        dependents=["HEALTHCARE"],
        ip_subnets=["10.70.0.0/24"],
        protocols=["MODBUS", "BACnet"],
        coordinates={"lat": 12.9500, "lng": 77.5700},
        financial_exposure_cr=45.0
    ),

    # 10. Citizen Services Portal
    "CITIZEN_PORTAL": SmartCityAsset(
        asset_id="CITIZEN_PORTAL",
        name="Citizen Digital Revenue & Civic Portal",
        type="citizen_portal",
        criticality=0.75,
        criticality_tier="MEDIUM",
        location="Cloud Municipal Datacenter",
        sector="civic",
        status="healthy",
        dependencies=["COMM_NETWORK", "FINANCIAL_SERVICES"],
        dependents=[],
        ip_subnets=["10.80.0.0/24"],
        protocols=["HTTPS", "OIDC", "GraphQL"],
        coordinates={"lat": 12.9850, "lng": 77.6150},
        financial_exposure_cr=32.0
    ),

    # 11. Public Wi-Fi Infrastructure
    "PUBLIC_WIFI": SmartCityAsset(
        asset_id="PUBLIC_WIFI",
        name="Municipal Public Wi-Fi Mesh",
        type="public_wifi",
        criticality=0.55,
        criticality_tier="LOW",
        location="City Centers & Metro Transit Hubs",
        sector="telco",
        status="healthy",
        dependencies=["COMM_NETWORK", "POWER_GRID"],
        dependents=[],
        ip_subnets=["172.20.0.0/16"],
        protocols=["802.1X", "RADIUS", "WPA2-Enterprise"],
        coordinates={"lat": 12.9755, "lng": 77.6050},
        financial_exposure_cr=12.0
    ),

    # 12. IoT Environmental & Sensor Mesh
    "IOT_SENSORS": SmartCityAsset(
        asset_id="IOT_SENSORS",
        name="IoT Environmental & Flood Sensors",
        type="iot_sensors",
        criticality=0.60,
        criticality_tier="MEDIUM",
        location="Stormwater Drains & Weather Stations",
        sector="iot",
        status="healthy",
        dependencies=["COMM_NETWORK"],
        dependents=["WATER_MANAGEMENT"],
        ip_subnets=["10.90.0.0/24"],
        protocols=["MQTT", "CoAP", "LoRaWAN"],
        coordinates={"lat": 12.9900, "lng": 77.5800},
        financial_exposure_cr=15.0
    ),
}


class AssetRegistryService:
    """Manages querying, risk updates, and dependency lookups for all assets."""

    def __init__(self):
        self._assets = dict(ASSET_REGISTRY)

    def get_all(self) -> List[Dict[str, Any]]:
        return [a.to_dict() for a in self._assets.values()]

    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        # Case-insensitive / normalized lookup
        key = asset_id.upper().replace("-", "_").replace(" ", "_")
        for aid, a in self._assets.items():
            if aid == key or a.type.upper() == key:
                return a.to_dict()
        return None

    def get_criticality(self, asset_id: str) -> float:
        a = self.get_asset(asset_id)
        return a.get("criticality", 0.5) if a else 0.5

    def get_downstream_dependents(self, asset_id: str) -> List[str]:
        """Performs BFS graph traversal to return all downstream affected assets."""
        start_key = asset_id.upper().replace("-", "_").replace(" ", "_")
        visited = set()
        queue = list(self._assets.get(start_key, SmartCityAsset(asset_id, "", "", 0.5, "LOW", "", "")).dependents)

        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                if node in self._assets:
                    queue.extend(self._assets[node].dependents)

        return list(visited)

    def update_status(self, asset_id: str, status: str):
        key = asset_id.upper().replace("-", "_").replace(" ", "_")
        if key in self._assets:
            self._assets[key].status = status


asset_registry = AssetRegistryService()
SMART_CITY_ASSETS = ASSET_REGISTRY
get_all_assets = asset_registry.get_all
get_asset = asset_registry.get_asset
get_asset_blast_radius = asset_registry.get_downstream_dependents
