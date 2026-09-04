"""
Securox — Unified Authoritative Data Models (SQLAlchemy 2.0)
Defines the single source of truth schema for Healthcare, Traffic, Finance, and SOC.
"""

import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text,
    ForeignKey, UniqueConstraint, Index, text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


# ==============================================================================
# 1. CORE AUTHENTICATION, RBAC & IDENTITY
# ==============================================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(128), unique=True, index=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    salt: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    role: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="OPERATOR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_logins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, nullable=False)
    last_login_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["UserSession"]] = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=True)


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    resource: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(256), default="")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[str] = mapped_column(String(32), ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    permission_id: Mapped[str] = mapped_column(String(64), ForeignKey("permissions.id", ondelete="CASCADE"), index=True)

    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    os: Mapped[str] = mapped_column(String(64), default="Unknown")
    browser: Mapped[str] = mapped_column(String(64), default="Unknown")
    ip: Mapped[str] = mapped_column(String(45), default="")
    location: Mapped[str] = mapped_column(String(128), default="")
    trust_score: Mapped[float] = mapped_column(Float, default=100.0)
    status: Mapped[str] = mapped_column(String(32), default="trusted")
    first_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    user: Mapped["User"] = relationship("User", back_populates="devices")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), default="")
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    expires_at: Mapped[str] = mapped_column(String(64), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="sessions")


class SecurityBan(Base):
    __tablename__ = "security_bans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_type: Mapped[str] = mapped_column(String(32), index=True)  # IP, DEVICE, USER, ACCOUNT
    target_value: Mapped[str] = mapped_column(String(128), index=True)
    reason: Mapped[str] = mapped_column(String(256), default="")
    banned_by: Mapped[str] = mapped_column(String(64), default="SYSTEM")
    banned_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    expires_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    domain: Mapped[str] = mapped_column(String(32), index=True, default="GLOBAL")
    rule_definition: Mapped[str] = mapped_column(Text, nullable=False)
    risk_modifier: Mapped[float] = mapped_column(Float, default=0.0)
    action: Mapped[str] = mapped_column(String(32), default="ALLOW")
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ==============================================================================
# 2. AUDIT TRAIL & CANONICAL EVENTS
# ==============================================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    actor: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    actor_username: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    actor_role: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True, server_default="RESOURCE")
    resource_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    decision: Mapped[str] = mapped_column(String(32), default="ALLOW", server_default="ALLOW")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True, server_default="{}")

    # Traffic domain compatibility attributes
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    details_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    success: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, server_default=text("CURRENT_TIMESTAMP"))


class EventStream(Base):
    __tablename__ = "event_stream"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    type: Mapped[str] = mapped_column(String(64), index=True)
    source_type: Mapped[str] = mapped_column(String(64), default="system")
    asset: Mapped[str] = mapped_column(String(64), index=True, default="unknown")
    severity: Mapped[str] = mapped_column(String(32), index=True, default="info")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


# ==============================================================================
# 3. SOC INCIDENTS, ALERTS, RISK & CAMPAIGNS
# ==============================================================================

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True, server_default=text("CURRENT_TIMESTAMP"))
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), index=True, default="MEDIUM", server_default="MEDIUM")
    type: Mapped[str] = mapped_column(String(64), index=True, default="SECURITY", server_default="SECURITY")
    status: Mapped[str] = mapped_column(String(32), index=True, default="OPEN", server_default="OPEN")
    asset_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    asset: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    domain: Mapped[str] = mapped_column(String(32), index=True, default="SOC", server_default="SOC")
    owner: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, server_default="0.0")
    detected_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True, server_default=text("CURRENT_TIMESTAMP"))
    acknowledged_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_escalated: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True, server_default="{}")

    timelines: Mapped[List["IncidentTimeline"]] = relationship(
        "IncidentTimeline", back_populates="incident", cascade="all, delete-orphan"
    )


class IncidentTimeline(Base):
    __tablename__ = "incident_timelines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    incident_id: Mapped[str] = mapped_column(String(64), ForeignKey("incidents.id", ondelete="CASCADE"), index=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), default="NOTE")
    severity: Mapped[str] = mapped_column(String(32), default="INFO")
    source: Mapped[str] = mapped_column(String(64), default="SYSTEM")

    incident: Mapped["Incident"] = relationship("Incident", back_populates="timelines")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    asset: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_category: Mapped[str] = mapped_column(String(32), default="LOW")
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    scenario: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    transaction_id: Mapped[str] = mapped_column(String(64), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="UPI")
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[str] = mapped_column(String(32), default="REVIEW")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    asset: Mapped[str] = mapped_column(String(64), index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(String(32), default="LOW")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class Mitigation(Base):
    __tablename__ = "mitigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    asset: Mapped[str] = mapped_column(String(64), default="")
    playbook: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_asset: Mapped[str] = mapped_column(String(64), nullable=False)
    before_risk: Mapped[float] = mapped_column(Float, default=0.0)
    after_risk: Mapped[float] = mapped_column(Float, default=0.0)
    verification_metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(64), default="SYSTEM")
    status: Mapped[str] = mapped_column(String(32), default="EXECUTED")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    stages: Mapped[str] = mapped_column(Text, default="[]")
    affected_assets: Mapped[str] = mapped_column(Text, default="[]")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    first_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class CrossDomainThreat(Base):
    __tablename__ = "cross_domain_threats"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    threat_actor_ip: Mapped[str] = mapped_column(String(45), index=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    domains_involved: Mapped[str] = mapped_column(Text, default="[]")
    first_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    campaign_summary: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="DETECTED")


# ==============================================================================
# 4. SIMULATION ENGINE & PERSISTENT RUNTIME STATE
# ==============================================================================

class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    target_asset: Mapped[str] = mapped_column(String(64))
    attack_type: Mapped[str] = mapped_column(String(64))
    intensity: Mapped[float] = mapped_column(Float, default=1.0)
    duration: Mapped[float] = mapped_column(Float, default=60.0)
    events_generated: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED")
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class SimulationState(Base):
    """
    Persists active simulation progress across process restarts.
    Guarantees active scenarios, stages, injected attacks, and telemetry survive crashes.
    """
    __tablename__ = "simulation_state"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="active_state")
    scenario_id: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(32), default="IDLE")  # IDLE, RUNNING, PAUSED, COMPLETED
    current_stage: Mapped[int] = mapped_column(Integer, default=0)
    stage_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    elapsed_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    events_emitted: Mapped[int] = mapped_column(Integer, default=0)
    state_blob: Mapped[str] = mapped_column(Text, default="{}")
    started_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


# ==============================================================================
# 5. SMART TRAFFIC INFRASTRUCTURE & COMPUTER VISION
# ==============================================================================

class Intersection(Base):
    __tablename__ = "intersections"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    controller_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    signal_phase: Mapped[str] = mapped_column(String(32), default="RED")
    queue_length: Mapped[int] = mapped_column(Integer, default=0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    signals: Mapped[List["TrafficSignal"]] = relationship("TrafficSignal", back_populates="intersection_rel")


class RoadSegment(Base):
    __tablename__ = "road_segments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    route_id: Mapped[str] = mapped_column(String(64), index=True)
    start_node: Mapped[str] = mapped_column(String(64))
    end_node: Mapped[str] = mapped_column(String(64))
    length_km: Mapped[float] = mapped_column(Float, default=1.0)
    lanes: Mapped[int] = mapped_column(Integer, default=2)
    speed_limit_kmh: Mapped[float] = mapped_column(Float, default=50.0)
    current_speed_kmh: Mapped[float] = mapped_column(Float, default=45.0)
    current_volume: Mapped[int] = mapped_column(Integer, default=100)
    congestion_level: Mapped[str] = mapped_column(String(32), default="LOW")
    incident_count: Mapped[int] = mapped_column(Integer, default=0)
    capacity: Mapped[int] = mapped_column(Integer, default=1500)
    density_score: Mapped[float] = mapped_column(Float, default=30.0)
    status: Mapped[str] = mapped_column(String(32), default="OPERATIONAL")
    coordinates_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_updated: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class TrafficSignal(Base):
    """Reconciled traffic signal combining Securox zones and Traffic controller phases."""
    __tablename__ = "traffic_signals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    intersection_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("intersections.id", ondelete="SET NULL"), nullable=True)
    intersection: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    zone: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    controller_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_state: Mapped[str] = mapped_column(String(32), default="RED")
    cycle_time_sec: Mapped[int] = mapped_column(Integer, default=90)
    cycle_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timing_plan: Mapped[str] = mapped_column(String(64), default="FIXED")
    mode: Mapped[str] = mapped_column(String(32), default="AUTO")
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    is_tampered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_compromised: Mapped[bool] = mapped_column(Boolean, default=False)
    last_override_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_command_time: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    intersection_rel: Mapped[Optional["Intersection"]] = relationship("Intersection", back_populates="signals")


class Camera(Base):
    """Reconciled Camera model supporting both IP security feeds and CCTV stream telemetry."""
    __tablename__ = "cameras"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intersection_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    road_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    camera_type: Mapped[str] = mapped_column(String(32), default="FIXED_CCTV")  # FIXED_CCTV, PTZ, MOBILE_CAMERA, PHONE_CAMERA, IP_CAMERA, SIMULATED_CAMERA
    stream_type: Mapped[str] = mapped_column(String(32), default="WEBRTC")      # WEBRTC, RTSP, HLS, HTTP, SIMULATION
    stream_url: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")           # ONLINE, OFFLINE, DEGRADED, COMPROMISED, UNAUTHORIZED
    health: Mapped[str] = mapped_column(String(32), default="HEALTHY")
    fps: Mapped[float] = mapped_column(Float, default=30.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=42.0)
    resolution: Mapped[str] = mapped_column(String(32), default="1920x1080")
    incident_count: Mapped[int] = mapped_column(Integer, default=0)
    last_seen: Mapped[Optional[str]] = mapped_column(String(64), default=_utcnow_iso)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    trust_status: Mapped[str] = mapped_column(String(32), default="TRUSTED")    # TRUSTED, UNTRUSTED, SUSPICIOUS, BLOCKED
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    last_heartbeat: Mapped[Optional[str]] = mapped_column(String(64), default=_utcnow_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    domain: Mapped[str] = mapped_column(String(32), index=True, default="TRAFFIC")
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    criticality: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    firmware_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen: Mapped[Optional[str]] = mapped_column(String(64), default=_utcnow_iso)


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(String(64))
    location: Mapped[str] = mapped_column(String(128))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    last_reading: Mapped[float] = mapped_column(Float, default=0.0)
    expected_range_min: Mapped[float] = mapped_column(Float, default=0.0)
    expected_range_max: Mapped[float] = mapped_column(Float, default=100.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    anomaly_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    last_heartbeat: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vehicle_plate: Mapped[str] = mapped_column(String(32), unique=True, index=True)


class Tollgate(Base):
    __tablename__ = "tollgates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    gate_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    route: Mapped[str] = mapped_column(String(64))


class TollgateDistance(Base):
    __tablename__ = "tollgate_distances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_gate: Mapped[str] = mapped_column(String(32), index=True)
    to_gate: Mapped[str] = mapped_column(String(32), index=True)
    distance_km: Mapped[float] = mapped_column(Float)
    min_travel_time_min: Mapped[float] = mapped_column(Float)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    tag_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_plate: Mapped[str] = mapped_column(String(32), index=True)
    tollgate_id: Mapped[str] = mapped_column(String(32), index=True)
    lane_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    direction: Mapped[str] = mapped_column(String(16), default="INBOUND")
    status: Mapped[str] = mapped_column(String(32), default="success")
    reason: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    route_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    tag_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_plate: Mapped[str] = mapped_column(String(32))
    from_gate: Mapped[str] = mapped_column(String(32))
    to_gate: Mapped[str] = mapped_column(String(32))
    lane_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    actual_time_min: Mapped[float] = mapped_column(Float)
    min_travel_time_min: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(128))
    severity: Mapped[str] = mapped_column(String(32), default="MEDIUM")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    override_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    override_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    override_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detected_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class TrackedVehicle(Base):
    __tablename__ = "tracked_vehicles"

    track_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(String(32), default="car")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    first_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    lane: Mapped[int] = mapped_column(Integer, default=1)
    direction: Mapped[str] = mapped_column(String(16), default="NORTH")
    estimated_speed: Mapped[float] = mapped_column(Float, default=45.0)
    camera_id: Mapped[str] = mapped_column(String(32), ForeignKey("cameras.id", ondelete="CASCADE"))
    license_plate: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class TrafficPrediction(Base):
    __tablename__ = "traffic_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    road_id: Mapped[str] = mapped_column(String(32), ForeignKey("road_segments.id", ondelete="CASCADE"), index=True)
    horizon_minutes: Mapped[int] = mapped_column(Integer, default=15)
    predicted_volume: Mapped[int] = mapped_column(Integer, default=100)
    predicted_speed: Mapped[float] = mapped_column(Float, default=45.0)
    predicted_congestion: Mapped[str] = mapped_column(String(32), default="LOW")
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class CyberThreat(Base):
    __tablename__ = "cyber_threats"

    threat_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    threat_type: Mapped[str] = mapped_column(String(64), index=True)
    asset_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    evidence_json: Mapped[str] = mapped_column(Text, default="{}")
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    risk_score: Mapped[float] = mapped_column(Float, default=75.0)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    source: Mapped[str] = mapped_column(String(64), default="CYBER_ENGINE")
    mitigation_action: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


# ==============================================================================
# 6. HEALTHCARE DOMAIN & IOMT RECORDS
# ==============================================================================

class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    hospital_id: Mapped[str] = mapped_column(String(64), index=True, default="HOSP-CITY-01")
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    department: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    assigned_doctor_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    assigned_nurse_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    room_bed: Mapped[str] = mapped_column(String(32), default="")
    condition: Mapped[str] = mapped_column(String(32), default="STABLE")
    admission_date: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    vital_signs_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    medical_records: Mapped[List["MedicalRecord"]] = relationship(
        "MedicalRecord", back_populates="patient", cascade="all, delete-orphan"
    )
    ambulances: Mapped[List["Ambulance"]] = relationship("Ambulance", back_populates="assigned_patient")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), ForeignKey("patients.id", ondelete="CASCADE"), index=True)
    doctor_id: Mapped[str] = mapped_column(String(64), index=True)
    diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    prescriptions: Mapped[str] = mapped_column(Text, default="[]")
    lab_results: Mapped[str] = mapped_column(Text, default="[]")
    treatment_notes: Mapped[str] = mapped_column(Text, default="")
    sensitivity: Mapped[str] = mapped_column(String(32), default="RESTRICTED")
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="medical_records")


class Ambulance(Base):
    __tablename__ = "ambulances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    driver_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    vehicle_number: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    call_sign: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="AVAILABLE")
    current_location: Mapped[str] = mapped_column(String(128), default="")
    destination_hospital: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    patient_priority: Mapped[str] = mapped_column(String(32), default="NORMAL")
    assigned_patient_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    eta_minutes: Mapped[int] = mapped_column(Integer, default=0)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    assigned_patient: Mapped[Optional["Patient"]] = relationship("Patient", back_populates="ambulances")


# ==============================================================================
# 7. FINTECH, BANKING & AML/CFT GRAPH
# ==============================================================================

class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), default="SAVINGS")
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    branch: Mapped[str] = mapped_column(String(64), default="HEADQUARTERS")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    risk_rating: Mapped[str] = mapped_column(String(32), default="LOW")
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    transactions: Mapped[List["BankTransaction"]] = relationship("BankTransaction", back_populates="account")


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("bank_accounts.id", ondelete="CASCADE"), index=True)
    sender_name: Mapped[str] = mapped_column(String(128))
    receiver_account: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    channel: Mapped[str] = mapped_column(String(32), index=True, default="UPI")
    transaction_type: Mapped[str] = mapped_column(String(32), default="TRANSFER")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    decision: Mapped[str] = mapped_column(String(32), default="APPROVE")
    is_fraud: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_sar: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    beneficiary_age_hours: Mapped[float] = mapped_column(Float, default=720.0, server_default="720.0")
    device_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True, server_default=text("CURRENT_TIMESTAMP"))
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True, server_default=text("CURRENT_TIMESTAMP"))

    account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="transactions")
    fraud_cases: Mapped[List["FraudCase"]] = relationship("FraudCase", back_populates="transaction")


class FraudCase(Base):
    __tablename__ = "fraud_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("bank_transactions.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[str] = mapped_column(String(64), index=True)
    fraud_type: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)

    transaction: Mapped[Optional["BankTransaction"]] = relationship("BankTransaction", back_populates="fraud_cases")


class AMLCase(Base):
    __tablename__ = "aml_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    suspect_account_id: Mapped[str] = mapped_column(String(64), index=True)
    case_type: Mapped[str] = mapped_column(String(64), index=True)  # STRUCTURING, RAPID_MOVEMENT, MULE_NETWORK
    total_suspicious_volume: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="INVESTIGATING")
    sar_filed: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class AMLGraphState(Base):
    """
    Persists the synthetic/production AML money-mule graph state across backend restarts.
    """
    __tablename__ = "aml_graph_state"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default="primary")
    graph_name: Mapped[str] = mapped_column(String(128), default="SmartCityFintechGraph")
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, default=0)
    mule_cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    nodes_json: Mapped[str] = mapped_column(Text, default="[]")
    edges_json: Mapped[str] = mapped_column(Text, default="[]")
    clusters_json: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


# ==============================================================================
# ADVANCED TRAFFIC INTELLIGENCE: SENSING, VEHICLE IDENTITY & RFID
# ==============================================================================

class MobileCameraSession(Base):
    __tablename__ = "mobile_camera_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    latitude: Mapped[float] = mapped_column(Float, default=12.9716)
    longitude: Mapped[float] = mapped_column(Float, default=77.5946)
    started_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")
    stream_status: Mapped[str] = mapped_column(String(32), default="STREAMING")
    trust_status: Mapped[str] = mapped_column(String(32), default="EVALUATED")


class VehicleDetectionRecord(Base):
    __tablename__ = "vehicle_detections"

    detection_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    vehicle_class: Mapped[str] = mapped_column(String(32), default="car")
    confidence: Mapped[float] = mapped_column(Float, default=0.92)
    bounding_box_json: Mapped[str] = mapped_column(Text, default="[0,0,0,0]")
    tracking_id: Mapped[str] = mapped_column(String(64), index=True)
    location: Mapped[str] = mapped_column(String(128), default="Majestic Interchange")
    direction: Mapped[str] = mapped_column(String(32), default="NORTH")
    speed_estimate: Mapped[float] = mapped_column(Float, default=45.0)
    lane: Mapped[int] = mapped_column(Integer, default=1)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class RFIDReader(Base):
    __tablename__ = "rfid_readers"

    reader_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    lane: Mapped[str] = mapped_column(String(32), default="LANE-01")
    status: Mapped[str] = mapped_column(String(32), default="ONLINE")
    ip_address: Mapped[str] = mapped_column(String(45), default="10.12.4.50")
    device_id: Mapped[str] = mapped_column(String(64), default="DEV-RFID-01")
    trust_status: Mapped[str] = mapped_column(String(32), default="TRUSTED")
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class RFIDReadRecord(Base):
    __tablename__ = "rfid_reads"

    read_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    reader_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    tag_id: Mapped[str] = mapped_column(String(64), index=True)
    lane: Mapped[str] = mapped_column(String(32), default="LANE-01")
    signal_strength: Mapped[float] = mapped_column(Float, default=-58.0)
    vehicle_association: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.98)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")


class FastagRecord(Base):
    __tablename__ = "fastags"

    fastag_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tag_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_registration: Mapped[str] = mapped_column(String(32), index=True)
    customer_id: Mapped[str] = mapped_column(String(64), default="CUST-1001")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE")  # ACTIVE, BLOCKED, EXPIRED, SUSPENDED, UNKNOWN
    issuer: Mapped[str] = mapped_column(String(64), default="NPCI_NETC")
    linked_account: Mapped[str] = mapped_column(String(64), default="ACC-***-9021")
    created_at: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)
    last_seen: Mapped[str] = mapped_column(String(64), default=_utcnow_iso)


class VehicleIdentityVerificationRecord(Base):
    __tablename__ = "vehicle_identity_verifications"

    verification_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    rfid_read_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    detection_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    camera_id: Mapped[str] = mapped_column(String(64), index=True)
    tag_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    registered_plate: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    ocr_plate: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    rfid_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    identity_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="VERIFIED")  # VERIFIED, MISMATCH, OCR_ONLY, RFID_ONLY, UNKNOWN_TAG, UNKNOWN_PLATE, LOW_CONFIDENCE, DUPLICATE_READ, STALE_READ
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    repeated_mismatch_count: Mapped[int] = mapped_column(Integer, default=0)
    cameras_seen_json: Mapped[str] = mapped_column(Text, default="[]")
    timestamp: Mapped[str] = mapped_column(String(64), default=_utcnow_iso, index=True)
    details: Mapped[str] = mapped_column(Text, default="{}")

