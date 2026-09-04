"""
Securox Central Security Event Architecture — Integration & Verification Suite
Verifies:
  1. Canonical 14-field event schema compliance
  2. Ingestion across all 16 canonical security actions
  3. Persistent storage and multi-criteria query filters
  4. Aggregated event analytics and statistics endpoint
  5. In-process streaming queue and subscriber broadcast
  6. Domain-integrated event emission (LOGIN, BREAK_GLASS, SIGNAL_OVERRIDE, TRANSACTION, FRAUD_ALERT, AML_ALERT)
"""

import asyncio
import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app"))
if backend_app not in sys.path:
    sys.path.insert(0, backend_app)
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(1, backend_dir)

from main import app
from auth.jwt_auth import create_access_token
from services.event_fabric import event_fabric, CANONICAL_ACTIONS

client = TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "username": "admin", "role": "admin"})


@pytest.fixture
def auditor_token():
    return create_access_token({"sub": "auditor", "username": "auditor", "role": "auditor"})


@pytest.fixture
def doctor_token():
    return create_access_token({"sub": "doctor", "username": "doctor", "role": "doctor"})


@pytest.fixture
def operator_token():
    return create_access_token({"sub": "traffic_operator", "username": "traffic_operator", "role": "traffic_operator"})


def test_canonical_event_ingestion(admin_token):
    """Verifies that an event with canonical 14 fields is ingested and persisted."""
    payload = {
        "event_id": f"EVT-TEST-{uuid.uuid4().hex[:6].upper()}",
        "timestamp": "2026-09-05T00:00:00Z",
        "domain": "SECURITY",
        "organization": "Pan-City SOC Command",
        "user": "admin",
        "role": "admin",
        "device": "SOC-CONSOLE-01",
        "ip": "10.0.0.1",
        "location": "City Operations HQ",
        "resource": "SYSTEM_AUTH",
        "action": "LOGIN",
        "result": "SUCCESS",
        "risk": 0.0,
        "metadata": {"method": "HARDWARE_MFA", "session_ttl": 3600}
    }
    resp = client.post("/api/events", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["event_id"] == payload["event_id"]
    assert data["domain"] == "SECURITY"
    assert data["action"] == "LOGIN"
    assert data["result"] == "SUCCESS"
    assert data["risk"] == 0.0
    assert data["metadata"]["method"] == "HARDWARE_MFA"


def test_all_16_canonical_actions_ingestion(admin_token):
    """Verifies that all 16 canonical actions can be ingested without rejection."""
    for action in CANONICAL_ACTIONS:
        payload = {
            "domain": "PLATFORM",
            "user": "test_actor",
            "role": "system",
            "resource": f"RESOURCE:{action}",
            "action": action,
            "result": "SUCCESS",
            "risk": 10.0,
            "metadata": {"test_action": action}
        }
        resp = client.post("/api/events", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["action"] == action
        assert "event_id" in data


def test_get_security_events_filtering(auditor_token):
    """Auditors and analysts can query events by domain, action, and min_risk."""
    resp = client.get("/api/events?domain=FINANCE&limit=10", headers={"Authorization": f"Bearer {auditor_token}"})
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    for evt in events:
        assert evt["domain"] == "FINANCE"


def test_get_security_events_stats(admin_token):
    """Verifies aggregated event statistics endpoint."""
    resp = client.get("/api/events/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_events" in stats
    assert "high_risk_events" in stats
    assert "domains" in stats
    assert "top_actions" in stats
    assert stats["total_events"] > 0


@pytest.mark.asyncio
async def test_in_process_streaming_subscriber():
    """Verifies that in-process asyncio queues receive events emitted to the fabric."""
    test_q = asyncio.Queue()
    event_fabric.subscribe_queue(test_q)

    test_payload = {
        "domain": "HEALTHCARE",
        "user": "doctor_stream",
        "role": "doctor",
        "resource": "PATIENT:P-1001",
        "action": "PATIENT_ACCESS",
        "result": "SUCCESS",
        "risk": 5.0,
        "metadata": {"reason": "Morning ward rounds"}
    }
    await event_fabric.ingest_event(test_payload)

    received = await asyncio.wait_for(test_q.get(), timeout=2.0)
    assert received["action"] == "PATIENT_ACCESS"
    assert received["user"] == "doctor_stream"
    event_fabric.unsubscribe_queue(test_q)


def test_auth_login_produces_event():
    """Verifies that user login route emits a canonical LOGIN event."""
    resp = client.post(
        "/api/auth/login",
        data={"username": "superadmin", "password": "admin123"}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Verify event logged
    ev_resp = client.get("/api/events?action=LOGIN&user=superadmin&limit=5", headers={"Authorization": f"Bearer {token}"})
    assert ev_resp.status_code == 200
    events = ev_resp.json()
    assert any(e["user"] == "superadmin" and e["action"] == "LOGIN" for e in events)


def test_break_glass_produces_canonical_event(doctor_token):
    """Verifies that healthcare emergency break-glass emits a canonical BREAK_GLASS event."""
    resp = client.post(
        "/api/healthcare/break-glass",
        json={"patient_id": "P-1004", "reason": "Patient experiencing acute status epilepticus", "override_type": "EMERGENCY_OVERRIDE"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 200

    # Check event fabric
    ev_resp = client.get("/api/events?action=BREAK_GLASS&limit=5", headers={"Authorization": f"Bearer {doctor_token}"})
    assert ev_resp.status_code == 200
    events = ev_resp.json()
    assert any("P-1004" in e["resource"] for e in events)

@pytest.fixture
def paramedic_token():
    return create_access_token({
        "sub": "paramedic",
        "username": "paramedic",
        "role": "paramedic",
        "department": "Emergency Medical Services"
    })


@pytest.fixture
def customer_token():
    return create_access_token({
        "sub": "customer",
        "username": "customer",
        "role": "customer",
        "customer_id": "CUST-101"
    })


def test_patient_access_and_medical_update_produce_events(doctor_token):
    # PATIENT_ACCESS
    resp = client.get("/api/healthcare/patients/P-1001", headers={"Authorization": f"Bearer {doctor_token}"})
    assert resp.status_code == 200
    ev_resp = client.get("/api/events?action=PATIENT_ACCESS&limit=5", headers={"Authorization": f"Bearer {doctor_token}"})
    assert ev_resp.status_code == 200
    assert any("P-1001" in e["resource"] for e in ev_resp.json())

    # MEDICAL_RECORD_UPDATE
    up_resp = client.patch(
        "/api/healthcare/patients/P-1001",
        json={"notes": "Central event architecture verification"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert up_resp.status_code == 200
    ev_resp2 = client.get("/api/events?action=MEDICAL_RECORD_UPDATE&limit=5", headers={"Authorization": f"Bearer {doctor_token}"})
    assert ev_resp2.status_code == 200
    assert any("P-1001" in e["resource"] for e in ev_resp2.json())


@pytest.fixture
def teller_token():
    return create_access_token({
        "sub": "teller",
        "username": "teller",
        "role": "teller",
        "branch_id": "BR-01"
    })


def test_ambulance_assignment_produces_event(paramedic_token):
    dsp_payload = {
        "ambulance_id": "AMB-01",
        "paramedic_id": "paramedic",
        "patient_id": "P-1003",
        "caller_name": "Emergency Hotline 108",
        "emergency_type": "STEMI Acute Infarction",
        "triage_priority": "P1_CRITICAL",
        "origin_location": "Indiranagar 100ft Road",
        "destination_hospital": "City General Hospital (H001)",
        "green_corridor_active": True,
        "vitals": {"hr": 118, "bp": "158/94", "spo2": 93}
    }
    resp = client.post(
        "/api/healthcare/emergency/dispatch",
        json=dsp_payload,
        headers={"Authorization": f"Bearer {paramedic_token}"}
    )
    assert resp.status_code == 200
    ev_resp = client.get("/api/events?action=AMBULANCE_ASSIGNMENT&limit=5", headers={"Authorization": f"Bearer {paramedic_token}"})
    assert ev_resp.status_code == 200
    assert any("AMB-01" in e["resource"] for e in ev_resp.json())


def test_signal_override_and_incident_creation_produce_events(operator_token):
    # SIGNAL_OVERRIDE
    resp = client.post(
        "/api/traffic/signals/SIG-01/safety-override",
        json={"target_state": "ALL_RED", "mode": "MANUAL_HOLD", "reason": "VIP Corridor Cleared"},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert resp.status_code == 200
    ev_resp = client.get("/api/events?action=SIGNAL_OVERRIDE&limit=5", headers={"Authorization": f"Bearer {operator_token}"})
    assert ev_resp.status_code == 200
    assert any("SIG-01" in e["resource"] for e in ev_resp.json())

    # INCIDENT_CREATED
    inc_resp = client.post(
        "/api/traffic/incidents",
        json={"title": "Junction gridlock detected", "category": "HAZARD", "severity": "HIGH", "location": "Sector 4"},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert inc_resp.status_code == 200
    ev_resp2 = client.get("/api/events?action=INCIDENT_CREATED&limit=5", headers={"Authorization": f"Bearer {operator_token}"})
    assert ev_resp2.status_code == 200
    assert any(e["action"] == "INCIDENT_CREATED" for e in ev_resp2.json())


def test_camera_access_and_failure_produce_events(operator_token):
    # CAMERA_ACCESS
    resp = client.get("/api/traffic/cameras", headers={"Authorization": f"Bearer {operator_token}"})
    assert resp.status_code == 200
    ev_resp = client.get("/api/events?action=CAMERA_ACCESS&limit=5", headers={"Authorization": f"Bearer {operator_token}"})
    assert ev_resp.status_code == 200
    assert any(e["action"] == "CAMERA_ACCESS" for e in ev_resp.json())

    # CAMERA_FAILURE
    fail_resp = client.post(
        "/api/traffic/cameras/CAM-01/report-failure",
        json={"reason": "Optics vandalized / signal timeout", "severity": "HIGH"},
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert fail_resp.status_code == 200
    ev_resp2 = client.get("/api/events?action=CAMERA_FAILURE&limit=5", headers={"Authorization": f"Bearer {operator_token}"})
    assert ev_resp2.status_code == 200
    assert any("CAM-01" in e["resource"] for e in ev_resp2.json())


def test_transaction_and_fraud_alert_produce_events(teller_token):
    # Normal transaction -> TRANSACTION event
    resp = client.post(
        "/api/finance/transactions",
        json={"account_id": "ACC-7001", "counterparty_account": "ACC-7002", "amount": 1500.0, "channel": "UPI"},
        headers={"Authorization": f"Bearer {teller_token}"}
    )
    assert resp.status_code == 201
    ev_resp = client.get("/api/events?domain=FINANCE&action=TRANSACTION&limit=5", headers={"Authorization": f"Bearer {teller_token}"})
    assert ev_resp.status_code == 200
    assert any(e["action"] == "TRANSACTION" for e in ev_resp.json())

    # High-risk transaction -> FRAUD_ALERT event
    resp_fraud = client.post(
        "/api/finance/transactions",
        json={"account_id": "ACC-7002", "counterparty_account": "ACC-9999", "amount": 4999999.0, "channel": "SWIFT_WIRE", "ip_address": "198.51.100.99"},
        headers={"Authorization": f"Bearer {teller_token}"}
    )
    assert resp_fraud.status_code == 201
    ev_fraud = client.get("/api/events?action=FRAUD_ALERT&limit=5", headers={"Authorization": f"Bearer {teller_token}"})
    assert ev_fraud.status_code == 200
    assert any(e["action"] == "FRAUD_ALERT" for e in ev_fraud.json())


def test_access_denied_produces_event(auditor_token):
    # Auditor attempting mutating action -> ACCESS_DENIED
    resp = client.post(
        "/api/finance/transactions",
        json={"account_id": "ACC-7001", "counterparty_account": "ACC-7002", "amount": 100.0},
        headers={"Authorization": f"Bearer {auditor_token}"}
    )
    assert resp.status_code == 403
    ev_resp = client.get("/api/events?action=ACCESS_DENIED&limit=5", headers={"Authorization": f"Bearer {auditor_token}"})
    assert ev_resp.status_code == 200
    assert any(e["action"] == "ACCESS_DENIED" for e in ev_resp.json())


def test_device_registered_and_policy_change_produce_events(admin_token):
    # DEVICE_REGISTERED
    dev_resp = client.post(
        "/api/security/devices/register",
        json={"user_id": "admin", "os_name": "Fedora 40", "browser": "Securox Agent", "ip": "10.10.10.5", "trust_score": 98.0},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert dev_resp.status_code == 200
    ev_resp = client.get("/api/events?action=DEVICE_REGISTERED&limit=5", headers={"Authorization": f"Bearer {admin_token}"})
    assert ev_resp.status_code == 200
    assert any(e["action"] == "DEVICE_REGISTERED" for e in ev_resp.json())

    # POLICY_CHANGE
    pol_resp = client.put(
        "/api/security/policies/POL-01",
        json={"name": "Enhanced Zero Trust Interlock", "risk_modifier": 1.25},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert pol_resp.status_code == 200
    ev_resp2 = client.get("/api/events?action=POLICY_CHANGE&limit=5", headers={"Authorization": f"Bearer {admin_token}"})
    assert ev_resp2.status_code == 200
    assert any("POL-01" in e["resource"] for e in ev_resp2.json())


def test_logout_produces_event(admin_token):
    resp = client.post("/api/logout", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    ev_resp = client.get("/api/events?action=LOGOUT&limit=5", headers={"Authorization": f"Bearer {admin_token}"})
    assert ev_resp.status_code == 200
    assert any(e["action"] == "LOGOUT" for e in ev_resp.json())


def test_websocket_event_streaming(admin_token):
    with client.websocket_connect("/api/events/ws") as ws:
        # Initial greeting from WebSocket endpoint
        init_msg = ws.receive_json()
        assert init_msg["type"] in ("CONNECTION_ESTABLISHED", "INITIAL_EVENT_BUFFER", "PING")
        
        # Emit an event to the fabric
        payload = {
            "domain": "SECURITY",
            "user": "ws_tester",
            "role": "soc_analyst",
            "resource": "TEST_RESOURCE",
            "action": "LOGIN",
            "result": "SUCCESS",
            "risk": 0.0,
            "metadata": {"source": "ws_test"}
        }
        resp = client.post("/api/events", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
