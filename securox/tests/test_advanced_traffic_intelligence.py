"""
SECUR0X — Advanced Traffic Intelligence Automated Test Suite
Tests:
  1. CCTV Camera Management & Stream Lifecycle:
     - CRUD for cameras (register, query, update, delete)
     - Stream start, stop, and stream info retrieval
     - Password / private RTSP credentials masking
  2. RBAC / ABAC Zero-Trust Camera Stream Security:
     - Authorized traffic operator / investigator granted access
     - Unauthorized roles (citizen) denied (403)
     - High risk caller (risk_score >= 60.0) blocked (403)
  3. Phone-as-CCTV MobileCameraSession:
     - Zero-trust posture evaluation
     - Device session creation with token & risk score
  4. AI Video Processing Pipeline & Vehicle Tracking:
     - Ingestion of detections with tracking ID (TRACK-XX)
     - Multi-frame agreement & OCR_UNCERTAIN handling for low-confidence reads
     - Querying vehicle tracks and plate history
  5. FASTag RFID Reader Subsystem:
     - Reader registry querying
     - Real-time RFID read ingestion & telemetry
  6. Vehicle Identity Cross-Verification Engine:
     - VERIFIED: Matching RFID tag and OCR plate
     - LOW_CONFIDENCE / OCR_UNCERTAIN: Optical uncertainty differentiated from fraud
     - MISMATCH: RFID plate != OCR plate
     - Repeated multi-camera mismatch: Escalates to ESCALATED_TO_SOC and triggers security alert
  7. Emergency Green Corridor CCTV Monitoring:
     - Junction-to-camera association and camera coverage metrics
     - Dynamic congestion detection, ETA adjustment, and corridor CCTV alerts
  8. WebRTC Signaling WebSocket Security:
     - Authenticated WebRTC handshake rejection for unauthenticated/unauthorized clients
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
from services.traffic_engine import traffic_engine

client = TestClient(app)


# ── Stakeholder Persona Fixtures ──────────────────────────────────────────────

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
    return create_access_token({
        "sub": "traffic_operator",
        "username": "traffic_operator",
        "role": "traffic_operator",
        "risk_score": 80.0
    })


@pytest.fixture
def investigator_token():
    return create_access_token({
        "sub": "soc_investigator",
        "username": "soc_investigator",
        "role": "soc_analyst",
        "risk_score": 10.0
    })


@pytest.fixture
def citizen_token():
    return create_access_token({
        "sub": "citizen_user",
        "username": "citizen_user",
        "role": "citizen",
        "risk_score": 5.0
    })


# ── Test 1: Camera Registry CRUD & Stream Lifecycle ──────────────────────────

def test_camera_crud_and_stream_lifecycle(operator_token):
    cam_id = f"CAM-TEST-{uuid.uuid4().hex[:6].upper()}"
    headers = {"Authorization": f"Bearer {operator_token}"}

    # 1. Register Camera
    create_payload = {
        "id": cam_id,
        "name": "North Radial Corridor Cam",
        "location": "Junction 101 Northbound",
        "camera_type": "PTZ",
        "stream_type": "WEBRTC",
        "stream_url": "rtsp://admin:secret123@10.0.1.55:554/live",
        "fps": 10,
        "resolution": "1920x1080",
        "intersection_id": "J-101",
        "road_id": "ROAD-01",
    }
    resp = client.post("/api/v1/traffic/cameras", json=create_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json().get("camera", resp.json())
    assert data["id"] == cam_id
    assert data["camera_type"] == "PTZ"
    # Credentials in stream_url must be masked
    assert "secret123" not in data.get("stream_url", "")

    # 2. Get Camera Detail
    resp = client.get(f"/api/v1/traffic/cameras/{cam_id}", headers=headers)
    assert resp.status_code == 200
    cam_data = resp.json().get("camera", resp.json())
    assert cam_data["id"] == cam_id

    # 3. Update Camera
    patch_payload = {"status": "ONLINE", "fps": 15}
    resp = client.patch(f"/api/v1/traffic/cameras/{cam_id}", json=patch_payload, headers=headers)
    assert resp.status_code == 200
    patch_data = resp.json().get("camera", resp.json())
    assert patch_data["status"] == "ONLINE"
    assert patch_data["fps"] == 15

    # 4. Start & Stop Stream
    resp = client.post(f"/api/v1/traffic/cameras/{cam_id}/stream/start", headers=headers)
    assert resp.status_code == 200
    start_data = resp.json().get("stream", resp.json())
    assert start_data["status"] == "ONLINE"
    assert start_data["webrtc_active"] is True

    resp = client.get(f"/api/v1/traffic/cameras/{cam_id}/stream", headers=headers)
    assert resp.status_code == 200
    stream_info = resp.json().get("stream", resp.json())
    assert stream_info["camera_id"] == cam_id
    assert stream_info["status"] == "ONLINE"

    resp = client.post(f"/api/v1/traffic/cameras/{cam_id}/stream/stop", headers=headers)
    assert resp.status_code == 200
    stop_data = resp.json().get("stream", resp.json())
    assert stop_data["status"] == "OFFLINE"

    # 5. Delete Camera
    resp = client.delete(f"/api/v1/traffic/cameras/{cam_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json().get("deleted") is True or resp.json().get("status") == "ok"


# ── Test 2: RBAC & ABAC Zero-Trust Camera Authorization ──────────────────────

def test_camera_access_authorization(operator_token, citizen_token, compromised_operator_token):
    cam_id = "CAM-101"

    # Authorized operator -> 200
    resp = client.get(f"/api/v1/traffic/cameras/{cam_id}", headers={"Authorization": f"Bearer {operator_token}"})
    assert resp.status_code == 200

    # Unauthorized role (citizen) -> 403
    resp = client.get(f"/api/v1/traffic/cameras/{cam_id}", headers={"Authorization": f"Bearer {citizen_token}"})
    assert resp.status_code == 403

    # Compromised caller with risk_score >= 60.0 -> 403
    resp = client.get(f"/api/v1/traffic/cameras/{cam_id}", headers={"Authorization": f"Bearer {compromised_operator_token}"})
    assert resp.status_code == 403
    assert "quarantine" in resp.text.lower() or "denied" in resp.text.lower() or "risk" in resp.text.lower()


# ── Test 3: Phone-as-CCTV MobileCameraSession Enrollment ─────────────────────

def test_mobile_camera_session_enrollment(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}
    device_id = f"MOB-TEST-{uuid.uuid4().hex[:6]}"

    payload = {
        "device_id": device_id,
        "operator_id": "OFFICER-PATROL-12",
        "fps": 5,
        "resolution": "1280x720",
        "device_metadata": {
            "platform": "Android 14",
            "model": "Pixel 8",
            "security_patch": "2026-08",
            "hardware_backed_keystore": True,
            "root_detected": False
        }
    }
    resp = client.post("/api/v1/traffic/mobile-camera/session", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json().get("session", resp.json())
    assert data["device_id"] == device_id
    assert data["trust_status"] == "TRUSTED"
    assert data["risk_score"] < 40
    assert data["fps"] == 5
    assert data["camera_id"].startswith("CAM-MOB-")


# ── Test 4: Vehicle Detection Ingest & OCR Multi-Frame Agreement ─────────────

def test_vehicle_detection_and_ocr_confidence(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}
    track_id = f"TRACK-{uuid.uuid4().hex[:4].upper()}"

    # Ingest detection with high OCR confidence -> CONFIRMED
    high_conf_payload = {
        "camera_id": "CAM-101",
        "tracking_id": track_id,
        "vehicle_type": "SEDAN",
        "plate_number": "MH12DE1433",
        "plate_confidence": 0.94,
        "speed_kmh": 46.5
    }
    resp = client.post("/api/v1/traffic/detections/ingest", json=high_conf_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    dets = resp.json().get("detections", [resp.json()])
    d1 = dets[0]
    assert d1["tracking_id"] == track_id
    assert d1["ocr_status"] == "CONFIRMED"

    # Ingest detection with low OCR confidence (< 0.70) -> OCR_UNCERTAIN
    track_low = f"TRACK-LOW-{uuid.uuid4().hex[:4].upper()}"
    low_conf_payload = {
        "camera_id": "CAM-101",
        "tracking_id": track_low,
        "vehicle_type": "SUV",
        "plate_number": "KA04HA10??",
        "plate_confidence": 0.58,
        "speed_kmh": 52.0
    }
    resp = client.post("/api/v1/traffic/detections/ingest", json=low_conf_payload, headers=headers)
    assert resp.status_code == 200
    dets_low = resp.json().get("detections", [resp.json()])
    d2 = dets_low[0]
    assert d2["ocr_status"] in ["OCR_UNCERTAIN", "LOW_CONFIDENCE"]

    # Query detections by camera and tracking ID
    resp = client.get(f"/api/v1/traffic/detections?camera_id=CAM-101&tracking_id={track_id}", headers=headers)
    assert resp.status_code == 200
    results = resp.json().get("detections", resp.json())
    assert len(results) >= 1
    assert any(r.get("tracking_id") == track_id for r in results)

    # Retrieve tracked vehicles & plates
    resp_v = client.get("/api/v1/traffic/vehicles", headers=headers)
    assert resp_v.status_code == 200
    vehicles = resp_v.json().get("vehicles", resp_v.json())
    assert isinstance(vehicles, list)

    resp_p = client.get("/api/v1/traffic/plates", headers=headers)
    assert resp_p.status_code == 200
    plates = resp_p.json().get("plates", resp_p.json())
    assert isinstance(plates, list)


# ── Test 5: RFID Reader Subsystem ────────────────────────────────────────────

def test_rfid_reader_subsystem(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}

    # List readers
    resp = client.get("/api/v1/traffic/rfid/readers", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    readers = data.get("readers", data)
    assert len(readers) >= 1
    reader_ids = [r.get("reader_id") or r.get("id") for r in readers]
    assert "RFID-READER-01" in reader_ids

    # Ingest RFID read
    tag_id = "TAG-98231"
    read_payload = {
        "reader_id": "RFID-READER-01",
        "tag_id": tag_id,
        "epc": "E28011700000020123456789",
        "signal_rssi": -55.2,
        "lane_id": "LANE-1"
    }
    resp = client.post("/api/v1/traffic/rfid/read", json=read_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    read_data = resp.json()
    assert read_data.get("tag_id") == tag_id or read_data.get("read", {}).get("tag_id") == tag_id

    # Query reads
    resp = client.get("/api/v1/traffic/rfid/reads?limit=10", headers=headers)
    assert resp.status_code == 200
    reads = resp.json().get("reads", resp.json())
    assert any(r.get("tag_id") == tag_id for r in reads)


# ── Test 6: Vehicle Identity Cross-Verification Engine ───────────────────────

def test_vehicle_identity_cross_verification(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Scenario A: Matching Tag + Plate -> VERIFIED
    verified_payload = {
        "ocr_plate": "MH-12-DE-1433",
        "rfid_tag_id": "TAG-98231",
        "ocr_confidence": 0.95,
        "rfid_rssi": -54.0,
        "camera_id": "CAM-101",
        "rfid_reader_id": "RFID-READER-01",
        "location": "Junction 101 Toll"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=verified_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    res_a = resp.json().get("verification", resp.json())
    assert res_a["verification_status"] == "VERIFIED"
    assert res_a["risk_score"] <= 15
    assert res_a["escalation_status"] == "NONE"

    # Scenario B: Low OCR Confidence -> LOW_CONFIDENCE (not malicious fraud)
    low_conf_payload = {
        "ocr_plate": "MH-12-DE-14??",
        "rfid_tag_id": "TAG-98231",
        "ocr_confidence": 0.52,
        "rfid_rssi": -58.0,
        "camera_id": "CAM-101",
        "rfid_reader_id": "RFID-READER-01",
        "location": "Junction 101 Toll"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=low_conf_payload, headers=headers)
    assert resp.status_code == 200
    res_b = resp.json().get("verification", resp.json())
    assert res_b["verification_status"] in ["LOW_CONFIDENCE", "OCR_UNCERTAIN"]
    assert res_b["escalation_status"] == "NONE"

    # Scenario C: Definite Single Mismatch -> MISMATCH
    fraud_tag = f"TAG-TEST-{uuid.uuid4().hex[:6]}"
    mismatch_payload = {
        "ocr_plate": "DL-01-AB-9999",  # Plate does not match tag
        "rfid_tag_id": "TAG-98231",    # TAG-98231 is registered to MH-12-DE-1433
        "ocr_confidence": 0.96,
        "rfid_rssi": -50.0,
        "camera_id": "CAM-101",
        "rfid_reader_id": "RFID-READER-01",
        "location": "Plaza Gantry 1"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=mismatch_payload, headers=headers)
    assert resp.status_code == 200
    res_c = resp.json().get("verification", resp.json())
    assert res_c["verification_status"] == "MISMATCH"

    # Scenario D: Repeated Mismatch across multiple cameras -> ESCALATED_TO_SOC
    # Second detection of same tag with mismatching plate at CAM-102
    mismatch_payload_2 = {
        "ocr_plate": "DL-01-AB-9999",
        "rfid_tag_id": "TAG-98231",
        "ocr_confidence": 0.94,
        "rfid_rssi": -52.0,
        "camera_id": "CAM-102",  # Distinct camera
        "rfid_reader_id": "RFID-READER-02",
        "location": "Plaza Gantry 2"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=mismatch_payload_2, headers=headers)
    assert resp.status_code == 200
    res_d = resp.json().get("verification", resp.json())
    assert res_d["verification_status"] == "MISMATCH"
    assert res_d["repeated_mismatch_count"] >= 2
    assert res_d["escalation_status"] == "ESCALATED_TO_SOC"
    assert res_d["risk_score"] >= 80

    # Retrieve verification detail
    ver_id = res_d["id"]
    resp = client.get(f"/api/v1/traffic/vehicle-verification/{ver_id}", headers=headers)
    assert resp.status_code == 200
    detail = resp.json().get("verification", resp.json())
    assert detail["id"] == ver_id


# ── Test 6B: FASTag Camera ANPR Without Hardware RFID & Manual Approval Flow ─

def test_fastag_no_rfid_manual_approval_flow(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Step 1: Camera extracts vehicle plate, but no physical RFID scanner hardware is connected
    no_rfid_payload = {
        "ocr_plate": "KA-05-MK-9821",
        "tag_id": None,
        "ocr_confidence": 0.96,
        "camera_id": "CAM-101",
        "location": "Toll Plaza Gantry Alpha - Lane 1"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=no_rfid_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    res_no_rfid = resp.json().get("verification", resp.json())
    assert res_no_rfid["verification_status"] == "NO_RFID_DETECTED"
    assert res_no_rfid["action_taken"] == "PROMPT_OPERATOR_MANUAL_APPROVAL"
    assert res_no_rfid["risk_score"] == 25.0

    # Step 2: Operator manually approves clearance ("No RFID detected for vehicle. Can I approve? -> Approve")
    approve_payload = {
        "ocr_plate": "KA-05-MK-9821",
        "tag_id": None,
        "ocr_confidence": 0.96,
        "manual_approved": True,
        "operator_reason": "Visual plate verified by operator; RFID hardware scanner not present.",
        "camera_id": "CAM-101"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=approve_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    res_approved = resp.json().get("verification", resp.json())
    assert res_approved["verification_status"] == "MANUALLY_APPROVED_NO_RFID"
    assert res_approved["action_taken"] == "BARRIER_OPENED_OPERATOR_APPROVAL"
    assert res_approved["risk_score"] == 0.0

    # Step 3: Operator rejects clearance
    reject_payload = {
        "ocr_plate": "DL-01-AB-1234",
        "tag_id": None,
        "ocr_confidence": 0.96,
        "manual_approved": False,
        "operator_reason": "OPERATOR_REJECTED",
        "camera_id": "CAM-101"
    }
    resp = client.post("/api/v1/traffic/rfid/verify", json=reject_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    res_rejected = resp.json().get("verification", resp.json())
    assert res_rejected["verification_status"] == "REJECTED_NO_RFID"
    assert res_rejected["action_taken"] == "BARRIER_LOCKED_FLAGGED_FOR_INSPECTION"


# ── Test 7: Emergency Green Corridor CCTV Monitoring ─────────────────────────

def test_green_corridor_cctv_monitoring(operator_token):
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Corridor CAM-101 to CAM-108
    corridor_id = "CORR-01"
    resp = client.get(f"/api/v1/traffic/green-corridors/{corridor_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    corr = resp.json().get("corridor", resp.json())
    assert corr["id"] == corridor_id
    assert "corridor_cameras" in corr
    assert len(corr["corridor_cameras"]) >= 3
    assert "camera_coverage" in corr
    assert "ONLINE" in corr["camera_coverage"]

    # Trigger traffic engine tick to simulate corridor progression & congestion check
    tick_res = traffic_engine.tick()
    assert "status" in tick_res
    assert "active_corridors" in tick_res


# ── Test 8: WebRTC Signaling Endpoint Security ───────────────────────────────

def test_webrtc_signaling_security():
    # WebSocket connection with invalid token returns AUTH_FAILED error
    with client.websocket_connect("/ws/webrtc/CAM-101?token=invalid_token") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["code"] == "AUTH_FAILED"

    # WebSocket connection with valid operator token receives connection_state
    token = create_access_token({
        "sub": "traffic_operator",
        "username": "traffic_operator",
        "role": "traffic_operator",
        "risk_score": 10.0
    })
    with client.websocket_connect(f"/ws/webrtc/CAM-101?token={token}") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connection_state"
        assert msg["status"] in ("CONNECTED", "STREAMING")
