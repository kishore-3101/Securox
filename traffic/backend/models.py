import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# ==========================================
# PRESERVED FASTAG MODELS (DO NOT REMOVE)
# ==========================================

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(String, unique=True, index=True)  # EPC ID
    vehicle_plate = Column(String, unique=True, index=True)


class Tollgate(Base):
    __tablename__ = "tollgates"
    id = Column(Integer, primary_key=True, index=True)
    gate_id = Column(String, unique=True, index=True)
    route = Column(String)


class TollgateDistance(Base):
    __tablename__ = "tollgate_distances"
    id = Column(Integer, primary_key=True, index=True)
    from_gate = Column(String, index=True)
    to_gate = Column(String, index=True)
    distance_km = Column(Float)
    min_travel_time_min = Column(Float)


class Scan(Base):
    __tablename__ = "scans"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=True)
    tag_id = Column(String, index=True)  # EPC ID
    vehicle_plate = Column(String, index=True)  # OCR Plate
    tollgate_id = Column(String, index=True)
    lane_id = Column(String, index=True, nullable=True)
    direction = Column(String)  # 'INBOUND' or 'OUTBOUND'
    status = Column(String, default="success") # success, anomaly, manual_override_success
    reason = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    route_id = Column(String)


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, index=True, nullable=True)
    tag_id = Column(String, index=True)
    vehicle_plate = Column(String)
    from_gate = Column(String)
    to_gate = Column(String)
    lane_id = Column(String, nullable=True)
    actual_time_min = Column(Float)
    min_travel_time_min = Column(Float)
    reason = Column(String)
    severity = Column(String)
    status = Column(String, default="pending") # pending, overridden, reported
    override_by = Column(String, nullable=True)
    override_reason = Column(String, nullable=True)
    override_at = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_resolved = Column(Boolean, default=False)


# ==========================================
# SECUROX PRODUCTION ENTERPRISE MODELS
# ==========================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    role = Column(String, default="OPERATOR")  # ADMIN, ANALYST, OPERATOR, EXECUTIVE, VIEWER
    is_active = Column(Boolean, default=True)
    failed_logins = Column(Integer, default=0)
    risk_score = Column(Float, default=5.0)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Camera(Base):
    __tablename__ = "cameras"
    id = Column(String, primary_key=True, index=True)  # e.g. CAM-01
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="ONLINE")  # ONLINE, DEGRADED, OFFLINE, COMPROMISED, MAINTENANCE
    fps = Column(Float, default=30.0)
    latency_ms = Column(Float, default=42.0)
    resolution = Column(String, default="1920x1080")
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)
    vehicle_count = Column(Integer, default=0)
    detection_confidence = Column(Float, default=0.92)
    network_health = Column(Float, default=98.5)
    security_health = Column(Float, default=95.0)
    risk_score = Column(Float, default=10.0)
    stream_url = Column(String, nullable=True)
    road_id = Column(String, nullable=True)
    is_simulated = Column(Boolean, default=True)


class RoadSegment(Base):
    __tablename__ = "road_segments"
    id = Column(String, primary_key=True, index=True)  # e.g. ROAD-NH44-01
    name = Column(String, nullable=False)
    route_id = Column(String, default="NH44")
    start_node = Column(String, nullable=False)
    end_node = Column(String, nullable=False)
    length_km = Column(Float, default=12.5)
    lanes = Column(Integer, default=4)
    speed_limit_kmh = Column(Float, default=100.0)
    current_speed_kmh = Column(Float, default=82.0)
    current_volume = Column(Integer, default=240)
    capacity = Column(Integer, default=400)
    density_score = Column(Float, default=45.0)
    congestion_level = Column(String, default="FREE_FLOW")  # FREE_FLOW, MODERATE, HEAVY, SEVERE, CRITICAL
    status = Column(String, default="OPEN")
    coordinates_json = Column(Text, default="[]")  # Polyline coords [[lat, lng], ...]


class Intersection(Base):
    __tablename__ = "intersections"
    id = Column(String, primary_key=True, index=True)  # e.g. INT-01
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    controller_id = Column(String, nullable=False)
    status = Column(String, default="NORMAL")
    signal_phase = Column(String, default="NORTH_SOUTH_GREEN")
    queue_length = Column(Integer, default=8)
    risk_score = Column(Float, default=12.0)


class TrafficSignal(Base):
    __tablename__ = "traffic_signals"
    id = Column(String, primary_key=True, index=True)  # e.g. SIG-INT01
    intersection_id = Column(String, index=True)
    controller_id = Column(String, index=True)
    current_state = Column(String, default="GREEN")  # GREEN, YELLOW, RED, FLASHING_RED
    cycle_time = Column(Integer, default=90)
    timing_plan = Column(String, default="ADAPTIVE_PEAK_01")
    status = Column(String, default="NORMAL")  # NORMAL, DEGRADED, MANIPULATED, OFFLINE
    last_command_time = Column(DateTime, default=datetime.datetime.utcnow)
    is_compromised = Column(Boolean, default=False)


class Sensor(Base):
    __tablename__ = "sensors"
    id = Column(String, primary_key=True, index=True)  # e.g. SEN-LOOP-01
    type = Column(String, default="INDUCTIVE_LOOP")  # INDUCTIVE_LOOP, RADAR, INFRARED, BLUETOOTH
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="ONLINE")  # ONLINE, FAULTY, TAMPERED, OFFLINE
    last_reading = Column(Float, default=150.0)
    expected_range_min = Column(Float, default=80.0)
    expected_range_max = Column(Float, default=300.0)
    confidence = Column(Float, default=0.98)
    data_quality_score = Column(Float, default=98.0)
    last_ping = Column(DateTime, default=datetime.datetime.utcnow)


class Asset(Base):
    __tablename__ = "assets"
    id = Column(String, primary_key=True, index=True)  # e.g. ASSET-CAM-01
    asset_type = Column(String, nullable=False)  # CAMERA, SENSOR, TRAFFIC_CONTROLLER, INTERSECTION, ROAD, EDGE_DEVICE, GATEWAY, SERVER, API, USER
    name = Column(String, nullable=False)
    ip_address = Column(String, default="192.168.10.1")
    mac_address = Column(String, default="00:1A:2B:3C:4D:5E")
    location = Column(String, default="Sector 4")
    status = Column(String, default="HEALTHY")  # HEALTHY, DEGRADED, COMPROMISED, OFFLINE
    risk_score = Column(Float, default=12.0)
    criticality = Column(String, default="HIGH")  # CRITICAL, HIGH, MEDIUM, LOW
    firmware_version = Column(String, default="v3.1.2-sec")
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"
    event_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String, index=True)  # e.g. TRAFFIC_CONGESTION, CAMERA_TAMPER, SIGNAL_ANOMALY
    severity = Column(String, index=True)    # INFO, LOW, MEDIUM, HIGH, CRITICAL
    asset_id = Column(String, index=True)
    location = Column(String)
    source = Column(String)
    confidence = Column(Float, default=0.95)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    metadata_json = Column(Text, default="{}")
    is_simulated = Column(Boolean, default=True)


class CyberThreat(Base):
    __tablename__ = "cyber_threats"
    threat_id = Column(String, primary_key=True, index=True)
    threat_type = Column(String, index=True)  # PORT_SCAN, UNAUTHORIZED_COMMAND, REPLAY_ATTACK, BRUTE_FORCE, BEACONING
    asset_id = Column(String, index=True)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    evidence_json = Column(Text, default="{}")
    confidence = Column(Float, default=0.92)
    risk_score = Column(Float, default=85.0)
    status = Column(String, default="OPEN")  # OPEN, INVESTIGATING, MITIGATED, RESOLVED
    source = Column(String, default="NETWORK_IDS")
    severity = Column(String, default="HIGH")  # INFO, LOW, MEDIUM, HIGH, CRITICAL


class Incident(Base):
    __tablename__ = "incidents"
    incident_id = Column(String, primary_key=True, index=True)  # INC-2026-001
    title = Column(String, nullable=False)
    severity = Column(String, default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    type = Column(String, default="TRAFFIC_CONGESTION")      # CYBER_PHYSICAL, TRAFFIC_CONGESTION, SIGNAL_TAMPERING, etc.
    status = Column(String, default="DETECTED", index=True)  # DETECTED, TRIAGED, ACKNOWLEDGED, INVESTIGATING, CONTAINED, RESOLVED, CLOSED
    asset_id = Column(String, index=True)
    location = Column(String)
    risk_score = Column(Float, default=50.0)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)
    evidence_json = Column(Text, default="{}")
    action_log_json = Column(Text, default="[]")
    root_cause = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)


class IncidentTimeline(Base):
    __tablename__ = "incident_timelines"
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.incident_id"), index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    event_type = Column(String)
    severity = Column(String, default="INFO")
    source = Column(String)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    user_id = Column(String, nullable=True)
    username = Column(String, nullable=True)
    action = Column(String, nullable=False)  # LOGIN, LOGOUT, RESOLVE_INCIDENT, OVERRIDE_SIGNAL, etc.
    target_type = Column(String, nullable=True)
    target_id = Column(String, nullable=True)
    details_json = Column(Text, default="{}")
    ip_address = Column(String, default="127.0.0.1")
    success = Column(Boolean, default=True)


class TrafficPrediction(Base):
    __tablename__ = "traffic_predictions"
    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(String, index=True)
    horizon_minutes = Column(Integer)  # 15, 30, 60, 120
    predicted_volume = Column(Integer)
    predicted_speed = Column(Float)
    predicted_congestion = Column(String)  # FREE_FLOW, MODERATE, HEAVY, SEVERE, CRITICAL
    confidence = Column(Float, default=0.88)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class TrackedVehicle(Base):
    __tablename__ = "tracked_vehicles"
    track_id = Column(String, primary_key=True, index=True)
    vehicle_type = Column(String, default="CAR")  # CAR, BUS, TRUCK, MOTORCYCLE, BICYCLE, VAN, EMERGENCY_VEHICLE
    confidence = Column(Float, default=0.94)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    lane = Column(Integer, default=1)
    direction = Column(String, default="NORTHBOUND")
    estimated_speed = Column(Float, default=65.0)
    camera_id = Column(String, default="CAM-01")
    license_plate = Column(String, nullable=True)
