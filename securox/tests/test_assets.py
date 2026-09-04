import pytest
from backend.assets.registry import asset_registry

def test_asset_registry_counts():
    assets = asset_registry.get_all()
    assert len(assets) == 12
    ids = [a["asset_id"] for a in assets]
    assert "POWER_GRID" in ids
    assert "TRAFFIC_CONTROL" in ids
    assert "HEALTHCARE" in ids
    assert "EMERGENCY_SERVICES" in ids
    assert "COMM_NETWORK" in ids

def test_downstream_blast_radius():
    deps = asset_registry.get_downstream_dependents("POWER_GRID")
    assert len(deps) > 0
    # Power Grid failure cascades to Comm Network, Healthcare, Traffic Control, etc.
    assert any(d in deps for d in ["COMM_NETWORK", "HEALTHCARE", "TRAFFIC_CONTROL", "WATER_MANAGEMENT"])

def test_asset_status_update():
    asset_registry.update_status("TRAFFIC_CONTROL", "degraded")
    a = asset_registry.get_asset("TRAFFIC_CONTROL")
    assert a["status"] == "degraded"
    asset_registry.update_status("TRAFFIC_CONTROL", "healthy")
