import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CyberThreatDetection(BaseModel):
    threat_id: str = Field(default_factory=lambda: f"THR-{uuid.uuid4().hex[:8].upper()}")
    threat_type: str
    asset_id: str
    location: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.90
    risk_score: float = 80.0
    status: str = "OPEN"  # OPEN, INVESTIGATING, MITIGATED, RESOLVED
    source: str = "CYBER_SENSOR"
    severity: str = "HIGH"  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    description: str

class UserRiskProfile(BaseModel):
    username: str
    risk_score: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    reasons: List[str]
    failed_logins: int
    last_login_ip: str

class CybersecurityEngine:
    def __init__(self):
        self.active_threats: List[CyberThreatDetection] = []
        self.user_failed_attempts: Dict[str, int] = {}
        self.network_flow_log: List[Dict[str, Any]] = []

    def inspect_camera_security(
        self, 
        camera_id: str, 
        location: str,
        failed_auth_attempts: int, 
        heartbeat_jitter_ms: float, 
        firmware_hash: str, 
        expected_firmware_hash: str,
        outbound_bytes_per_sec: float
    ) -> Optional[CyberThreatDetection]:
        # 1. Firmware integrity breach
        if firmware_hash != expected_firmware_hash:
            threat = CyberThreatDetection(
                threat_type="CAMERA_FIRMWARE_TAMPERING",
                asset_id=camera_id,
                location=location,
                confidence=0.98,
                risk_score=95.0,
                severity="CRITICAL",
                source="CAMERA_INTEGRITY_DAEMON",
                description=f"Firmware hash mismatch on {camera_id}. Unauthorized binary replacement suspected.",
                evidence={
                    "reported_hash": firmware_hash,
                    "expected_hash": expected_firmware_hash,
                    "verification": "FAILED"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 2. Brute-force RTSP/ONVIF authentication attack
        if failed_auth_attempts >= 5:
            threat = CyberThreatDetection(
                threat_type="CAMERA_BRUTE_FORCE_AUTH",
                asset_id=camera_id,
                location=location,
                confidence=0.94,
                risk_score=82.0,
                severity="HIGH",
                source="CAMERA_AUTH_MONITOR",
                description=f"{failed_auth_attempts} failed authentication attempts recorded on camera {camera_id} in 60 seconds.",
                evidence={
                    "failed_attempts": failed_auth_attempts,
                    "protocol": "RTSP/ONVIF",
                    "source_subnet": "192.168.10.0/24"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 3. Abnormal outbound exfiltration
        if outbound_bytes_per_sec > 15_000_000:  # > 15 MB/s unexpected outbound
            threat = CyberThreatDetection(
                threat_type="CAMERA_DATA_EXFILTRATION",
                asset_id=camera_id,
                location=location,
                confidence=0.89,
                risk_score=78.0,
                severity="HIGH",
                source="NETWORK_FLOW_ANALYZER",
                description=f"Abnormal outbound traffic surge ({outbound_bytes_per_sec / 1e6:.1f} MB/s) from camera {camera_id} to external endpoint.",
                evidence={
                    "rate_bps": outbound_bytes_per_sec,
                    "destination_ip": "185.220.101.44",
                    "destination_port": 443
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        return None

    def inspect_traffic_signal_security(
        self,
        controller_id: str,
        intersection_id: str,
        location: str,
        command_source_ip: str,
        authorized_ips: List[str],
        cycle_seconds: int,
        conflicting_greens: bool
    ) -> Optional[CyberThreatDetection]:
        # 1. Conflicting Greens (Fatal safety condition)
        if conflicting_greens:
            threat = CyberThreatDetection(
                threat_type="SIGNAL_CONFLICTING_GREEN_PHASES",
                asset_id=controller_id,
                location=location,
                confidence=0.99,
                risk_score=99.0,
                severity="CRITICAL",
                source="SAFETY_MONITORING_DAEMON",
                description=f"CRITICAL SAFETY VIOLATION: Controller {controller_id} at {intersection_id} active green in intersecting conflicting directions.",
                evidence={
                    "controller_id": controller_id,
                    "intersection_id": intersection_id,
                    "safety_interlock": "TRIPPED_TO_FLASHING_RED"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 2. Unauthorized Command from unrecognized IP
        if command_source_ip not in authorized_ips:
            threat = CyberThreatDetection(
                threat_type="UNAUTHORIZED_SIGNAL_COMMAND",
                asset_id=controller_id,
                location=location,
                confidence=0.96,
                risk_score=91.0,
                severity="CRITICAL",
                source="NTCIP_CONTROLLER_IDS",
                description=f"Unauthorized NTCIP command injected into traffic controller {controller_id} from unknown IP {command_source_ip}.",
                evidence={
                    "source_ip": command_source_ip,
                    "protocol": "NTCIP 1202",
                    "action": "FORCE_PHASE_OVERRIDE"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 3. Impossible Cycle Timing (e.g. 5 seconds cycle or 600 seconds hold)
        if cycle_seconds < 15 or cycle_seconds > 300:
            threat = CyberThreatDetection(
                threat_type="SIGNAL_TIMING_MANIPULATION",
                asset_id=controller_id,
                location=location,
                confidence=0.92,
                risk_score=85.0,
                severity="HIGH",
                source="SIGNAL_TIMING_VALIDATOR",
                description=f"Abnormal signal cycle duration ({cycle_seconds}s) configured on controller {controller_id}. Possible timing denial-of-service.",
                evidence={
                    "cycle_duration": cycle_seconds,
                    "allowed_range": "30s - 180s"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        return None

    def inspect_sensor_security(
        self,
        sensor_id: str,
        location: str,
        reading_history: List[float],
        last_timestamp_delta_sec: float
    ) -> Optional[CyberThreatDetection]:
        # 1. Stuck Constant Value (Zero-variance freeze over multiple readings)
        if len(reading_history) >= 8 and len(set(reading_history[-8:])) == 1:
            stuck_val = reading_history[-1]
            threat = CyberThreatDetection(
                threat_type="SENSOR_TELEMETRY_STUCK",
                asset_id=sensor_id,
                location=location,
                confidence=0.95,
                risk_score=72.0,
                severity="MEDIUM",
                source="SENSOR_DATA_QUALITY_ENGINE",
                description=f"Sensor {sensor_id} telemetry stuck at constant value ({stuck_val}) across 8 consecutive poll intervals.",
                evidence={
                    "stuck_value": stuck_val,
                    "consecutive_samples": 8,
                    "variance": 0.0
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 2. Replay-like timestamp or telemetry replay
        if last_timestamp_delta_sec < 0:
            threat = CyberThreatDetection(
                threat_type="SENSOR_REPLAY_ATTACK",
                asset_id=sensor_id,
                location=location,
                confidence=0.93,
                risk_score=88.0,
                severity="HIGH",
                source="TELEMETRY_INTEGRITY_CHECKER",
                description=f"Out-of-order or duplicate timestamp delta ({last_timestamp_delta_sec}s) detected on {sensor_id}. Suspected packet replay.",
                evidence={
                    "timestamp_skew_sec": last_timestamp_delta_sec,
                    "indicator": "NONCE_REUSE"
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        return None

    def inspect_network_traffic(
        self,
        source_ip: str,
        target_ip: str,
        dest_ports: List[int],
        packet_count_per_sec: int,
        protocol: str
    ) -> Optional[CyberThreatDetection]:
        # 1. Port scanning behavior (connecting to multiple distinct ports in rapid succession)
        if len(set(dest_ports)) >= 10:
            threat = CyberThreatDetection(
                threat_type="NETWORK_PORT_SCAN",
                asset_id=f"IP-{source_ip}",
                location="Operational Network Segment (VLAN-20)",
                confidence=0.97,
                risk_score=84.0,
                severity="HIGH",
                source="EDGE_NETWORK_IDS",
                description=f"Port scan reconnaissance detected from {source_ip} targeting OT infrastructure ({len(dest_ports)} ports scanned).",
                evidence={
                    "source_ip": source_ip,
                    "ports_probed": dest_ports[:8],
                    "total_ports": len(dest_ports)
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        # 2. High-volume volumetric flood / connection burst
        if packet_count_per_sec > 5000:
            threat = CyberThreatDetection(
                threat_type="NETWORK_CONNECTION_BURST",
                asset_id=f"IP-{target_ip}",
                location="Core Traffic Gateway",
                confidence=0.91,
                risk_score=80.0,
                severity="HIGH",
                source="TRAFFIC_GATEWAY_FIREWALL",
                description=f"Abnormal connection burst ({packet_count_per_sec} pps) from {source_ip} to {target_ip}. Potential DoS flood.",
                evidence={
                    "packet_rate_pps": packet_count_per_sec,
                    "target_ip": target_ip,
                    "protocol": protocol
                }
            )
            self.active_threats.insert(0, threat)
            return threat

        return None

    def calculate_user_risk(
        self,
        username: str,
        failed_logins: int,
        is_new_device: bool,
        is_unusual_hour: bool,
        had_privilege_escalation: bool,
        ip_address: str = "127.0.0.1"
    ) -> UserRiskProfile:
        score = 10.0
        reasons = []

        if failed_logins > 0:
            added = min(40.0, failed_logins * 8.0)
            score += added
            reasons.append(f"{failed_logins} failed login attempts (+{added:.0f})")

        if is_new_device:
            score += 20.0
            reasons.append("Authentication from unverified device/fingerprint (+20)")

        if is_unusual_hour:
            score += 15.0
            reasons.append("Administrative session initiated outside normal operating window (+15)")

        if had_privilege_escalation:
            score += 25.0
            reasons.append("Privilege escalation / role modification performed (+25)")

        score = min(100.0, score)

        if score >= 80:
            sev = "CRITICAL"
        elif score >= 60:
            sev = "HIGH"
        elif score >= 35:
            sev = "MEDIUM"
        else:
            sev = "LOW"

        if not reasons:
            reasons.append("Standard operator activity within nominal baseline.")

        return UserRiskProfile(
            username=username,
            risk_score=round(score, 1),
            severity=sev,
            reasons=reasons,
            failed_logins=failed_logins,
            last_login_ip=ip_address
        )

cyber_engine = CybersecurityEngine()
