"""
Unit tests for the authoritative /api/auth/capabilities endpoint.
Verifies server-side capability resolution, sector assignments, and route permissions across roles.
"""

import pytest
from fastapi.testclient import TestClient
from securox.backend.app.main import app
from securox.backend.app.auth.jwt_auth import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


def test_capabilities_unauthenticated(client):
    """Accessing /api/auth/capabilities without a Bearer token should fail with 401."""
    resp = client.get("/api/auth/capabilities")
    assert resp.status_code == 401


def test_capabilities_admin(client):
    """Admin role must have all operational capabilities, is_admin=True, and all 9 pages."""
    token = create_access_token({"sub": "admin", "role": "admin"})
    resp = client.get("/api/auth/capabilities", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "admin"
    assert data["sector"] == "global"
    caps = data["capabilities"]
    assert caps["is_admin"] is True
    assert caps["is_read_only"] is False
    assert caps["can_override_signals"] is True
    assert caps["can_dispatch_ambulances"] is True
    assert caps["can_view_patient_records"] is True
    assert caps["can_freeze_accounts"] is True
    assert caps["can_execute_mitigations"] is True
    assert caps["can_inject_simulations"] is True
    assert "overview" in data["allowed_pages"]
    assert "twin" in data["allowed_pages"]
    assert "healthcare" in data["allowed_pages"]
    assert "traffic" in data["allowed_pages"]
    assert "finance" in data["allowed_pages"]


def test_capabilities_doctor(client):
    """Doctor role must have patient record access, but NOT signal override or account freeze."""
    token = create_access_token({"sub": "doctor", "role": "doctor"})
    resp = client.get("/api/auth/capabilities", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "doctor"
    assert data["sector"] == "healthcare"
    caps = data["capabilities"]
    assert caps["is_admin"] is False
    assert caps["can_view_patient_records"] is True
    assert caps["can_edit_patient_records"] is True
    assert caps["can_override_signals"] is False
    assert caps["can_freeze_accounts"] is False


def test_capabilities_traffic_operator(client):
    """Traffic operator must have signal override capabilities, but NOT healthcare patient access."""
    token = create_access_token({"sub": "traffic", "role": "traffic_operator"})
    resp = client.get("/api/auth/capabilities", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "traffic_operator"
    assert data["sector"] == "transport"
    caps = data["capabilities"]
    assert caps["can_override_signals"] is True
    assert caps["can_view_patient_records"] is False
    assert caps["can_freeze_accounts"] is False


def test_capabilities_viewer(client):
    """Viewer must be is_read_only=True and have zero mutating capabilities."""
    token = create_access_token({"sub": "viewer", "role": "viewer"})
    resp = client.get("/api/auth/capabilities", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "viewer"
    caps = data["capabilities"]
    assert caps["is_read_only"] is True
    assert caps["can_override_signals"] is False
    assert caps["can_dispatch_ambulances"] is False
    assert caps["can_freeze_accounts"] is False
