"""
Securox Traffic Models — Unified Data Model Bridge
Re-exports authoritative models from core.models to ensure single schema truth.
"""

from core.database import Base
from core.models import (
    Vehicle, Tollgate, TollgateDistance, Scan, Anomaly,
    User, Camera, Intersection, RoadSegment, Sensor,
    TrafficSignal, TrackedVehicle, TrafficPrediction,
    CyberThreat, Asset, AuditLog, Incident, IncidentTimeline
)

__all__ = [
    "Base",
    "Vehicle", "Tollgate", "TollgateDistance", "Scan", "Anomaly",
    "User", "Camera", "Intersection", "RoadSegment", "Sensor",
    "TrafficSignal", "TrackedVehicle", "TrafficPrediction",
    "CyberThreat", "Asset", "AuditLog", "Incident", "IncidentTimeline"
]
