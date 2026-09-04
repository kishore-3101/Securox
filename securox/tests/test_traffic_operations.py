"""
Securox Smart Traffic Domain — Complete Operational Subsystems Test Suite
Tests:
  1. Traffic Overview & Grid KPIs
  2. Multi-Tier Signal Safety Override Pipeline:
     - Rejects unauthenticated callers (401)
     - Rejects unauthorized roles e.g. citizen (403)
     - Rejects high-risk operator (risk_score >= 60.0 -> 403, triggers SOC incident + audit block)
     - Rejects invalid/empty operational context and short justifications (400)
     - Conflict Matrix Interlock & Clearance sequence (Yellow -> All-Red Hold -> Target Green)
     - Atomically commits signal state and audit log
  3. Roads & Congestion Intelligence (V/C density, speed deficit)
  4. Roadside Sensors & Sensor Disparity Analysis Engine (Loop vs. CCTV disparity)
  5. Traffic Incidents Lifecycle (Operator create -> Police on-scene verify -> Status update)
  6. FASTag ANPR Toll Processing & Fraud Defense (Clone detection, velocity impossibility, supervisor override)
  7. Emergency Vehicles & Green Corridor Preemption (Creation -> Preemptive signal lock -> Clearance & restoration)
  8. Signal Technician Hardware Maintenance (Diagnostic tickets, voltage/loop resistance, firmware integrity)
  9. Citizen Public Portal Isolation (Public read-only feed accessible, all operational control routes strictly blocked)
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from auth.jwt_auth import create_access_token

client = TestClient(app)


# ── Fixtures for Stakeholder Personas ─────────────────────────────────────────

@pytest.fixture
def operator_token():
    return create_access_token({
        "sub": "traffic_operator",
        "username": "traffic_operator",
        "role": "traffic_operator",
        "risk_score": 15.0
    })


@pytest.fixture
def compromised_operator_token():
    """Operator whose account or behavior has elevated risk score >= 60.0"""
    return create_access_token({
        "sub": "traffic_operator",
        "username": "traffic_operator",
        "role": "traffic_operator",
        "risk_score": 75.0
    })


@pytest.fixture
def police_token():
    return create_access_token({
        "sub": "traffic_police",
        "username": "traffic_police",
        "role": "traffic_police",
        "risk_score": 10.0
    })


@pytest.fixture
def technician_token():
    return create_access_token({
        "sub": "signal_tech",
        "username": "signal_tech",
        "role": "signal_technician",
        "risk_score": 10.0
    })


@pytest.fixture
def emergency_token():
    return create_access_token({
        "sub": "emergency_traffic",
        "username": "emergency_traffic",
        "role": "emergency_traffic",
        "risk_score": 5.0
    })


@pytest.fixture
def supervisor_token():
    return create_access_token({
        "sub": "traffic_supervisor",
        "username": "traffic_supervisor",
        "role": "traffic_supervisor",
        "risk_score": 15.0
    })


@pytest.fixture
def citizen_token():
    return create_access_token({
        "sub": "citizen",
        "username": "citizen",
        "role": "citizen",
        "risk_score": 0.0
    })


# ── 1. Traffic Overview & Citywide KPIs ───────────────────────────────────────

def test_traffic_overview_authorized(operator_token):
    res = client.get("/api/traffic/overview", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["grid_status"] == "OPERATIONAL"
    assert data["total_signals"] >= 6
    assert data["total_roads"] >= 5
    assert data["total_sensors"] >= 5
    assert "average_speed_kmh" in data
    assert "grid_congestion_index" in data


def test_traffic_overview_unauthenticated():
    res = client.get("/api/traffic/overview")
    assert res.status_code == 401


# ── 2. Traffic Signals & Critical Safety Override Pipeline ─────────────────────

def test_signals_list(operator_token):
    res = client.get("/api/traffic/signals", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
    signals = res.json()
    assert len(signals) >= 6
    ids = [s["id"] for s in signals]
    assert "SIG-01" in ids
    assert "SIG-02" in ids


def test_signal_safety_override_unauthenticated():
    """Unauthenticated users must NEVER actuate signals."""
    payload = {
        "target_state": "GREEN",
        "mode": "MANUAL_OVERRIDE",
        "reason": "Emergency rush preemption",
        "context_type": "EMERGENCY_PREEMPTION"
    }
    res = client.post("/api/traffic/signals/SIG-01/safety-override", json=payload)
    assert res.status_code == 401


def test_signal_safety_override_citizen_forbidden(citizen_token):
    """Citizens have zero authority to actuate or override municipal signals."""
    payload = {
        "target_state": "GREEN",
        "mode": "MANUAL_OVERRIDE",
        "reason": "I am in a hurry",
        "context_type": "MANUAL_OVERRIDE"
    }
    res = client.post("/api/traffic/signals/SIG-01/safety-override",
                       headers={"Authorization": f"Bearer {citizen_token}"},
                       json=payload)
    assert res.status_code == 403


def test_signal_safety_override_high_risk_blocked(compromised_operator_token):
    """Operator with risk score >= 60.0 is blocked by zero-trust SCADA guard."""
    payload = {
        "target_state": "GREEN",
        "mode": "MANUAL_OVERRIDE",
        "reason": "Preempting junction for traffic flow",
        "context_type": "CONGESTION_MITIGATION"
    }
    res = client.post("/api/traffic/signals/SIG-01/safety-override",
                       headers={"Authorization": f"Bearer {compromised_operator_token}"},
                       json=payload)
    assert res.status_code == 403
    data = res.json()
    assert "Operator risk score" in data["detail"] or "safety threshold" in data["detail"]


def test_signal_safety_override_invalid_context(operator_token):
    """Override missing valid operational context or justification must be rejected."""
    # Short reason (< 5 chars)
    res = client.post("/api/traffic/signals/SIG-01/safety-override",
                       headers={"Authorization": f"Bearer {operator_token}"},
                       json={
                           "target_state": "GREEN",
                           "reason": "yo",
                           "context_type": "EMERGENCY_PREEMPTION"
                       })
    assert res.status_code == 400

    # Invalid context type
    res2 = client.post("/api/traffic/signals/SIG-01/safety-override",
                        headers={"Authorization": f"Bearer {operator_token}"},
                        json={
                            "target_state": "GREEN",
                            "reason": "Preempting for motorcade clearance",
                            "context_type": "INVALID_CONTEXT_TYPE"
                        })
    assert res2.status_code == 400


def test_signal_safety_override_conflict_interlock_execution(operator_token):
    """
    Valid operator executing override on SIG-01 (Grand Ave NS).
    Conflict matrix interlock checks conflicting approach SIG-02 (Broadway EW).
    Generates clearance transition plan and atomically commits state and audit log.
    """
    payload = {
        "target_state": "GREEN",
        "mode": "MANUAL_OVERRIDE",
        "reason": "Ambulance trauma dispatch clearance",
        "context_type": "EMERGENCY_PREEMPTION",
        "context_ref": "DISP-AMB-902"
    }
    res = client.post("/api/traffic/signals/SIG-01/safety-override",
                       headers={"Authorization": f"Bearer {operator_token}"},
                       json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["allowed"] is True
    assert data["signal_id"] == "SIG-01"
    assert data["target_state"] == "GREEN"
    assert "safety_transition_plan" in data
    assert len(data["safety_transition_plan"]) >= 1
    assert "audit_id" in data


# ── 3. Roads & Congestion Intelligence ────────────────────────────────────────

def test_get_road_segments(operator_token):
    res = client.get("/api/traffic/roads", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
    roads = res.json()
    assert len(roads) >= 5
    for r in roads:
        assert "speed_limit_kmh" in r
        assert "current_speed_kmh" in r
        assert "congestion_level" in r


# ── 4. Roadside Sensors & Disparity Engine ────────────────────────────────────

def test_get_traffic_sensors(operator_token):
    res = client.get("/api/traffic/sensors", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
    sensors = res.json()
    assert len(sensors) >= 5


def test_sensor_disparity_analysis(operator_token):
    """Sensor Disparity Engine detects physical loop faults or SCADA spoofing."""
    res = client.get("/api/traffic/sensors/disparity", headers={"Authorization": f"Bearer {operator_token}"})
    assert res.status_code == 200
    data = res.json()
    assert "disparity_alerts" in data
    assert "cross_comparison" in data
    assert len(data["cross_comparison"]) >= 1


# ── 5. Traffic Incidents Lifecycle ────────────────────────────────────────────

def test_traffic_incidents_lifecycle(operator_token, police_token):
    # 1. Operator reports collision incident
    create_payload = {
        "title": "Minor Rear-End Fender Bender",
        "category": "COLLISION",
        "severity": "LOW",
        "location": "Indiranagar 100ft Road Junction",
        "road_id": "ROAD-URBAN-01",
        "description": "Two passenger hatchbacks collided, blocking left curb lane."
    }
    res_create = client.post("/api/traffic/incidents",
                             headers={"Authorization": f"Bearer {operator_token}"},
                             json=create_payload)
    assert res_create.status_code == 200
    inc = res_create.json()
    inc_id = inc["id"]
    assert inc["title"] == create_payload["title"]
    assert inc["verified"] == 0

    # 2. Traffic Police on-scene verification
    res_verify = client.patch(f"/api/traffic/incidents/{inc_id}/verify",
                              headers={"Authorization": f"Bearer {police_token}"},
                              json={"verified": True, "notes": "Officer on scene. Vehicles moved to shoulder."})
    assert res_verify.status_code == 200
    verified_inc = res_verify.json()
    assert verified_inc["verified"] == 1
    assert verified_inc["status"] == "VERIFIED"

    # 3. Resolve incident
    res_status = client.patch(f"/api/traffic/incidents/{inc_id}/status",
                              headers={"Authorization": f"Bearer {police_token}"},
                              json={"status": "RESOLVED", "resolution_notes": "Debris cleared, traffic flowing normally."})
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "RESOLVED"


# ── 6. Toll & FASTag ANPR Fraud Defense ────────────────────────────────────────

def test_toll_scans_and_clone_detection(operator_token, supervisor_token):
    # 1. Fetch toll scans
    res_scans = client.get("/api/traffic/toll/scans", headers={"Authorization": f"Bearer {operator_token}"})
    assert res_scans.status_code == 200
    scans = res_scans.json()
    assert len(scans) >= 3

    # 2. Process an inbound FASTag scan at Gate 1 (cleared)
    tag_id = f"TAG-TEST-{uuid.uuid4().hex[:6].upper()}"
    res_scan1 = client.post("/api/traffic/toll/process",
                            headers={"Authorization": f"Bearer {operator_token}"},
                            json={
                                "tollgate_id": "TOLL-GATE-01",
                                "tollgate_name": "Electronic City Elevated Tollway",
                                "vehicle_number": "KA-01-MJ-8888",
                                "fastag_id": tag_id,
                                "amount": 120.0,
                                "vehicle_class": "CAR/JEEP/VAN"
                            })
    assert res_scan1.status_code == 200
    assert res_scan1.json()["status"] == "CLEARED"

    # 3. Simulate cloned tag appearing at distant Gate 2 within seconds -> Detected as CLONED
    res_scan2 = client.post("/api/traffic/toll/process",
                            headers={"Authorization": f"Bearer {operator_token}"},
                            json={
                                "tollgate_id": "TOLL-GATE-02",
                                "tollgate_name": "Airport Expressway Plaza",
                                "vehicle_number": "DL-01-AB-1234",
                                "fastag_id": tag_id,
                                "amount": 120.0,
                                "vehicle_class": "CAR/JEEP/VAN"
                            })
    assert res_scan2.status_code == 200
    cloned_scan = res_scan2.json()
    assert cloned_scan["status"] == "CLONED"
    assert "Duplicate cryptographic signature detected" in cloned_scan["flag_reason"]

    # 4. Supervisor overrides suspect/cloned scan
    target_scan_id = cloned_scan["id"]
    res_override = client.post(f"/api/traffic/toll/{target_scan_id}/override",
                               headers={"Authorization": f"Bearer {supervisor_token}"},
                               json={"reason": "Fleet vehicle duplicate tag verified by transport supervisor."})
    assert res_override.status_code == 200
    assert res_override.json()["status"] == "OVERRIDDEN_CLEARED"


# ── 7. Emergency Response & Green Corridor Preemption ─────────────────────────

def test_green_corridor_lifecycle(emergency_token):
    # 1. Fetch green corridors
    res_list = client.get("/api/traffic/green-corridor", headers={"Authorization": f"Bearer {emergency_token}"})
    assert res_list.status_code == 200
    corrs = res_list.json()
    assert len(corrs) >= 2

    # 2. Activate standby corridor
    standby_corr = next((c for c in corrs if c.get("status") == "STANDBY"), corrs[0])
    corr_id = standby_corr["id"]

    res_act = client.post(f"/api/traffic/green-corridor/{corr_id}/activate",
                          headers={"Authorization": f"Bearer {emergency_token}"})
    assert res_act.status_code == 200
    activated = res_act.json()
    assert activated["status"] == "ACTIVE"

    # 3. Deactivate and restore normal adaptive timing
    res_deact = client.post(f"/api/traffic/green-corridor/{corr_id}/deactivate",
                            headers={"Authorization": f"Bearer {emergency_token}"})
    assert res_deact.status_code == 200
    assert res_deact.json()["status"] == "COMPLETED"


# ── 8. Traffic Signal Technician Maintenance ──────────────────────────────────

def test_technician_maintenance_lifecycle(technician_token):
    # 1. List maintenance tickets
    res_list = client.get("/api/traffic/maintenance/tickets", headers={"Authorization": f"Bearer {technician_token}"})
    assert res_list.status_code == 200
    tickets = res_list.json()
    assert len(tickets) >= 3

    # 2. Technician creates new diagnostic ticket
    tkt_data = {
        "signal_id": "SIG-03",
        "issue_type": "LOOP_IMPEDANCE_DRIFT",
        "priority": "HIGH",
        "voltage_reading": 228.4,
        "loop_resistance_ohms": 9.8,
        "firmware_checksum": "sha256_stig_v4.2.1_valid",
        "diagnostic_log": "High loop impedance detected; potential coil degradation."
    }
    res_create = client.post("/api/traffic/maintenance/tickets",
                             headers={"Authorization": f"Bearer {technician_token}"},
                             json=tkt_data)
    assert res_create.status_code == 200
    created = res_create.json()
    tkt_id = created["id"]
    assert created["signal_id"] == "SIG-03"
    assert created["status"] == "OPEN"

    # 3. Technician updates ticket to COMPLETED
    res_update = client.patch(f"/api/traffic/maintenance/tickets/{tkt_id}",
                              headers={"Authorization": f"Bearer {technician_token}"},
                              json={
                                  "status": "COMPLETED",
                                  "diagnostic_log": "Re-soldered feeder junction box. Impedance normalized to 4.1 ohms.",
                                  "resolution_notes": "Hardware loop verified operational."
                              })
    assert res_update.status_code == 200
    updated = res_update.json()
    assert updated["status"] == "COMPLETED"
    assert updated["completed_at"] is not None


# ── 9. Citizen Public Portal & Security Isolation ─────────────────────────────

def test_citizen_public_feed_accessible_without_auth():
    """Citizens can view the public advisory feed without needing credentials."""
    res = client.get("/api/traffic/citizen/public-feed")
    assert res.status_code == 200
    feed = res.json()
    assert "city" in feed
    assert "corridors" in feed
    assert "active_green_corridors_advisories" in feed
    assert "public_incidents" in feed


def test_citizen_strictly_blocked_from_infrastructure_mutations(citizen_token):
    """Citizen role is blocked from modifying infrastructure, dispatching corridors, or altering tickets."""
    # Blocked from creating incidents
    res1 = client.post("/api/traffic/incidents",
                       headers={"Authorization": f"Bearer {citizen_token}"},
                       json={"title": "test", "location": "here"})
    assert res1.status_code == 403

    # Blocked from green corridors
    res2 = client.post("/api/traffic/green-corridor/CORR-01/activate",
                       headers={"Authorization": f"Bearer {citizen_token}"})
    assert res2.status_code == 403

    # Blocked from maintenance tickets
    res3 = client.post("/api/traffic/maintenance/tickets",
                       headers={"Authorization": f"Bearer {citizen_token}"},
                       json={"signal_id": "SIG-01"})
    assert res3.status_code == 403