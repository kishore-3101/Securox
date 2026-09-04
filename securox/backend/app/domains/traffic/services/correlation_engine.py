import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from traffic_core.services.event_bus import NormalizedEvent

class CorrelatedSecurityIncident(BaseModel):
    correlation_id: str = Field(default_factory=lambda: f"CORR-{uuid.uuid4().hex[:8].upper()}")
    title: str
    incident_type: str  # CYBER_PHYSICAL, INFRASTRUCTURE_TAMPERING, TRAFFIC_SPOOFING, NETWORK_BREACH
    verdict: str  # CONFIRMED, SUSPECTED, POSSIBLE, INFORMATIONAL
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    composite_risk_score: float
    affected_assets: List[str]
    location: str
    correlated_event_ids: List[str]
    root_cause_summary: str
    factors: List[Dict[str, Any]]
    recommended_actions: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ThreatCorrelationEngine:
    def __init__(self, correlation_window_sec: int = 180):
        self.recent_events: List[NormalizedEvent] = []
        self.correlation_window_sec = correlation_window_sec
        self.active_correlations: List[CorrelatedSecurityIncident] = []

    def ingest_event(self, event: NormalizedEvent) -> Optional[CorrelatedSecurityIncident]:
        """
        Receives normalized events and executes multi-domain correlation rules.
        """
        self.recent_events.insert(0, event)
        # Prune events older than correlation window
        now = datetime.utcnow()
        self.recent_events = [
            e for e in self.recent_events 
            if (now - datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")).replace(tzinfo=None)).total_seconds() <= self.correlation_window_sec
        ]

        # Evaluate correlation rules
        return self._evaluate_correlations(event)

    def _evaluate_correlations(self, trigger_event: NormalizedEvent) -> Optional[CorrelatedSecurityIncident]:
        # Rule 1: Cyber-Physical Attack (Signal Anomaly/Tamper + Traffic Queue Buildup + Network Anomaly)
        signal_events = [e for e in self.recent_events if "SIGNAL" in e.event_type.upper() or "PHASE" in e.event_type.upper()]
        traffic_events = [e for e in self.recent_events if "CONGESTION" in e.event_type.upper() or "TRAFFIC" in e.event_type.upper()]
        network_events = [e for e in self.recent_events if "NETWORK" in e.event_type.upper() or "PORT_SCAN" in e.event_type.upper() or "BURST" in e.event_type.upper()]
        camera_events = [e for e in self.recent_events if "CAMERA" in e.event_type.upper()]
        user_events = [e for e in self.recent_events if "USER" in e.event_type.upper() or "AUTH" in e.event_type.upper()]

        # Check for Cyber-Physical Incident
        if signal_events and traffic_events and network_events:
            linked_ids = [e.event_id for e in (signal_events[:2] + traffic_events[:2] + network_events[:2])]
            assets = list(set([e.asset_id for e in (signal_events + traffic_events + network_events)]))
            
            corr = CorrelatedSecurityIncident(
                title="HIGH-SEVERITY CYBER-PHYSICAL ATTACK IN PROGRESS",
                incident_type="CYBER_PHYSICAL",
                verdict="CONFIRMED",
                severity="CRITICAL",
                composite_risk_score=94.0,
                affected_assets=assets,
                location=trigger_event.location,
                correlated_event_ids=linked_ids,
                root_cause_summary=(
                    f"Traffic signal timing manipulation coincided with network intrusion telemetry "
                    f"and immediate severe congestion queueing at {trigger_event.location}."
                ),
                factors=[
                    {"factor": "Unauthorized signal controller override", "weight": "+35", "source": "NTCIP Controller"},
                    {"factor": "Network reconnaissance / port probing", "weight": "+25", "source": "Edge Firewall"},
                    {"factor": "Abnormal traffic congestion escalation", "weight": "+20", "source": "Traffic Density Engine"},
                    {"factor": "Critical infrastructure exposure", "weight": "+14", "source": "Asset Catalog"}
                ],
                recommended_actions=[
                    "Isolate controller network interface from upstream VLAN-20.",
                    "Engage hardware failsafe: switch traffic controller to FLASHING RED safety mode.",
                    "Dispatch field technician and alert municipal traffic authority.",
                    "Preserve network flow PCAP and controller access logs for digital forensics."
                ]
            )
            self.active_correlations.insert(0, corr)
            return corr

        # Rule 2: Coordinated Camera Outage + Network Event (Possible Reconnaissance / Blindspot Creation)
        if camera_events and network_events:
            linked_ids = [e.event_id for e in (camera_events[:2] + network_events[:2])]
            assets = list(set([e.asset_id for e in (camera_events + network_events)]))

            corr = CorrelatedSecurityIncident(
                title="COORDINATED CAMERA FEED TAMPERING & NETWORK EVENT",
                incident_type="INFRASTRUCTURE_TAMPERING",
                verdict="SUSPECTED",
                severity="HIGH",
                composite_risk_score=83.0,
                affected_assets=assets,
                location=trigger_event.location,
                root_cause_summary=(
                    f"Camera status degradation occurred within 30 seconds of an abnormal network flow burst, "
                    f"indicating deliberate camera blindspot induction."
                ),
                factors=[
                    {"factor": "Camera telemetry disruption / RTSP timeout", "weight": "+30", "source": "Camera Health Monitor"},
                    {"factor": "Volumetric network anomaly on camera subnet", "weight": "+28", "source": "Network Flow Sensor"},
                    {"factor": "Potential intentional surveillance denial", "weight": "+25", "source": "Correlation Engine"}
                ],
                recommended_actions=[
                    "Check physical switch port status and power over ethernet (PoE) supply.",
                    "Verify cryptographic certificate and hash on camera firmware.",
                    "Cross-reference neighboring cameras for secondary visual confirmation."
                ]
            )
            self.active_correlations.insert(0, corr)
            return corr

        # Rule 3: Sensor Discrepancy + Traffic Anomaly (Telemetry Spoofing)
        sensor_events = [e for e in self.recent_events if "SENSOR" in e.event_type.upper()]
        if sensor_events and traffic_events:
            linked_ids = [e.event_id for e in (sensor_events[:2] + traffic_events[:2])]
            assets = list(set([e.asset_id for e in (sensor_events + traffic_events)]))

            corr = CorrelatedSecurityIncident(
                title="SENSOR TELEMETRY SPOOFING & PHYSICAL INCONSISTENCY",
                incident_type="TRAFFIC_SPOOFING",
                verdict="SUSPECTED",
                severity="HIGH",
                composite_risk_score=78.0,
                affected_assets=assets,
                location=trigger_event.location,
                root_cause_summary=(
                    f"Physical roadway sensor reporting impossible or zero counts while camera vision "
                    f"registers high vehicle volume at {trigger_event.location}."
                ),
                factors=[
                    {"factor": "Sensor vs Computer Vision vehicle discrepancy", "weight": "+35", "source": "Cross-Validation Engine"},
                    {"factor": "Telemetry integrity failure", "weight": "+25", "source": "Sensor Quality Monitor"},
                    {"factor": "Impact on automated ramp metering algorithms", "weight": "+18", "source": "Traffic Flow Service"}
                ],
                recommended_actions=[
                    "Exclude faulty/spoofed sensor from automated signal timing calculations.",
                    "Recalibrate inductive loop detector.",
                    "Audit telemetry gateway for unauthorized MQTT or Modbus injections."
                ]
            )
            self.active_correlations.insert(0, corr)
            return corr

        return None

correlation_engine = ThreatCorrelationEngine()
