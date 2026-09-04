"""
Securox — Canonical Smart City Cyber Telemetry Schema
Provides unified dataclass, Pydantic model, and dictionary specifications
for cross-dataset normalization in SH-FIN-05.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ── Standardized Multi-Class Attack Categories ────────────────────────────────
ATTACK_CLASSES = [
    "BENIGN",
    "DOS",
    "DDOS",
    "BRUTE_FORCE",
    "PORT_SCAN",
    "BOTNET",
    "INFILTRATION",
    "WEB_ATTACK",
    "OTHER",
]

# Attack Class to Severity Level
ATTACK_SEVERITY_MAP = {
    "BENIGN": "LOW",
    "DOS": "HIGH",
    "DDOS": "CRITICAL",
    "BRUTE_FORCE": "HIGH",
    "PORT_SCAN": "MEDIUM",
    "BOTNET": "HIGH",
    "INFILTRATION": "CRITICAL",
    "WEB_ATTACK": "HIGH",
    "OTHER": "MEDIUM",
}

# Attack Class to Base Threat Weight (0.0 to 1.0)
ATTACK_WEIGHT_MAP = {
    "BENIGN": 0.05,
    "PORT_SCAN": 0.45,
    "BRUTE_FORCE": 0.65,
    "OTHER": 0.50,
    "WEB_ATTACK": 0.70,
    "DOS": 0.80,
    "BOTNET": 0.85,
    "DDOS": 0.95,
    "INFILTRATION": 1.00,
}


@dataclass
class CanonicalEvent:
    """
    Unified telemetry representation representing a single network flow
    or edge security event across smart city digital infrastructure.
    """
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_ip: str = "192.168.1.100"
    destination_ip: str = "10.0.0.1"
    source_port: int = 44320
    destination_port: int = 80
    protocol: str = "TCP"                  # TCP, UDP, ICMP, HTTP, etc.
    bytes_in: float = 0.0                  # Payload or wire bytes received
    bytes_out: float = 0.0                 # Payload or wire bytes sent
    packets: int = 1                       # Total packet count in flow
    duration: float = 0.001                # Flow duration in seconds
    request_rate: float = 1.0              # Inferred or measured requests/sec
    error_rate: float = 0.0                # Flow error or connection reset ratio
    asset_id: str = "TRAFFIC_CTRL_ZONE1"   # Target smart city asset ID
    asset_type: str = "traffic_control"    # traffic_control, power_grid, hospital, etc.
    location: str = "Bengaluru Central"    # Municipal zone / coordinate name
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    attack_type: str = "BENIGN"            # One of ATTACK_CLASSES
    label: int = 0                         # 0 = Benign, 1 = Attack
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_feature_vector(self) -> List[float]:
        """Returns standard numeric vector for ML pipelines."""
        tot_bytes = self.bytes_in + self.bytes_out
        dur = max(self.duration, 0.0001)
        byte_rate = tot_bytes / dur
        pkt_rate = self.packets / dur
        
        # Calculate port entropy surrogate
        port_val = float(self.destination_port % 1024) / 1024.0
        
        return [
            float(self.request_rate),
            float(byte_rate),
            float(pkt_rate),
            float(self.duration),
            float(self.bytes_in),
            float(self.bytes_out),
            float(self.packets),
            float(self.error_rate),
            float(port_val),
            1.0 if self.protocol.upper() == "TCP" else (0.5 if self.protocol.upper() == "UDP" else 0.0),
        ]


class CanonicalEventModel(BaseModel):
    """Pydantic validation model for API ingestion."""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source_ip: str
    destination_ip: str
    source_port: int = 0
    destination_port: int = 0
    protocol: str = "TCP"
    bytes_in: float = 0.0
    bytes_out: float = 0.0
    packets: int = 1
    duration: float = 0.001
    request_rate: float = 1.0
    error_rate: float = 0.0
    asset_id: str = "TRAFFIC_CTRL_ZONE1"
    asset_type: str = "traffic_control"
    location: str = "Bengaluru Central"
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    attack_type: str = "BENIGN"
    label: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
