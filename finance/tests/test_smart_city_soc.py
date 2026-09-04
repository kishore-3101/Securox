import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app

client = TestClient(app)

def test_canonical_scenarios_01_to_06():
    """Verify all 6 canonical attack scenarios trigger and return valid telemetry & risk state."""
    scenarios = ["01", "02", "03", "04", "05", "06"]
    for sc_id in scenarios:
        resp = client.post(f"/api/simulate/scenario/{sc_id}")
        assert resp.status_code == 200, f"Scenario {sc_id} failed with {resp.text}"
        data = resp.json()
        assert data.get("status") == "SUCCESS"
        assert "target_asset" in data
        assert "scenario_name" in data
        assert "city_risk" in data
        assert data["city_risk"] > 0

def test_restore_normal_operations():
    """Verify restoring normal operations resets city risks and returns nominal state."""
    resp = client.post("/api/simulate/normal-operations")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "SUCCESS"
    assert data.get("city_risk") == 18.0
    assert "restored_assets_count" in data
    assert data["restored_assets_count"] >= 8

def test_custom_scenario_builder():
    """Verify the interactive custom attack scenario builder runs through the live pipeline."""
    payload = {
        "target_asset": "WATER_SUPPLY",
        "attack_type": "SCADA_INJECTION",
        "severity": "HIGH",
        "intensity": 0.85,
        "duration": 30,
        "cascade": True
    }
    resp = client.post("/api/simulate/custom", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "SUCCESS"
    assert data.get("target_asset") == "WATER_SUPPLY"
    assert "alert" in data
    assert data["alert"]["severity"] in ["HIGH", "CRITICAL"]

def test_multi_stage_campaigns_api():
    """Verify campaign detection and retrieval of multi-stage attack campaigns."""
    # First inject scenario 06 to ensure active campaign exists
    client.post("/api/simulate/scenario/06")
    resp = client.get("/api/campaigns")
    assert resp.status_code == 200
    data = resp.json()
    campaigns = data if isinstance(data, list) else data.get("campaigns", [])
    assert len(campaigns) >= 1
    first_camp = campaigns[0]
    assert "id" in first_camp or "campaign_id" in first_camp

def test_what_if_cascade_simulation():
    """Verify what-if cascading failure simulator computes blast radius and dependent tree."""
    payload = {
        "target_asset": "POWER_GRID",
        "failure_type": "CYBER_ATTACK_OUTAGE"
    }
    resp = client.post("/api/simulate/what-if", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("target_asset") == "POWER_GRID"
    assert "blast_radius_percent" in data
    assert data["blast_radius_percent"] > 0
    assert "impacted_assets_count" in data
    assert "cascading_dependents" in data
    assert "recommended_action" in data
    assert len(data["cascading_dependents"]) > 0

def test_response_execution_with_state_transition():
    """Verify mitigation actions alter asset risk and return verifiable before/after state transition."""
    # Ensure asset has high risk first
    client.post("/api/simulate/scenario/02")
    payload = {
        "asset_id": "POWER_GRID",
        "action_type": "ISOLATE_ASSET",
        "source_ip": "198.51.100.44",
        "operator": "test_operator"
    }
    resp = client.post("/api/response/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ["SUCCESS", "VERIFIED"]
    assert "before_risk" in data
    assert "after_risk" in data
    assert data["after_risk"] < data["before_risk"], "Mitigation should verifiably reduce risk"
    assert "merkle_hash" in data
    assert data.get("verification_status") == "VERIFIED"

def test_data_lab_api():
    """Verify dataset lab listing and replay runner."""
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 4
    assert any(d.get("id") == "cicids2017" for d in data)

    # Replay test
    replay_payload = {
        "dataset_name": "cicids2017",
        "speed_multiplier": 5,
        "target_asset": "TRAFFIC_SYSTEM"
    }
    r_resp = client.post("/api/datasets/replay", json=replay_payload)
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data.get("status") in ["SUCCESS", "STREAMING", "RUNNING"]
    assert r_data.get("dataset") == "cicids2017"

def test_global_search_api():
    """Verify global search queries across assets, alerts, and campaigns."""
    resp = client.get("/api/search", params={"q": "power"})
    assert resp.status_code == 200
    data = resp.json()
    assert "query" in data
    assert "alerts" in data
    assert "campaigns" in data

def test_incident_report_generation():
    """Verify formal incident report generation endpoint."""
    resp = client.get("/api/reports/incident", params={"asset": "POWER_GRID"})
    assert resp.status_code == 200
    data = resp.json()
    assert "incident_id" in data
    assert "classification" in data
    assert "mitre_tactics" in data
    assert "merkle_proof" in data

def test_rbac_roles_and_persona_switching():
    """Verify sector RBAC role listing and persona switching."""
    # List roles
    resp = client.get("/api/auth/roles")
    assert resp.status_code == 200
    data = resp.json()
    assert "roles" in data
    assert len(data["roles"]) >= 6
    role_ids = [r["id"] for r in data["roles"]]
    assert "admin" in role_ids
    assert "health_operator" in role_ids
    assert "traffic_operator" in role_ids
    assert "finance_investigator" in role_ids

    # Switch to Healthcare
    h_resp = client.post("/api/auth/switch-role", json={"role_or_username": "health"})
    assert h_resp.status_code == 200
    assert h_resp.json().get("role") == "health_operator"

    # Switch to Traffic
    t_resp = client.post("/api/auth/switch-role", json={"role_or_username": "traffic"})
    assert t_resp.status_code == 200
    assert t_resp.json().get("role") == "traffic_operator"

    # Switch to Finance
    f_resp = client.post("/api/auth/switch-role", json={"role_or_username": "finance"})
    assert f_resp.status_code == 200
    assert f_resp.json().get("role") == "finance_investigator"
