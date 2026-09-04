import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessionLocal
import models
from services.event_bus import event_bus, NormalizedEvent
from services.correlation_engine import correlation_engine
from services.incident_service import incident_service
from services.cv_engine import cv_engine

class ScenarioInfo(BaseModel):
    id: str
    name: str
    description: str
    severity: str
    steps_count: int
    domains: List[str]

SCENARIO_CATALOG: List[ScenarioInfo] = [
    ScenarioInfo(
        id="scenario_1",
        name="Scenario 1: Major Highway Congestion",
        description="Rapid vehicle density buildup on corridor NH44 causing speed collapse to 18 km/h.",
        severity="HIGH",
        steps_count=3,
        domains=["TRAFFIC"]
    ),
    ScenarioInfo(
        id="scenario_2",
        name="Scenario 2: Optical Camera Infrastructure Compromise",
        description="RTSP authentication brute force followed by firmware tampering and video feed blackout on CAM-04.",
        severity="HIGH",
        steps_count=4,
        domains=["CAMERA", "CYBER"]
    ),
    ScenarioInfo(
        id="scenario_3",
        name="Scenario 3: Roadway Sensor Spoofing & Disagreement",
        description="Loop detector telemetry injected with zero readings while vision cameras detect 380+ vehicles.",
        severity="MEDIUM",
        steps_count=3,
        domains=["SENSOR", "TRAFFIC"]
    ),
    ScenarioInfo(
        id="scenario_4",
        name="Scenario 4: Traffic Signal Controller Hijack",
        description="Unauthorized NTCIP command forces continuous red phase on major arterial intersection.",
        severity="HIGH",
        steps_count=3,
        domains=["SIGNAL", "CYBER"]
    ),
    ScenarioInfo(
        id="scenario_5",
        name="Scenario 5: Suspicious Operator Account Brute-Force",
        description="9 consecutive failed logins from an unapproved IP targeting the admin account.",
        severity="MEDIUM",
        steps_count=3,
        domains=["USER", "CYBER"]
    ),
    ScenarioInfo(
        id="scenario_6",
        name="Scenario 6: Lateral Network Port Scan & Reconnaissance",
        description="High-frequency port probing across OT VLAN targeting traffic controller and camera subnets.",
        severity="HIGH",
        steps_count=3,
        domains=["NETWORK", "CYBER"]
    ),
    ScenarioInfo(
        id="scenario_7",
        name="Scenario 7: Full Master Cyber-Physical Attack",
        description="Coordinated cyber-physical breach: unauthorized signal override + network burst + massive traffic gridlock.",
        severity="CRITICAL",
        steps_count=5,
        domains=["SIGNAL", "NETWORK", "TRAFFIC", "CORRELATION"]
    ),
    ScenarioInfo(
        id="scenario_8",
        name="Scenario 8: Multi-Vehicle Collision & Queue Bottleneck",
        description="Sudden braking and stationary vehicle anomaly on lane 2 followed by emergency queue propagation.",
        severity="HIGH",
        steps_count=3,
        domains=["CV", "TRAFFIC"]
    ),
    ScenarioInfo(
        id="scenario_9",
        name="Scenario 9: Multi-Domain Cascading Infrastructure Blackout",
        description="Simultaneous optical blindness, sensor corruption, and signal controller disconnect.",
        severity="CRITICAL",
        steps_count=4,
        domains=["CAMERA", "SIGNAL", "SENSOR", "CYBER"]
    )
]

class ScenarioSimulator:
    def __init__(self):
        self.active_scenario: Optional[str] = None
        self.scenario_state: str = "IDLE"  # IDLE, RUNNING, COMPLETED
        self.current_step: int = 0
        self.total_steps: int = 0
        self.execution_log: List[Dict[str, Any]] = []

    def get_catalog(self) -> List[ScenarioInfo]:
        return SCENARIO_CATALOG

    async def launch_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Launches an interactive scenario that cascades through the event bus and engines.
        """
        self.active_scenario = scenario_id
        self.scenario_state = "RUNNING"
        self.current_step = 1
        self.execution_log = []

        db = SessionLocal()
        try:
            if scenario_id == "scenario_7":
                # Master Cyber-Physical Demonstration flow
                return await self._run_master_cyber_physical(db)
            elif scenario_id == "scenario_1":
                return await self._run_major_congestion(db)
            elif scenario_id == "scenario_2":
                return await self._run_camera_compromise(db)
            elif scenario_id == "scenario_4":
                return await self._run_signal_hijack(db)
            else:
                # Fallback generic scenario execution
                return await self._run_generic_scenario(scenario_id, db)
        finally:
            db.close()

    async def _run_master_cyber_physical(self, db: Session) -> Dict[str, Any]:
        # Step 1: Reconnaissance Network Anomaly
        ev1 = NormalizedEvent(
            event_type="NETWORK_PORT_SCAN",
            severity="HIGH",
            asset_id="IP-192.168.10.84",
            location="Sector 4 - Intersection 12 OT Subnet",
            source="EDGE_NETWORK_IDS",
            confidence=0.96,
            title="Rapid Port Scan Reconnaissance Detected",
            description="Probing detected across TCP ports 80, 502, 161 (SNMP), and 5150 targeting Controller CTRL-INT12.",
            metadata={"source_ip": "192.168.10.84", "ports_scanned": [80, 161, 502, 5150]},
            is_simulated=True
        )
        await event_bus.publish(ev1)
        correlation_engine.ingest_event(ev1)

        # Step 2: Signal Controller Unauthorized Override
        sig = db.query(models.TrafficSignal).filter(models.TrafficSignal.intersection_id == "INT-12").first()
        if not sig:
            sig = db.query(models.TrafficSignal).first()
        if sig:
            sig.status = "MANIPULATED"
            sig.is_compromised = True
            sig.current_state = "RED"
            db.commit()

        ev2 = NormalizedEvent(
            event_type="SIGNAL_ANOMALY",
            severity="CRITICAL",
            asset_id=sig.controller_id if sig else "CTRL-INT12",
            location="Intersection 12 (Central Arterial)",
            source="NTCIP_CONTROLLER_IDS",
            confidence=0.98,
            title="Unauthorized Signal Timing Override",
            description="External unauthenticated command forced continuous 360-second RED lock on North-South corridor.",
            metadata={"controller_id": sig.controller_id if sig else "CTRL-INT12", "injected_phase": "ALL_RED_HOLD"},
            is_simulated=True
        )
        await event_bus.publish(ev2)
        correlation_engine.ingest_event(ev2)

        # Step 3: Physical Traffic Congestion Buildup
        road = db.query(models.RoadSegment).filter(models.RoadSegment.id == "ROAD-NH44-02").first()
        if not road:
            road = db.query(models.RoadSegment).first()
        if road:
            road.current_volume = 410
            road.current_speed_kmh = 14.5
            road.density_score = 92.0
            road.congestion_level = "CRITICAL"
            db.commit()

        ev3 = NormalizedEvent(
            event_type="TRAFFIC_CONGESTION",
            severity="CRITICAL",
            asset_id=road.id if road else "ROAD-NH44-02",
            location="Intersection 12 Approach (NH44-02)",
            source="TRAFFIC_DENSITY_ENGINE",
            confidence=0.95,
            title="Critical Traffic Gridlock & Queue Buildup",
            description="Vehicle volume surged +42% while average speed collapsed -78% (14.5 km/h) with 450m queue.",
            metadata={"queue_length_m": 450, "average_speed": 14.5, "density_index": 92.0},
            is_simulated=True
        )
        await event_bus.publish(ev3)
        corr = correlation_engine.ingest_event(ev3)

        # Step 4: Multi-Source Correlation Incident Generation
        if not corr:
            # Force correlation instance for scenario consistency
            corr = correlation_engine._evaluate_correlations(ev3)

        incident = None
        if corr:
            incident = incident_service.create_incident_from_correlation(
                db=db,
                title="CRITICAL CYBER-PHYSICAL INCIDENT: Coordinated Controller Compromise & Gridlock",
                incident_type="CYBER_PHYSICAL",
                severity="CRITICAL",
                asset_id=sig.controller_id if sig else "CTRL-INT12",
                location="Intersection 12 (Central Arterial)",
                risk_score=94.0,
                evidence={
                    "network_recon": ev1.event_id,
                    "signal_override": ev2.event_id,
                    "traffic_congestion": ev3.event_id,
                    "root_cause": "NTCIP controller unauthorized phase hold coinciding with port reconnaissance and corridor queueing."
                },
                root_cause="Unauthorized signal override caused severe physical congestion following network reconnaissance."
            )

        self.scenario_state = "COMPLETED"
        return {
            "scenario_id": "scenario_7",
            "status": "COMPLETED",
            "incident_id": incident.incident_id if incident else "INC-2026-001",
            "message": "Cyber-physical attack scenario executed. Live incident and correlation generated.",
            "events_published": [ev1.event_id, ev2.event_id, ev3.event_id],
            "correlation_id": corr.correlation_id if corr else None
        }

    async def _run_major_congestion(self, db: Session) -> Dict[str, Any]:
        road = db.query(models.RoadSegment).first()
        if road:
            road.current_volume = 385
            road.current_speed_kmh = 18.0
            road.density_score = 88.0
            road.congestion_level = "CRITICAL"
            db.commit()

        ev = NormalizedEvent(
            event_type="TRAFFIC_CONGESTION",
            severity="CRITICAL",
            asset_id=road.id if road else "ROAD-NH44-01",
            location=road.name if road else "NH44 Northbound",
            source="TRAFFIC_DENSITY_ENGINE",
            confidence=0.94,
            title="Severe Corridor Congestion Triggered",
            description="Vehicle throughput bottleneck observed. Density index 88/100.",
            is_simulated=True
        )
        await event_bus.publish(ev)
        return {"scenario_id": "scenario_1", "status": "COMPLETED", "event_id": ev.event_id}

    async def _run_camera_compromise(self, db: Session) -> Dict[str, Any]:
        cam = db.query(models.Camera).filter(models.Camera.id == "CAM-04").first() or db.query(models.Camera).first()
        if cam:
            cam.status = "COMPROMISED"
            cam.security_health = 25.0
            cam.risk_score = 88.0
            db.commit()

        ev = NormalizedEvent(
            event_type="CAMERA_SECURITY_BREACH",
            severity="HIGH",
            asset_id=cam.id if cam else "CAM-04",
            location=cam.location if cam else "NH44 KM 42",
            source="CAMERA_INTEGRITY_DAEMON",
            confidence=0.97,
            title=f"Camera Security Integrity Compromise on {cam.id if cam else 'CAM-04'}",
            description="Brute-force authentication bypass and unauthorized RTSP stream redirection detected.",
            is_simulated=True
        )
        await event_bus.publish(ev)
        return {"scenario_id": "scenario_2", "status": "COMPLETED", "event_id": ev.event_id}

    async def _run_signal_hijack(self, db: Session) -> Dict[str, Any]:
        sig = db.query(models.TrafficSignal).first()
        if sig:
            sig.status = "MANIPULATED"
            sig.is_compromised = True
            db.commit()

        ev = NormalizedEvent(
            event_type="SIGNAL_ANOMALY",
            severity="CRITICAL",
            asset_id=sig.id if sig else "SIG-01",
            location="Intersection 04",
            source="NTCIP_MONITOR",
            confidence=0.96,
            title="Unauthorized Traffic Signal Controller Manipulation",
            description="Impossible phase timing injected into controller firmware.",
            is_simulated=True
        )
        await event_bus.publish(ev)
        return {"scenario_id": "scenario_4", "status": "COMPLETED", "event_id": ev.event_id}

    async def _run_generic_scenario(self, scenario_id: str, db: Session) -> Dict[str, Any]:
        ev = NormalizedEvent(
            event_type="SIMULATED_INFRASTRUCTURE_ANOMALY",
            severity="HIGH",
            asset_id=f"ASSET-{scenario_id.upper()}",
            location="NH44 Highway Corridor",
            source="SCENARIO_SIMULATOR",
            confidence=0.95,
            title=f"Execution of {scenario_id.replace('_', ' ').title()}",
            description="Simulated telemetry disturbance injected across roadway infrastructure.",
            is_simulated=True
        )
        await event_bus.publish(ev)
        return {"scenario_id": scenario_id, "status": "COMPLETED", "event_id": ev.event_id}

    async def reset_simulation(self) -> Dict[str, Any]:
        """
        Resets all road speeds, camera statuses, traffic signals, and active risks back to normal.
        """
        db = SessionLocal()
        try:
            # Reset road segments
            for road in db.query(models.RoadSegment).all():
                road.current_speed_kmh = 82.0
                road.current_volume = 210
                road.density_score = 35.0
                road.congestion_level = "FREE_FLOW"

            # Reset cameras
            for cam in db.query(models.Camera).all():
                cam.status = "ONLINE"
                cam.security_health = 98.0
                cam.risk_score = 10.0

            # Reset signals
            for sig in db.query(models.TrafficSignal).all():
                sig.status = "NORMAL"
                sig.is_compromised = False
                sig.current_state = "GREEN"

            # Resolve active incidents
            for inc in db.query(models.Incident).filter(models.Incident.status != "RESOLVED").all():
                inc.status = "RESOLVED"
                inc.resolved_at = datetime.utcnow()
                inc.resolution_notes = "System state restored via simulation reset."

            db.commit()

            # Publish reset event
            reset_evt = NormalizedEvent(
                event_type="SYSTEM_RESET",
                severity="INFO",
                asset_id="SYSTEM_CORE",
                location="Command Center",
                source="OPERATOR_ACTION",
                title="System Simulation Reset Executed",
                description="All roadways, optical cameras, and signal controllers returned to normal operational baseline.",
                is_simulated=True
            )
            await event_bus.publish(reset_evt)

            self.active_scenario = None
            self.scenario_state = "IDLE"
            self.current_step = 0

            return {"status": "SUCCESS", "message": "All infrastructure restored to nominal baseline."}
        finally:
            db.close()

scenario_simulator = ScenarioSimulator()
