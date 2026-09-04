"""
Securox Phase 1 Security Hardening Test Suite
Verifies:
  1. Universal unauthenticated rejection (401 Unauthorized across all sensitive endpoints)
  2. Strict privilege escalation blocking (403 Forbidden for unauthorized roles)
  3. Strict auditor read-only enforcement (VIEW allowed, UPDATE/CREATE/DELETE forbidden)
  4. Broken Object-Level Authorization (BOLA/IDOR) in Healthcare (cross-department blocking)
  5. Emergency Break-Glass mechanism for life-critical clinical access
  6. Broken Object-Level Authorization (BOLA/IDOR) in Smart Traffic (jurisdiction isolation)
  7. Broken Object-Level Authorization (BOLA/IDOR) in Finance (customer account isolation)
  8. Production secret key fail-fast enforcement
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from auth.jwt_auth import create_access_token, validate_production_secrets

client = TestClient(app)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Universal Unauthenticated Request Rejection (401 Unauthorized)
# ══════════════════════════════════════════════════════════════════════════════

def test_unauthenticated_healthcare_patients_blocked():
    """Unauthenticated calls to patient lists and records must return 401."""
    resp = client.get("/api/healthcare/patients")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.get("/api/healthcare/patients/P-1001")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


def test_unauthenticated_healthcare_mutations_blocked():
    """Unauthenticated calls to ambulance dispatch and clinical response must return 401."""
    resp = client.patch("/api/healthcare/ambulances/AMB-01/status", json={"status": "DISPATCHED"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/api/healthcare/response", json={"asset_id": "EHR_CORE_GATEWAY", "action_type": "ISOLATE"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


def test_unauthenticated_traffic_signal_overrides_blocked():
    """Unauthenticated calls to traffic signal override and green corridor must return 401."""
    resp = client.post("/api/traffic/signals/SIG-01/override", json={"mode": "ALL_RED", "duration_seconds": 60})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.patch("/api/traffic/signals/SIG-01/override", json={"target_state": "RED", "duration_sec": 60})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/api/traffic/green-corridor", json={"corridor_name": "Emergency Corridor", "priority_route": ["SIG-01"]})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


def test_unauthenticated_toll_overrides_blocked():
    """Unauthenticated calls to toll system overrides must return 401."""
    resp = client.post("/api/toll/TXN-101/override", json={"override_reason": "Emergency bypass"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


def test_unauthenticated_finance_endpoints_blocked():
    """Unauthenticated calls to accounts and transaction submissions must return 401."""
    resp = client.get("/api/finance/accounts")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.get("/api/finance/accounts/ACC-9001")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/api/finance/transactions", json={"account_id": "ACC-9001", "amount": 1000.0, "type": "DEBIT"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


def test_unauthenticated_security_governance_and_soc_blocked():
    """Unauthenticated calls to policies, incidents, and mitigations must return 401."""
    resp = client.get("/api/security/policies")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/api/incidents", json={"title": "Test Incident", "severity": "HIGH", "domain": "TRAFFIC"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.patch("/api/incidents/INC-001", json={"status": "RESOLVED"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    resp = client.post("/api/response/execute", json={"asset_id": "POWER_GRID", "action_type": "ISOLATE_ASSET"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Strict Privilege Escalation Blocking (403 Forbidden)
# ══════════════════════════════════════════════════════════════════════════════

def test_privilege_escalation_citizen_blocked_from_signal_override():
    """Citizen role cannot override smart traffic signals."""
    token = create_access_token({"sub": "citizen", "role": "citizen"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/traffic/signals/SIG-01/override",
        json={"mode": "ALL_RED", "duration_seconds": 60},
        headers=headers
    )
    assert resp.status_code == 403
    assert "Forbidden" in resp.text or "Permission Denied" in resp.text or "Access Denied" in resp.text


def test_privilege_escalation_citizen_blocked_from_finance_transactions():
    """Citizen role cannot post financial transactions."""
    token = create_access_token({"sub": "citizen", "role": "citizen"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/finance/transactions",
        json={"account_id": "ACC-9001", "amount": 50000.0, "type": "TRANSFER"},
        headers=headers
    )
    assert resp.status_code == 403


def test_privilege_escalation_viewer_blocked_from_ambulance_dispatch():
    """Citizen/viewer role cannot dispatch ambulances."""
    token = create_access_token({"sub": "citizen", "role": "citizen"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.patch(
        "/api/healthcare/ambulances/AMB-01/status",
        json={"status": "DISPATCHED"},
        headers=headers
    )
    assert resp.status_code == 403


def test_privilege_escalation_viewer_blocked_from_mitigation_execution():
    """Citizen/viewer role cannot execute cyber response actions."""
    token = create_access_token({"sub": "citizen", "role": "citizen"})
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/response/execute",
        json={"asset_id": "POWER_GRID", "action_type": "ISOLATE_ASSET"},
        headers=headers
    )
    assert resp.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# 3. Auditor Strictly Read-Only Enforcement
# ══════════════════════════════════════════════════════════════════════════════

def test_auditor_read_only_access_granted_for_view():
    """Auditors can view records across all domains (Healthcare, Finance, Security)."""
    token = create_access_token({"sub": "auditor", "role": "auditor"})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/healthcare/patients", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/finance/accounts", headers=headers)
    assert resp.status_code == 200

    resp = client.get("/api/security/policies", headers=headers)
    assert resp.status_code == 200


def test_auditor_mutations_strictly_blocked():
    """Auditors are strictly forbidden from modifying any resources."""
    token = create_access_token({"sub": "auditor", "role": "auditor"})
    headers = {"Authorization": f"Bearer {token}"}

    # Cannot create transactions
    resp = client.post(
        "/api/finance/transactions",
        json={"account_id": "ACC-9001", "amount": 100.0, "type": "CREDIT"},
        headers=headers
    )
    assert resp.status_code == 403
    assert "strictly read-only" in resp.text

    # Cannot create incidents
    resp = client.post(
        "/api/incidents",
        json={"title": "Auditor Test Incident", "severity": "LOW", "domain": "FINANCE"},
        headers=headers
    )
    assert resp.status_code == 403
    assert "strictly read-only" in resp.text

    # Cannot execute mitigations
    resp = client.post(
        "/api/response/execute",
        json={"asset_id": "POWER_GRID", "action_type": "ISOLATE_ASSET"},
        headers=headers
    )
    assert resp.status_code == 403
    assert "strictly read-only" in resp.text

    # Cannot override traffic signals
    resp = client.patch(
        "/api/traffic/signals/SIG-01/override",
        json={"target_state": "RED", "duration_sec": 30},
        headers=headers
    )
    assert resp.status_code == 403
    assert "strictly read-only" in resp.text


# ══════════════════════════════════════════════════════════════════════════════
# 4. Broken Object-Level Authorization (BOLA/IDOR) in Healthcare
# ══════════════════════════════════════════════════════════════════════════════

def test_healthcare_doctor_assigned_patient_access_allowed():
    """Doctor assigned to Cardiology can view assigned patient P-1001."""
    token = create_access_token({"sub": "doctor", "role": "doctor"})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/healthcare/patients/P-1001", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient"]["id"] == "P-1001"
    assert data["patient"]["department"] == "Cardiology"


def test_healthcare_doctor_unassigned_department_patient_blocked_bola():
    """Doctor in Cardiology is blocked from accessing Neurology patient P-1004 without break-glass."""
    token = create_access_token({"sub": "doctor", "role": "doctor"})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/healthcare/patients/P-1004", headers=headers)
    assert resp.status_code == 403
    assert "BOLA/IDOR" in resp.text or "department" in resp.text


# ══════════════════════════════════════════════════════════════════════════════
# 5. Healthcare Emergency Break-Glass Mechanism
# ══════════════════════════════════════════════════════════════════════════════

def test_healthcare_emergency_break_glass_access_granted():
    """Doctor accessing out-of-department patient with X-Emergency-Break-Glass is granted access with audit."""
    token = create_access_token({"sub": "doctor", "role": "doctor"})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Emergency-Break-Glass": "true"
    }

    resp = client.get("/api/healthcare/patients/P-1004", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["patient"]["id"] == "P-1004"
    assert data["patient"]["department"] == "Neurology"


# ══════════════════════════════════════════════════════════════════════════════
# 6. Broken Object-Level Authorization (BOLA/IDOR) in Smart Traffic
# ══════════════════════════════════════════════════════════════════════════════

def test_traffic_operator_jurisdiction_allowed_for_assigned_zone():
    """Traffic operator assigned to 'Central' zone can override signal SIG-01 (Central)."""
    token = create_access_token({
        "sub": "traffic_operator",
        "role": "traffic_operator",
        "jurisdiction": "Central"
    })
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.patch(
        "/api/traffic/signals/SIG-01/override",
        json={"target_state": "GREEN", "duration_sec": 45},
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["signal_id"] == "SIG-01"


def test_traffic_operator_jurisdiction_blocked_for_out_of_zone_bola():
    """Traffic operator assigned to 'Central' zone is blocked from overriding SIG-03 (North zone)."""
    token = create_access_token({
        "sub": "traffic_operator",
        "role": "traffic_operator",
        "jurisdiction": "Central"
    })
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.patch(
        "/api/traffic/signals/SIG-03/override",
        json={"target_state": "RED", "duration_sec": 45},
        headers=headers
    )
    assert resp.status_code == 403
    assert "BOLA/IDOR" in resp.text
    assert "Central" in resp.text
    assert "North" in resp.text


# ══════════════════════════════════════════════════════════════════════════════
# 7. Broken Object-Level Authorization (BOLA/IDOR) in Finance
# ══════════════════════════════════════════════════════════════════════════════

def test_customer_allowed_access_to_own_account():
    """Customer customer (CUST-501) can access own bank account ACC-9001."""
    token = create_access_token({
        "sub": "customer",
        "role": "customer",
        "customer_id": "CUST-501"
    })
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/finance/accounts/ACC-9001", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["account"]["id"] == "ACC-9001"
    assert data["account"]["customer_id"] == "CUST-501"


def test_customer_blocked_from_other_customer_account_bola():
    """Customer customer (CUST-501) is blocked from accessing customer CUST-502's account ACC-9002."""
    token = create_access_token({
        "sub": "customer",
        "role": "customer",
        "customer_id": "CUST-501"
    })
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/finance/accounts/ACC-9002", headers=headers)
    assert resp.status_code == 403
    assert "BOLA/IDOR" in resp.text or "another customer" in resp.text


# ══════════════════════════════════════════════════════════════════════════════
# 8. Production Secret Key Fail-Fast Enforcement
# ══════════════════════════════════════════════════════════════════════════════

def test_production_secret_key_fail_fast_when_missing():
    """When SECUROX_ENV=production and SECRET_KEY is empty/unset, startup must fail immediately."""
    original_env = os.environ.get("SECUROX_ENV")
    original_secret = os.environ.get("SECRET_KEY")

    try:
        os.environ["SECUROX_ENV"] = "production"
        os.environ["SECRET_KEY"] = ""
        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets(env="production", secret="")
        assert "FATAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)
    finally:
        if original_env is not None:
            os.environ["SECUROX_ENV"] = original_env
        else:
            os.environ.pop("SECUROX_ENV", None)

        if original_secret is not None:
            os.environ["SECRET_KEY"] = original_secret
        else:
            os.environ.pop("SECRET_KEY", None)


def test_production_secret_key_fail_fast_when_default():
    """When SECUROX_ENV=production and SECRET_KEY is the insecure default, startup must fail immediately."""
    original_env = os.environ.get("SECUROX_ENV")
    original_secret = os.environ.get("SECRET_KEY")

    try:
        os.environ["SECUROX_ENV"] = "production"
        os.environ["SECRET_KEY"] = "securox-super-secret-key-change-in-production-2024"
        with pytest.raises(RuntimeError) as excinfo:
            validate_production_secrets(env="production", secret="securox-super-secret-key-change-in-production-2024")
        assert "insecure" in str(excinfo.value)
    finally:
        if original_env is not None:
            os.environ["SECUROX_ENV"] = original_env
        else:
            os.environ.pop("SECUROX_ENV", None)

        if original_secret is not None:
            os.environ["SECRET_KEY"] = original_secret
        else:
            os.environ.pop("SECRET_KEY", None)
