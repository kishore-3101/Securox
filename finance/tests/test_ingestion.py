import pytest
from datetime import datetime, timezone
from data.schema import CanonicalEvent, CanonicalEventModel, ATTACK_CLASSES

def test_canonical_event_instantiation():
    evt = CanonicalEvent(
        source_ip="192.168.1.100",
        destination_ip="10.50.0.1",
        source_port=44321,
        destination_port=80,
        protocol="TCP",
        bytes_in=1500000,
        bytes_out=2000,
        packets=25000,
        duration=0.01,
        request_rate=2500.0,
        error_rate=0.85,
        asset_id="TRAFFIC_CONTROL",
        attack_type="DDOS",
        label=1
    )
    assert evt.source_ip == "192.168.1.100"
    assert evt.destination_port == 80
    assert evt.attack_type == "DDOS"
    assert evt.label == 1
    d = evt.to_dict()
    assert isinstance(d, dict)
    assert d["attack_type"] == "DDOS"

def test_canonical_event_pydantic_validation():
    model = CanonicalEventModel(
        source_ip="10.0.0.5",
        destination_ip="10.10.0.1",
        destination_port=502,
        protocol="TCP",
        bytes_in=5000,
        bytes_out=500,
        packets=40,
        duration=0.1,
        asset_id="POWER_GRID",
        attack_type="BENIGN"
    )
    assert model.source_ip == "10.0.0.5"
    assert model.asset_id == "POWER_GRID"
    assert model.protocol == "TCP"
