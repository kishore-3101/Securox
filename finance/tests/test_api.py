import pytest
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_api_assets():
    resp = requests.get(f"{BASE_URL}/api/assets", timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 12

def test_api_metrics():
    resp = requests.get(f"{BASE_URL}/api/metrics", timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert "accuracy" in data
    assert "f1_macro" in data or "macro_f1" in data

def test_api_threat_intel():
    resp = requests.get(f"{BASE_URL}/api/threat-intel/lookup/185.220.101.5", timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("is_threat") is True

def test_api_events_post():
    payload = {
        "source_ip": "185.220.101.5",
        "destination_ip": "10.40.0.1",
        "destination_port": 80,
        "protocol": "TCP",
        "bytes_in": 1500000,
        "bytes_out": 2000,
        "packets": 28000,
        "duration": 0.01,
        "request_rate": 2800.0,
        "error_rate": 0.85,
        "asset_id": "TRAFFIC_CONTROL",
        "attack_type": "DDOS",
        "label": 1
    }
    resp = requests.post(f"{BASE_URL}/api/events", json=payload, timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert "alert_id" in data
    assert "risk_score" in data
    assert data["severity"] in ["HIGH", "CRITICAL", "CATASTROPHIC"]
