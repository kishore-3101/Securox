"""
Securox Healthcare Domain — Complete Operational Subsystems Test Suite
Tests:
  1. Patient Registration, Demographics, & Department Assignment
  2. Doctor & Nurse Assignment Scoping & BOLA Enforcement
  3. Clinical Privacy Shield: Reception & Billing restricted from clinical records & diagnoses
  4. Emergency Break-Glass Access:
     - Allows clinician emergency access
     - Immediately logs BREAK_GLASS event
     - Increases user risk score (+35.0)
     - Creates HIGH priority SOC security incident
     - Preserves immutable audit evidence
  5. Appointments: booking, listing, status transitions
  6. Inpatient Admissions & Bed Management: admitting, ward/bed allocator, discharge
  7. LIS / Laboratory: ordering stat/routine panels, submitting results with abnormal flag
  8. Pharmacy: prescription generation, drug dispensing
  9. Billing & TPA: insurance claims, invoice generation, cashless settlement
  10. Emergency & Paramedic Management: CAD dispatch, pre-hospital vitals transmission, Green Corridor preemption
  11. IoMT Security: device cartography, telemetry anomaly scanning, microsegmentation isolation
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from auth.jwt_auth import create_access_token

client = TestClient(app)

@pytest.fixture
def doctor_token():
    return create_access_token({
        "sub": "doctor",
        "username": "doctor",
        "role": "doctor",
        "department": "Cardiology",
        "assigned_patients": ["P-1001"]
    })

@pytest.fixture
def nurse_token():
    return create_access_token({
        "sub": "nurse",
        "username": "nurse",
        "role": "nurse",
        "department": "Cardiology",
        "assigned_patients": ["P-1001"]
    })

@pytest.fixture
def reception_token():
    return create_access_token({
        "sub": "reception",
        "username": "reception",
        "role": "reception",
        "department": "Front Desk"
    })

@pytest.fixture
def billing_token():
    return create_access_token({
        "sub": "billing",
        "username": "billing",
        "role": "billing_staff",
        "department": "Revenue Cycle"
    })

@pytest.fixture
def lab_token():
    return create_access_token({
        "sub": "lab_tech",
        "username": "lab_tech",
        "role": "lab_technician",
        "department": "Biochemistry"
    })

@pytest.fixture
def pharmacist_token():
    return create_access_token({
        "sub": "pharmacist",
        "username": "pharmacist",
        "role": "pharmacist",
        "department": "Central Pharmacy"
    })

@pytest.fixture
def paramedic_token():
    return create_access_token({
        "sub": "paramedic",
        "username": "paramedic",
        "role": "paramedic",
        "department": "Emergency Medical Services"
    })

@pytest.fixture
def security_token():
    return create_access_token({
        "sub": "hospital_sec",
        "username": "hospital_sec",
        "role": "hospital_security",
        "department": "Physical & Cyber Safety"
    })

def test_patient_registration_by_reception(reception_token):
    payload = {
        "name": "Lakshmi Narayanan",
        "age": 52,
        "gender": "Female",
        "department": "Cardiology",
        "room_bed": "Ward-3 / Bed-08",
        "diagnosis": "Unstable Angina",
        "condition": "GUARDED",
        "assigned_doctor_id": "doctor",
        "assigned_nurse_id": "nurse",
        "hospital_id": "H001"
    }
    resp = client.post(
        "/api/healthcare/patients",
        json=payload,
        headers={"Authorization": f"Bearer {reception_token}"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "ok"
    assert "patient" in data
    assert data["patient"]["name"] == "Lakshmi Narayanan"
    assert data["patient"]["id"].startswith("P-")

def test_reception_clinical_privacy_shield(reception_token):
    resp = client.get(
        "/api/healthcare/patients/P-1001",
        headers={"Authorization": f"Bearer {reception_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["medical_records"] == []
    assert data["patient"]["diagnosis"] == "[CLINICAL_RESTRICTED]"

def test_billing_clinical_privacy_shield(billing_token):
    resp = client.get(
        "/api/healthcare/patients/P-1001",
        headers={"Authorization": f"Bearer {billing_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["medical_records"] == []
    assert data["patient"]["diagnosis"] == "[CLINICAL_RESTRICTED]"

def test_doctor_access_assigned_patient(doctor_token):
    resp = client.get(
        "/api/healthcare/patients/P-1001",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient"]["id"] == "P-1001"
    assert data["patient"]["diagnosis"] != "[CLINICAL_RESTRICTED]"

def test_doctor_cross_department_bola_blocked(doctor_token):
    resp = client.get(
        "/api/healthcare/patients/P-1004",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 403

def test_emergency_break_glass_endpoint(doctor_token):
    payload = {
        "patient_id": "P-1004",
        "reason": "Acute Myocardial Infarction in transit to Cath Lab"
    }
    resp = client.post(
        "/api/healthcare/break-glass",
        json=payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "BREAK_GLASS_AUTHORIZED"
    assert data["new_user_risk"] >= 45.0
    assert "INC-BG-" in data["incident_id"]
    assert data["patient"]["id"] == "P-1004"

def test_break_glass_audit_logs(security_token):
    resp = client.get(
        "/api/healthcare/break-glass/logs",
        headers={"Authorization": f"Bearer {security_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "logs" in data
    assert len(data["logs"]) > 0

def test_appointment_lifecycle(reception_token, doctor_token):
    booking = {
        "patient_id": "P-1001",
        "department": "Cardiology",
        "doctor_id": "doctor",
        "reason": "Post-MI follow up and echo review",
        "hospital_id": "H001"
    }
    resp = client.post(
        "/api/healthcare/appointments",
        json=booking,
        headers={"Authorization": f"Bearer {reception_token}"}
    )
    assert resp.status_code == 200
    apt = resp.json()["appointment"]
    apt_id = apt["id"]
    assert apt["status"] == "SCHEDULED"

    resp_update = client.patch(
        f"/api/healthcare/appointments/{apt_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["new_status"] == "COMPLETED"

def test_admissions_and_discharge(reception_token, doctor_token):
    adm_payload = {
        "patient_id": "P-1002",
        "hospital_id": "H001",
        "department": "Cardiology",
        "room_bed": "ICU-Bed-03",
        "admission_type": "ICU",
        "admitting_doctor_id": "doctor",
        "assigned_nurse_id": "nurse"
    }
    resp = client.post(
        "/api/healthcare/admissions",
        json=adm_payload,
        headers={"Authorization": f"Bearer {reception_token}"}
    )
    assert resp.status_code == 200
    adm = resp.json()["admission"]
    adm_id = adm["id"]
    assert adm["status"] == "ADMITTED"

    resp_disc = client.post(
        f"/api/healthcare/admissions/{adm_id}/discharge",
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp_disc.status_code == 200
    assert resp_disc.json()["status"] == "DISCHARGED"

def test_lab_order_and_result(doctor_token, lab_token):
    order_payload = {
        "patient_id": "P-1001",
        "test_name": "High-Sensitivity Troponin-T",
        "category": "Cardiac Biomarkers",
        "priority": "STAT",
        "doctor_id": "doctor",
        "reference_range": "< 14 ng/L"
    }
    resp = client.post(
        "/api/healthcare/labs",
        json=order_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 200
    order = resp.json()["lab_order"]
    lab_id = order["id"]
    assert order["status"] == "ORDERED"

    result_payload = {
        "result_data": {"hs_cTnT": 142.5, "unit": "ng/L", "flag": "CRITICAL_HIGH"},
        "flagged_abnormal": True,
        "approved_by": "lab_tech"
    }
    resp_res = client.patch(
        f"/api/healthcare/labs/{lab_id}/result",
        json=result_payload,
        headers={"Authorization": f"Bearer {lab_token}"}
    )
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "COMPLETED"

def test_pharmacy_prescription_and_dispense(doctor_token, pharmacist_token):
    rx_payload = {
        "patient_id": "P-1001",
        "doctor_id": "doctor",
        "medication": "Ticagrelor 90mg",
        "dosage": "90 mg PO",
        "frequency": "BID",
        "duration": "30 days",
        "ddi_warning": "Monitor with concurrent Aspirin"
    }
    resp = client.post(
        "/api/healthcare/prescriptions",
        json=rx_payload,
        headers={"Authorization": f"Bearer {doctor_token}"}
    )
    assert resp.status_code == 200
    rx = resp.json()["prescription"]
    rx_id = rx["id"]

    resp_disp = client.patch(
        f"/api/healthcare/prescriptions/{rx_id}/dispense",
        json={"pharmacist_id": "pharmacist"},
        headers={"Authorization": f"Bearer {pharmacist_token}"}
    )
    assert resp_disp.status_code == 200
    assert resp_disp.json()["status"] == "DISPENSED"

def test_billing_invoice_and_settlement(billing_token):
    inv_payload = {
        "patient_id": "P-1001",
        "hospital_id": "H001",
        "total_amount": 78500.00,
        "insurance_claim_amount": 65000.00,
        "patient_payable": 13500.00,
        "payment_method": "INSURANCE_TPA",
        "line_items": [
            {"item": "Cath Lab Angiography", "amount": 55000.00},
            {"item": "Cardiac ICU (2 days)", "amount": 16000.00},
            {"item": "Stat Troponin Panels", "amount": 7500.00}
        ]
    }
    resp = client.post(
        "/api/healthcare/billing",
        json=inv_payload,
        headers={"Authorization": f"Bearer {billing_token}"}
    )
    assert resp.status_code == 200
    inv = resp.json()["invoice"]
    inv_id = inv["id"]

    resp_settle = client.post(
        f"/api/healthcare/billing/{inv_id}/settle",
        json={"payment_method": "UPI"},
        headers={"Authorization": f"Bearer {billing_token}"}
    )
    assert resp_settle.status_code == 200
    assert resp_settle.json()["status"] == "SETTLED"

def test_emergency_dispatch_and_vitals(paramedic_token):
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
    dsp = resp.json()["dispatch"]
    dsp_id = dsp["id"]

    resp_up = client.patch(
        f"/api/healthcare/emergency/dispatches/{dsp_id}",
        json={"status": "IN_TRANSIT", "vitals": {"hr": 96, "bp": "135/84", "spo2": 97}},
        headers={"Authorization": f"Bearer {paramedic_token}"}
    )
    assert resp_up.status_code == 200
    assert resp_up.json()["updates"]["status"] == "IN_TRANSIT"

def test_iomt_devices_and_isolation(security_token):
    resp = client.get(
        "/api/healthcare/iomt/devices",
        headers={"Authorization": f"Bearer {security_token}"}
    )
    assert resp.status_code == 200
    devices = resp.json()["devices"]
    assert len(devices) >= 4

    iso_payload = {
        "vlan_id": "QUARANTINE_VLAN_99",
        "reason": "Anomalous HL7 buffer overflow traffic detected"
    }
    resp_iso = client.post(
        "/api/healthcare/iomt/devices/IOMT-MON-12/isolate",
        json=iso_payload,
        headers={"Authorization": f"Bearer {security_token}"}
    )
    assert resp_iso.status_code == 200
    assert resp_iso.json()["status"] == "QUARANTINED"
    assert resp_iso.json()["quarantine_vlan"] == "QUARANTINE_VLAN_99"
