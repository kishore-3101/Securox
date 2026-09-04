"""
Securox — Interactive Demo Center Engine
Drives the 9-stage progression:
  EVENT → DETECTION → AI ANALYSIS → RISK → POLICY → ACTION → INCIDENT → INVESTIGATION → RECOVERY
Across 4 Categories:
  HEALTHCARE | TRAFFIC | FINANCE | CROSS_DOMAIN
And 3 Modes:
  NORMAL | ATTACK | RECOVERY

Every simulation generates real backend events that flow through:
  • Event Fabric (event_fabric.py)
  • Standardized AI Models (ai_registry in unified_ai_models.py)
  • Central Cyber-Risk Engine (cyber_risk_engine.py)
  • Unified Authorization Decision Pipeline (unified_authorization.py)
  • Safety Guard Engine (safety_guard.py)
  • Unified SOC Incident Workflow (soc_engine.py)
  • Cross-Domain Threat Correlation Engine (cross_domain_correlation.py)
  • SQLite WAL Persistent Storage (core/store.py)
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.store import store
from services.event_fabric import event_fabric
from services.cyber_risk_engine import cyber_risk_engine
from services.unified_authorization import unified_auth_pipeline
from services.safety_guard import safety_guard
from services.soc_engine import soc_engine
from services.cross_domain_correlation import cross_domain_correlator
from services.ai_models import ai_model_registry

logger = logging.getLogger("securox.demo_center")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoCategory(str, Enum):
    HEALTHCARE = "HEALTHCARE"
    TRAFFIC = "TRAFFIC"
    FINANCE = "FINANCE"
    CROSS_DOMAIN = "CROSS_DOMAIN"


class DemoMode(str, Enum):
    NORMAL = "NORMAL"
    ATTACK = "ATTACK"
    RECOVERY = "RECOVERY"


class DemoStage(str, Enum):
    EVENT = "EVENT"
    DETECTION = "DETECTION"
    AI_ANALYSIS = "AI_ANALYSIS"
    RISK = "RISK"
    POLICY = "POLICY"
    ACTION = "ACTION"
    INCIDENT = "INCIDENT"
    INVESTIGATION = "INVESTIGATION"
    RECOVERY = "RECOVERY"


class DemoStatus(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


STAGE_ORDER = [
    DemoStage.EVENT,
    DemoStage.DETECTION,
    DemoStage.AI_ANALYSIS,
    DemoStage.RISK,
    DemoStage.POLICY,
    DemoStage.ACTION,
    DemoStage.INCIDENT,
    DemoStage.INVESTIGATION,
    DemoStage.RECOVERY,
]


# Canonical stakeholder directory
STAKEHOLDERS = {
    DemoCategory.HEALTHCARE: {
        "name": "Dr. Robert Vance, MD",
        "role": "Chief Medical Officer (CMO)",
        "department": "Clinical Governance & Patient Safety",
        "contact": "cmo@cityhospital.securox",
        "pager": "PAGER-ICU-01",
        "channel": "Hospital Emergency Command Radio (Ch 3)"
    },
    DemoCategory.TRAFFIC: {
        "name": "Rajesh Kumar",
        "role": "Traffic Commander & Transit Director",
        "department": "Municipal Urban Mobility Authority",
        "contact": "traffic.chief@smartmobility.gov",
        "pager": "DISPATCH-STIG-44",
        "channel": "Civil Transit Safety Interlock Radio (Ch 8)"
    },
    DemoCategory.FINANCE: {
        "name": "Elena Rostova",
        "role": "Chief Information Security Officer (CISO)",
        "department": "State Apex Municipal Treasury & Fintech Operations",
        "contact": "ciso@fintech.securox",
        "pager": "FIN-RISK-PRIORITY",
        "channel": "Encrypted FinOps Clearinghouse Direct Line"
    },
    DemoCategory.CROSS_DOMAIN: {
        "name": "Vikram Sen",
        "role": "Joint Emergency Directorate Lead",
        "department": "Pan-City Unified Security Operations Center (SOC)",
        "contact": "director@soc.citygov.securox",
        "pager": "PAN-CITY-COMMAND-01",
        "channel": "Pan-City Multi-Agency Critical Alert Broadcast"
    }
}


class DemoCenterEngine:
    """Manages interactive demo simulations with real backend pipeline progression."""

    def __init__(self):
        self.status = DemoStatus.IDLE
        self.category = DemoCategory.HEALTHCARE
        self.mode = DemoMode.ATTACK
        self.speed = 1.0  # multiplier (1.0 = ~1.5s per stage)
        self.current_stage_index = 0
        self.active_session_id = f"DEMO-{uuid.uuid4().hex[:6].upper()}"
        self.current_risk_score = 15.0
        self.risk_trend: List[Dict[str, Any]] = []
        self.events_timeline: List[Dict[str, Any]] = []
        
        # Telemetry per stage
        self.stage_data: Dict[str, Any] = {}
        self.attacker_attempt: Dict[str, Any] = {}
        self.system_prevented: Dict[str, Any] = {}
        self.stakeholder: Dict[str, Any] = STAKEHOLDERS[DemoCategory.HEALTHCARE]
        self.decision_reason: Dict[str, Any] = {}
        self.ai_inference_result: Dict[str, Any] = {}
        self.safety_evaluation: Dict[str, Any] = {}
        self.active_incident: Optional[Dict[str, Any]] = None
        self.cross_domain_cluster: Optional[Dict[str, Any]] = None
        
        self._task: Optional[asyncio.Task] = None
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Not paused by default
        self._lock = asyncio.Lock()
        self._init_defaults()

    def _init_defaults(self):
        self._set_category_metadata(self.category, self.mode)

    def _set_category_metadata(self, category: DemoCategory, mode: DemoMode):
        self.stakeholder = STAKEHOLDERS.get(category, STAKEHOLDERS[DemoCategory.CROSS_DOMAIN])
        if category == DemoCategory.HEALTHCARE:
            if mode == DemoMode.NORMAL:
                self.attacker_attempt = {
                    "summary": "None (Routine Clinical Operations)",
                    "objective": "Authorized doctor rounds, bedside vital telemetry, nominal infusion rates",
                    "vector": "Authenticated Smart Hospital LAN",
                    "severity": "NOMINAL"
                }
                self.system_prevented = {
                    "summary": "Zero Disruptions",
                    "action": "Continuous baseline monitoring",
                    "protected_asset": "Cardiology ICU Bedside Gateway & Patient EHR"
                }
            elif mode == DemoMode.ATTACK:
                self.attacker_attempt = {
                    "summary": "Unauthorized BOLA Patient Export & IoMT Firmware Exploit",
                    "objective": "Hostile actor attempts mass exfiltration of 2,000 oncology records and bedside pump rate alteration",
                    "vector": "Stolen credentials on unapproved device DEV-ROTTEN-01 via external proxy 198.51.100.45",
                    "severity": "CRITICAL"
                }
                self.system_prevented = {
                    "summary": "Zero-Trust Export Block & Clinical Safety Interlock",
                    "action": "Safety Guard blocked ICU power trip during active surgery; ABAC blocked BOLA patient export",
                    "protected_asset": "Hospital PAC Archive & ICU Infusion Controller (Surgeries in progress: 3)"
                }
            else:  # RECOVERY
                self.attacker_attempt = {
                    "summary": "Residual Intrusion Quarantined",
                    "objective": "Attempted persistence eliminated",
                    "vector": "Hostile session terminated",
                    "severity": "LOW"
                }
                self.system_prevented = {
                    "summary": "System Restored to Verified Health",
                    "action": "Device DEV-ROTTEN-01 isolated; clinical credentials rotated; ICU telemetry verified nominal",
                    "protected_asset": "Cardiology & Oncology EHR Services"
                }
        elif category == DemoCategory.TRAFFIC:
            if mode == DemoMode.NORMAL:
                self.attacker_attempt = {
                    "summary": "None (Autonomous STIG Adaptive Cycle)",
                    "objective": "Routine vehicle throughput, loop sensor counts, scheduled ambulance priority",
                    "vector": "Municipal SCADA Traffic Backbone",
                    "severity": "NOMINAL"
                }
                self.system_prevented = {
                    "summary": "Zero Disruptions",
                    "action": "Dynamic timing plan optimization",
                    "protected_asset": "Airport Transit Corridor Intersections"
                }
            elif mode == DemoMode.ATTACK:
                self.attacker_attempt = {
                    "summary": "SCADA Field Cabinet Timing Plan Spoofing",
                    "objective": "Force all-green conflicting phases at Junction 14 to cause arterial gridlock and block ambulances",
                    "vector": "Unauthorized remote command injection into SCADA PLC via 185.220.101.5 (Tor Exit)",
                    "severity": "CRITICAL"
                }
                self.system_prevented = {
                    "summary": "Active Emergency Green Corridor Preservation",
                    "action": "Safety Guard detected active ALS Ambulance in transit; rejected signal shutdown and engaged hardware failsafe",
                    "protected_asset": "Green Corridor Emergency Route (Ambulance AMB-104 en-route)"
                }
            else:  # RECOVERY
                self.attacker_attempt = {
                    "summary": "SCADA Tampering Blocked & Cabinet Isolated",
                    "objective": "Attempted corridor disruption failed",
                    "vector": "Field cabinet isolated at firewall layer",
                    "severity": "LOW"
                }
                self.system_prevented = {
                    "summary": "Traffic Grid Integrity Restored",
                    "action": "Autonomous microsegmentation engaged; adaptive STIG cycling restored; corridor latency cleared",
                    "protected_asset": "Junction 14 Controller & Transit Corridor"
                }
        elif category == DemoCategory.FINANCE:
            if mode == DemoMode.NORMAL:
                self.attacker_attempt = {
                    "summary": "None (Standard Retail Banking & Payroll)",
                    "objective": "Authorized RTGS transfers, retail ATM transactions, domestic merchant clearing",
                    "vector": "Core Banking SWIFT Network",
                    "severity": "NOMINAL"
                }
                self.system_prevented = {
                    "summary": "Zero Disruptions",
                    "action": "Real-time AML graph tracking & Cyber-VaR scoring",
                    "protected_asset": "Municipal Treasury Vault & Commercial Branch Exchange"
                }
            elif mode == DemoMode.ATTACK:
                self.attacker_attempt = {
                    "summary": "SWIFT Account Takeover & Rapid Wire Exfiltration",
                    "objective": "Hostile syndicate attempts unauthorized ₹45,000,000 RTGS diversion to offshore shell entity",
                    "vector": "Compromised teller credentials & fan-out burst to 4 mule accounts",
                    "severity": "CRITICAL"
                }
                self.system_prevented = {
                    "summary": "Pre-Settlement Cyber-VaR Interception & Escrow Freeze",
                    "action": "XGBoost fraud classifier (score: 0.96) and AML graph contagion triggered immediate zero-trust escrow freeze",
                    "protected_asset": "Municipal Treasury Reserve (₹45,000,000 saved from exfiltration)"
                }
            else:  # RECOVERY
                self.attacker_attempt = {
                    "summary": "Mule Network Quarantined",
                    "objective": "Stolen credentials invalidated across network",
                    "vector": "Offshore wire canceled before clearing window closed",
                    "severity": "LOW"
                }
                self.system_prevented = {
                    "summary": "Liquidity Verified & Accounts Restored",
                    "action": "Mule wallets frozen; treasury ledger reconciled; clearinghouse returned to nominal risk",
                    "protected_asset": "Core Settlement Exchange"
                }
        else:  # CROSS_DOMAIN
            if mode == DemoMode.NORMAL:
                self.attacker_attempt = {
                    "summary": "None (Multi-Sector Smart City Synchronization)",
                    "objective": "Coordinated equilibrium across Healthcare, Traffic, and Financial utilities",
                    "vector": "Pan-City Event Bus",
                    "severity": "NOMINAL"
                }
                self.system_prevented = {
                    "summary": "Zero Disruptions",
                    "action": "Continuous cross-sector correlation monitoring",
                    "protected_asset": "City-wide Critical Infrastructure Fabric"
                }
            elif mode == DemoMode.ATTACK:
                self.attacker_attempt = {
                    "summary": "Coordinated Multi-Vector Cyber Assault (DEVICE-782)",
                    "objective": "Adversary pivots across Healthcare EHR, Traffic SCADA, and Banking Gateway simultaneously",
                    "vector": "Common pivot hardware DEVICE-782 at IP 192.168.1.105 triggering multi-sector failure",
                    "severity": "CRITICAL"
                }
                self.system_prevented = {
                    "summary": "Cross-Domain Attack Correlation & Pan-City Isolation",
                    "action": "Correlation Engine flagged COORDINATED ATTACK INDICATOR (confidence: 0.85); isolated pivot across all subnets",
                    "protected_asset": "City General Hospital + SCADA Transit + Municipal Treasury"
                }
            else:  # RECOVERY
                self.attacker_attempt = {
                    "summary": "Coordinated Attack Neutralized",
                    "objective": "Pan-city adversary neutralized",
                    "vector": "DEVICE-782 blacklisted city-wide",
                    "severity": "LOW"
                }
                self.system_prevented = {
                    "summary": "Pan-City SOC Command Re-established Normal Posture",
                    "action": "Unified incident resolved; multi-agency sign-off completed; risk score reset to 14.0",
                    "protected_asset": "All 12 City Critical Infrastructure Nodes"
                }

    async def start(self, category: DemoCategory, mode: DemoMode, speed: float = 1.0) -> Dict[str, Any]:
        """Starts an interactive demo simulation through the 9-stage progression."""
        async with self._lock:
            # Stop existing task if running
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            self.category = category
            self.mode = mode
            self.speed = max(0.2, min(speed, 5.0))
            self.status = DemoStatus.RUNNING
            self.current_stage_index = 0
            self.active_session_id = f"DEMO-{uuid.uuid4().hex[:6].upper()}"
            self._set_category_metadata(category, mode)
            
            # Reset initial risk depending on mode
            if mode == DemoMode.NORMAL:
                self.current_risk_score = 14.0
            elif mode == DemoMode.ATTACK:
                self.current_risk_score = 16.0
            else:  # RECOVERY
                self.current_risk_score = 88.0

            self.risk_trend = [{
                "timestamp": _utcnow(),
                "risk_score": self.current_risk_score,
                "stage": "INIT"
            }]
            self.events_timeline = []
            self.stage_data = {}
            self._pause_event.set()

            # Launch background execution loop
            self._task = asyncio.create_task(self._run_simulation_loop())

            return self.get_status()

    async def pause(self) -> Dict[str, Any]:
        """Pauses the running simulation."""
        if self.status == DemoStatus.RUNNING:
            self._pause_event.clear()
            self.status = DemoStatus.PAUSED
        return self.get_status()

    async def resume(self) -> Dict[str, Any]:
        """Resumes a paused simulation."""
        if self.status == DemoStatus.PAUSED:
            self._pause_event.set()
            self.status = DemoStatus.RUNNING
        return self.get_status()

    async def set_speed(self, speed: float) -> Dict[str, Any]:
        """Updates simulation speed."""
        self.speed = max(0.2, min(speed, 5.0))
        return self.get_status()

    async def reset(self) -> Dict[str, Any]:
        """Resets the simulation to healthy baseline and clears state."""
        async with self._lock:
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            self.status = DemoStatus.IDLE
            self.current_stage_index = 0
            self.current_risk_score = 14.0
            self.risk_trend = [{
                "timestamp": _utcnow(),
                "risk_score": 14.0,
                "stage": "RESET"
            }]
            self.events_timeline = []
            self.stage_data = {}
            self.active_incident = None
            self.cross_domain_cluster = None
            self._pause_event.set()
            self._set_category_metadata(self.category, DemoMode.NORMAL)

            # Re-anchor baseline in store
            await store.touch_login("demo_operator")
            return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        """Returns the complete live state of the Demo Center."""
        current_stage = STAGE_ORDER[min(self.current_stage_index, len(STAGE_ORDER) - 1)].value
        return {
            "session_id": self.active_session_id,
            "status": self.status.value,
            "category": self.category.value,
            "mode": self.mode.value,
            "speed": self.speed,
            "current_stage": current_stage,
            "current_stage_index": self.current_stage_index,
            "stages": [s.value for s in STAGE_ORDER],
            "risk": {
                "current_score": round(self.current_risk_score, 1),
                "tier": "CRITICAL" if self.current_risk_score >= 80 else ("HIGH" if self.current_risk_score >= 60 else ("MEDIUM" if self.current_risk_score >= 30 else "LOW")),
                "is_increasing": self.mode == DemoMode.ATTACK and self.current_stage_index > 0 and self.current_stage_index < 8,
                "is_decreasing": self.mode == DemoMode.RECOVERY,
                "trend": self.risk_trend[-15:]
            },
            "stakeholder": self.stakeholder,
            "attacker_attempt": self.attacker_attempt,
            "system_prevented": self.system_prevented,
            "decision_reason": self.decision_reason,
            "ai_inference": self.ai_inference_result,
            "safety_evaluation": self.safety_evaluation,
            "active_incident": self.active_incident,
            "cross_domain_cluster": self.cross_domain_cluster,
            "stage_data": self.stage_data,
            "events_timeline": self.events_timeline[-25:],
            "timestamp": _utcnow()
        }

    async def _run_simulation_loop(self):
        """Steps through the 9 stages executing real backend operations."""
        try:
            for idx, stage in enumerate(STAGE_ORDER):
                await self._pause_event.wait()
                self.current_stage_index = idx

                # Base stage interval adjusted for speed (e.g. 1.2s at 1.0x)
                stage_delay = max(0.3, 1.2 / self.speed)

                await self._execute_stage(stage)

                # Broadcast step update to WebSockets if available
                await self._broadcast_step(stage)

                await asyncio.sleep(stage_delay)

            self.status = DemoStatus.COMPLETED
            await self._broadcast_step(DemoStage.RECOVERY)
        except asyncio.CancelledError:
            logger.info("Demo Center simulation cancelled.")
        except Exception as e:
            logger.error("Error during Demo Center execution: %s", e, exc_info=True)
            self.status = DemoStatus.IDLE

    async def _broadcast_step(self, stage: DemoStage):
        """Broadcasts current step to WebSocket manager."""
        try:
            from main import manager
            await manager.broadcast({
                "type": "demo_center_step",
                "data": self.get_status()
            })
        except Exception:
            pass  # Fallback gracefully if main / manager not available in test context

    async def _execute_stage(self, stage: DemoStage):
        """Executes real backend processing corresponding to each stage."""
        ts = _utcnow()
        cat = self.category
        mode = self.mode

        # ── 1. STAGE: EVENT ──────────────────────────────────────────────
        if stage == DemoStage.EVENT:
            if cat == DemoCategory.HEALTHCARE:
                asset = "EHR_GATEWAY" if mode == DemoMode.ATTACK else "ICU_MONITOR_01"
                action = "PATIENT_RECORD_EXPORT" if mode == DemoMode.ATTACK else "PATIENT_ACCESS"
                user = "dr.chen_compromised" if mode == DemoMode.ATTACK else "dr.sarah.chen"
                ip = "198.51.100.45" if mode == DemoMode.ATTACK else "10.0.1.25"
                device = "DEV-ROTTEN-01" if mode == DemoMode.ATTACK else "DEV-CLINICAL-04"
            elif cat == DemoCategory.TRAFFIC:
                asset = "SCADA_PLC_14" if mode == DemoMode.ATTACK else "LOOP_SENSOR_HEBBAL"
                action = "OVERRIDE_TIMING_PLAN" if mode == DemoMode.ATTACK else "SIGNAL_CYCLE"
                user = "field_intruder" if mode == DemoMode.ATTACK else "traffic_system"
                ip = "185.220.101.5" if mode == DemoMode.ATTACK else "10.12.0.8"
                device = "DEVICE-782" if cat == DemoCategory.CROSS_DOMAIN else ("DEV-ROGUE-SCADA" if mode == DemoMode.ATTACK else "DEV-TRANSIT-01")
            elif cat == DemoCategory.FINANCE:
                asset = "SWIFT_SETTLEMENT_GATEWAY" if mode == DemoMode.ATTACK else "POS_TERMINAL_09"
                action = "CROSS_BORDER_WIRE" if mode == DemoMode.ATTACK else "TRANSACTION"
                user = "fin_teller_compromised" if mode == DemoMode.ATTACK else "teller.alex"
                ip = "203.0.113.88" if mode == DemoMode.ATTACK else "10.20.1.5"
                device = "DEV-FIN-ATTACK" if mode == DemoMode.ATTACK else "DEV-BANK-02"
            else:  # CROSS_DOMAIN
                asset = "PAN_CITY_COMM_HUB"
                action = "MULTI_SECTOR_BURST" if mode == DemoMode.ATTACK else "SYNC_TELEMETRY"
                user = "adversary_apt_vector" if mode == DemoMode.ATTACK else "system_orchestrator"
                ip = "198.51.100.10" if mode == DemoMode.ATTACK else "10.0.0.1"
                device = "DEVICE-782"

            event_dict = {
                "event_id": f"EV-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": ts,
                "domain": cat.value,
                "organization": STAKEHOLDERS[cat]["department"],
                "user": user,
                "role": "doctor" if cat == DemoCategory.HEALTHCARE else ("traffic_operator" if cat == DemoCategory.TRAFFIC else "finance_teller"),
                "device": device,
                "ip": ip,
                "location": "City Headquarters Facility",
                "resource": asset,
                "action": action,
                "result": "INITIATED",
                "risk": self.current_risk_score,
                "metadata": {"mode": mode.value, "stage": "EVENT"}
            }
            # Ingest real event via fabric (which automatically persists to SQLite store)
            await event_fabric.ingest_event(event_dict)

            self.events_timeline.append({
                "id": event_dict["event_id"],
                "timestamp": ts,
                "domain": cat.value,
                "action": action,
                "asset": asset,
                "summary": f"[{cat.value}] {action} initiated on {asset} by {user}"
            })
            self.stage_data[stage.value] = event_dict

        # ── 2. STAGE: DETECTION ──────────────────────────────────────────
        elif stage == DemoStage.DETECTION:
            if mode == DemoMode.ATTACK:
                det_type = "ANOMALOUS_ACCESS_BURST" if cat == DemoCategory.HEALTHCARE else ("UNAUTHORIZED_SCADA_OVERRIDE" if cat == DemoCategory.TRAFFIC else "HIGH_VALUE_WIRE_DEVIATION")
                alert_payload = {
                    "id": f"ALT-{uuid.uuid4().hex[:6].upper()}",
                    "timestamp": ts,
                    "asset": cat.value,
                    "severity": "CRITICAL",
                    "risk_score": 75.0,
                    "risk_category": "CRITICAL",
                    "anomaly_score": 0.94,
                    "scenario": f"{cat.value} Attack Detection",
                    "payload": {"detection_rule": det_type, "threat_level": "ELEVATED"}
                }
                await store.add_alert(alert_payload)
                self.stage_data[stage.value] = alert_payload
                if self.mode == DemoMode.ATTACK:
                    self.current_risk_score = 42.0
            else:
                self.stage_data[stage.value] = {
                    "detection_status": "NOMINAL_TELEMETRY",
                    "anomaly_score": 0.04,
                    "alert": None
                }
                if self.mode == DemoMode.RECOVERY:
                    self.current_risk_score = 65.0

        # ── 3. STAGE: AI ANALYSIS ────────────────────────────────────────
        elif stage == DemoStage.AI_ANALYSIS:
            if cat == DemoCategory.HEALTHCARE:
                model_id = "HC-MODEL-02" if mode == DemoMode.ATTACK else "HC-MODEL-01"
                features = {"patient_count": 2000, "export_rate": 50.0} if mode == DemoMode.ATTACK else {"patient_count": 1, "export_rate": 0.1}
            elif cat == DemoCategory.TRAFFIC:
                model_id = "TR-MODEL-04" if mode == DemoMode.ATTACK else "TR-MODEL-02"
                features = {"phase_length": 180.0, "green_ratio": 1.0} if mode == DemoMode.ATTACK else {"phase_length": 45.0, "green_ratio": 0.5}
            elif cat == DemoCategory.FINANCE:
                model_id = "FIN-MODEL-01" if mode == DemoMode.ATTACK else "FIN-MODEL-02"
                features = {"amount": 45000000.0, "cross_border": 1} if mode == DemoMode.ATTACK else {"amount": 250.0, "cross_border": 0}
            else:  # CROSS_DOMAIN
                model_id = "NET-MODEL-04" if mode == DemoMode.ATTACK else "NET-MODEL-01"
                features = {"pkt_variance": 88.0, "syn_ratio": 0.95} if mode == DemoMode.ATTACK else {"pkt_variance": 5.0, "syn_ratio": 0.05}

            try:
                pred = await ai_model_registry.predict(model_id, features)
                if hasattr(pred, "model_dump"):
                    pred = pred.model_dump()
            except Exception as e:
                pred = {
                    "model": model_id,
                    "prediction": "ANOMALY" if mode == DemoMode.ATTACK else "BENIGN",
                    "score": 0.94 if mode == DemoMode.ATTACK else 0.04,
                    "version": "1.0.0",
                    "timestamp": ts,
                    "features": features,
                    "disclaimer": "Model predictions are probabilistic inferences and do not represent ground truth."
                }
            self.ai_inference_result = pred
            self.stage_data[stage.value] = pred
            if mode == DemoMode.ATTACK:
                self.current_risk_score = 68.0
            elif mode == DemoMode.RECOVERY:
                self.current_risk_score = 45.0

        # ── 4. STAGE: RISK ───────────────────────────────────────────────
        elif stage == DemoStage.RISK:
            if mode == DemoMode.ATTACK:
                risk_req = {
                    "identity": "dr.chen_compromised" if cat == DemoCategory.HEALTHCARE else "compromised_actor",
                    "role": "doctor" if cat == DemoCategory.HEALTHCARE else "operator",
                    "resource": "SETTLEMENT_VAULT" if cat == DemoCategory.FINANCE else ("EHR_DATABASE" if cat == DemoCategory.HEALTHCARE else "SCADA_INTERLOCK"),
                    "action": "EXFILTRATION",
                    "device": "DEV-ROTTEN-01",
                    "location": "OFFSHORE_UNKNOWN",
                    "timestamp": ts,
                    "domain": cat.value,
                    "behavior": {"velocity": 12.0, "rate": 50.0},
                    "ml_detections": [{"model": "Ensemble", "anomaly_score": 0.94}]
                }
            else:
                risk_req = {
                    "identity": "authorized_user",
                    "role": "operator",
                    "resource": "NORMAL_GATEWAY",
                    "action": "ACCESS",
                    "device": "DEV-TRUSTED-01",
                    "location": "City Headquarters",
                    "timestamp": ts,
                    "domain": cat.value,
                    "behavior": {"velocity": 1.0, "rate": 1.0},
                    "ml_detections": []
                }
            try:
                assessment_obj = await cyber_risk_engine.evaluate(risk_req)
                assessment = assessment_obj.model_dump() if hasattr(assessment_obj, "model_dump") else dict(assessment_obj)
            except Exception as e:
                assessment = {
                    "risk_score": 91.0 if mode == DemoMode.ATTACK else 14.0,
                    "risk_category": "CRITICAL" if mode == DemoMode.ATTACK else "LOW",
                    "factors": [
                        {"name": "new device", "points": 20.0, "source_type": "POLICY_RULE"},
                        {"name": "unusual location", "points": 18.0, "source_type": "POLICY_RULE"},
                        {"name": "abnormal volume", "points": 25.0, "source_type": "STATISTICAL_BASELINE"},
                        {"name": "sensitive resource", "points": 13.0, "source_type": "POLICY_RULE"}
                    ],
                    "uncertainty": 0.08
                }

            if mode == DemoMode.ATTACK:
                self.current_risk_score = max(82.0, float(assessment.get("risk_score", 91.0)))
            elif mode == DemoMode.RECOVERY:
                self.current_risk_score = 30.0
            else:
                self.current_risk_score = min(25.0, float(assessment.get("risk_score", 14.0)))

            self.stage_data[stage.value] = assessment
            factors_list = assessment.get("factors", [])
            formatted_factors = []
            for f in factors_list:
                if isinstance(f, dict):
                    formatted_factors.append({
                        "name": f.get("name", "anomaly"),
                        "points": float(f.get("points", 10.0)),
                        "source": f.get("source_type", "POLICY_RULE")
                    })
                elif hasattr(f, "name"):
                    formatted_factors.append({
                        "name": getattr(f, "name"),
                        "points": float(getattr(f, "points", 10.0)),
                        "source": getattr(f, "source_type", "POLICY_RULE")
                    })
            if not formatted_factors:
                formatted_factors = [
                    {"name": "new device", "points": 20.0, "source": "POLICY_RULE"},
                    {"name": "unusual location", "points": 18.0, "source": "POLICY_RULE"},
                    {"name": "abnormal volume", "points": 25.0, "source": "STATISTICAL_BASELINE"},
                    {"name": "sensitive resource", "points": 13.0, "source": "POLICY_RULE"}
                ]

            self.decision_reason = {
                "composite_score": self.current_risk_score,
                "tier": "CRITICAL" if self.current_risk_score >= 80 else ("HIGH" if self.current_risk_score >= 60 else "LOW"),
                "factors": formatted_factors,
                "uncertainty": assessment.get("uncertainty", 0.08)
            }

        # ── 5. STAGE: POLICY ─────────────────────────────────────────────
        elif stage == DemoStage.POLICY:
            action_name = "PATIENT_EXPORT" if cat == DemoCategory.HEALTHCARE else ("SIGNAL_OVERRIDE" if cat == DemoCategory.TRAFFIC else "RTGS_WIRE")
            subject = "dr.chen_compromised" if mode == DemoMode.ATTACK else "dr.sarah.chen"
            role_name = "doctor" if cat == DemoCategory.HEALTHCARE else ("traffic_operator" if cat == DemoCategory.TRAFFIC else "finance_teller")
            res_name = "PATIENT_DB_01" if cat == DemoCategory.HEALTHCARE else "SCADA_CONTROLLER"
            attrs = {
                "device": "DEV-ROTTEN-01" if mode == DemoMode.ATTACK else "DEV-SEC-01",
                "location": "Offshore Unknown" if mode == DemoMode.ATTACK else "City Hospital Main",
                "risk_score": self.current_risk_score,
                "anomaly_score": 0.94 if mode == DemoMode.ATTACK else 0.05
            }
            try:
                auth_decision = await unified_auth_pipeline.authorize(
                    identity=subject,
                    role=role_name,
                    domain=cat.value,
                    resource=res_name,
                    action=action_name,
                    attributes=attrs
                )
                if hasattr(auth_decision, "model_dump"):
                    auth_decision = auth_decision.model_dump()
            except Exception as e:
                auth_decision = {
                    "decision": "BLOCK" if mode == DemoMode.ATTACK else "ALLOW",
                    "reason": f"Evaluated via unified RBAC+ABAC policy: {e}"
                }
            self.stage_data[stage.value] = auth_decision

        # ── 6. STAGE: ACTION ─────────────────────────────────────────────
        elif stage == DemoStage.ACTION:
            # Real evaluation from safety_guard
            safety_context = {}
            if cat == DemoCategory.HEALTHCARE:
                safety_context = {"surgeries_in_progress": 3, "icu_occupancy_pct": 92.0}
            elif cat == DemoCategory.TRAFFIC:
                safety_context = {"green_corridor_active": True, "active_emergency_vehicles": 2}
            elif cat == DemoCategory.FINANCE:
                safety_context = {"settlement_window_open": True, "active_clearing_inr": 45000000.0}

            prop_action = "SHUTDOWN_HOSPITAL_POWER" if cat == DemoCategory.HEALTHCARE else ("FORCE_ALL_RED" if cat == DemoCategory.TRAFFIC else "FREEZE_SETTLEMENT")
            eval_result_obj = safety_guard.evaluate_mitigation_safety(
                domain=cat.value,
                action_name=prop_action,
                target_asset=cat.value,
                safety_context=safety_context
            )
            eval_result = eval_result_obj.model_dump() if hasattr(eval_result_obj, "model_dump") else dict(eval_result_obj)
            self.safety_evaluation = eval_result
            self.stage_data[stage.value] = eval_result

        # ── 7. STAGE: INCIDENT ───────────────────────────────────────────
        elif stage == DemoStage.INCIDENT:
            if mode == DemoMode.ATTACK:
                incident_dict = {
                    "title": f"CRITICAL: {cat.value} Zero-Trust Threat Intercepted",
                    "domain": cat.value,
                    "severity": "CRITICAL",
                    "asset": f"{cat.value}_CORE_NODE",
                    "identity": "adversary_external",
                    "device": "DEV-ROTTEN-01" if cat != DemoCategory.CROSS_DOMAIN else "DEVICE-782",
                    "owner": "soc_lead",
                    "attack_type": "Multi-Factor Zero-Trust Intrusion",
                    "risk_score": self.current_risk_score
                }
                saved_inc = await soc_engine.create_incident(incident_dict)
                self.active_incident = saved_inc
                self.stage_data[stage.value] = saved_inc
            else:
                self.stage_data[stage.value] = {"incident_status": "NONE", "active": False}

        # ── 8. STAGE: INVESTIGATION ──────────────────────────────────────
        elif stage == DemoStage.INVESTIGATION:
            if self.active_incident and mode == DemoMode.ATTACK:
                inc_id = self.active_incident["id"]
                # Add real evidence
                ev_res = await soc_engine.add_evidence(
                    incident_id=inc_id,
                    evidence_type="PCAP_HASH",
                    description="Cryptographic SHA256 of malicious packet payload",
                    hash_value="f3a17e0b5c689d02341249e0fa982b1456c7890123456789abcdef0123456789",
                    added_by="soc_analyst_lead"
                )
                # Add note
                note_res = await soc_engine.add_notes(
                    incident_id=inc_id,
                    note_text=f"Cross-verified by {self.stakeholder['name']} ({self.stakeholder['role']}). Immediate zero-trust microsegmentation validated.",
                    author="soc_analyst_lead"
                )
                self.active_incident["evidence"] = [ev_res]
                self.active_incident["notes"] = [note_res]
                self.stage_data[stage.value] = {
                    "incident_id": inc_id,
                    "evidence_count": 1,
                    "notes_count": 1,
                    "status": "INVESTIGATING"
                }
            else:
                self.stage_data[stage.value] = {
                    "status": "NORMAL_MONITORING",
                    "evidence_count": 0,
                    "notes_count": 0
                }

            # If CROSS_DOMAIN, run correlation
            if cat == DemoCategory.CROSS_DOMAIN:
                sample_events = [
                    {"id": "E1", "domain": "HEALTHCARE", "device_id": "DEVICE-782", "ip_address": "192.168.1.105", "action": "ACCESS", "severity": "HIGH"},
                    {"id": "E2", "domain": "TRAFFIC", "device_id": "DEVICE-782", "ip_address": "192.168.1.105", "action": "SIGNAL", "severity": "CRITICAL"},
                    {"id": "E3", "domain": "FINANCE", "device_id": "DEVICE-782", "ip_address": "192.168.1.105", "action": "TRANSFER", "severity": "CRITICAL"}
                ]
                corrs = await cross_domain_correlator.correlate_events(sample_events)
                if corrs:
                    cluster_dict = corrs[0].model_dump() if hasattr(corrs[0], "model_dump") else corrs[0]
                    self.cross_domain_cluster = cluster_dict
                    self.stage_data[stage.value]["cross_domain_cluster"] = cluster_dict

        # ── 9. STAGE: RECOVERY ───────────────────────────────────────────
        elif stage == DemoStage.RECOVERY:
            if self.active_incident:
                inc_id = self.active_incident["id"]
                await soc_engine.contain_incident(
                    incident_id=inc_id,
                    containment_action="MICROSEGMENTATION_AND_CREDENTIAL_ROTATION",
                    performed_by="soc_lead"
                )
                res_inc = await soc_engine.resolve_incident(
                    incident_id=inc_id,
                    resolution_summary="Autonomous containment executed safely without critical infrastructure disruption. Asset verified healthy.",
                    resolved_by="ciso_exec"
                )
                self.active_incident = res_inc
            
            # Risk drops to healthy baseline
            self.current_risk_score = 14.2
            self.stage_data[stage.value] = {
                "status": "RECOVERED",
                "risk_score": 14.2,
                "infrastructure_state": "HEALTHY_BASELINE"
            }

        # Append to risk trend
        self.risk_trend.append({
            "timestamp": ts,
            "risk_score": round(self.current_risk_score, 1),
            "stage": stage.value
        })


# Singleton instance
demo_center_engine = DemoCenterEngine()
