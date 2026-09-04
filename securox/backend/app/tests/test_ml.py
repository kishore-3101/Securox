import pytest
from data.schema import CanonicalEvent
from ml.unified_detector import unified_detector

def test_unified_detector_anomaly_and_classifier():
    evt = CanonicalEvent(
        source_ip="185.220.101.5",
        destination_ip="10.40.0.1",
        source_port=44321,
        destination_port=80,
        protocol="TCP",
        bytes_in=1500000,
        bytes_out=2000,
        packets=28000,
        duration=0.01,
        request_rate=2800.0,
        error_rate=0.85,
        asset_id="TRAFFIC_CONTROL",
        attack_type="DDOS",
        label=1
    )
    res = unified_detector.analyze_event(evt)
    assert "anomaly_score" in res
    assert "attack_type" in res
    assert "attack_confidence" in res
    assert 0.0 <= res["anomaly_score"] <= 1.0
    assert res["attack_type"] in ["DDOS", "DOS", "BENIGN", "PORT_SCAN", "BRUTE_FORCE", "INFILTRATION"]

def test_unified_detector_benign():
    evt = CanonicalEvent(
        source_ip="10.50.0.10",
        destination_ip="10.50.0.1",
        source_port=52110,
        destination_port=80,
        protocol="TCP",
        bytes_in=1500,
        bytes_out=800,
        packets=10,
        duration=0.5,
        request_rate=20.0,
        error_rate=0.0,
        asset_id="TRAFFIC_CONTROL",
        attack_type="BENIGN",
        label=0
    )
    res = unified_detector.analyze_event(evt)
    assert res["anomaly_score"] < 0.80
