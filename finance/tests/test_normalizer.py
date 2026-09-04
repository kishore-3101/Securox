import pytest
from data.normalizer import DatasetNormalizer
from data.schema import CanonicalEvent

def test_normalize_cicids2017():
    row = {
        "Destination Port": 80,
        "Flow Duration": 50000,
        "Total Fwd Packets": 100,
        "Total Backward Packets": 50,
        "Total Length of Fwd Packets": 15000,
        "Total Length of Bwd Packets": 25000,
        "Flow Bytes/s": 800000,
        "Flow Packets/s": 3000,
        "Label": "DDoS"
    }
    evt = DatasetNormalizer.normalize_cicids2017(row)
    assert isinstance(evt, CanonicalEvent)
    assert evt.attack_type == "DDOS"
    assert evt.label == 1
    assert evt.destination_port == 80

def test_normalize_unsw_nb15():
    row = {
        "srcip": "172.16.0.5",
        "dstip": "10.0.0.1",
        "sport": 54321,
        "dsport": 443,
        "proto": "tcp",
        "dur": 0.5,
        "sbytes": 5000,
        "dbytes": 8000,
        "spkts": 25,
        "dpkts": 30,
        "attack_cat": "Generic",
        "label": 1
    }
    evt = DatasetNormalizer.normalize_unsw_nb15(row)
    assert isinstance(evt, CanonicalEvent)
    assert evt.label == 1
    assert evt.protocol == "TCP"

def test_normalize_nsl_kdd():
    row = {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "src_bytes": 215,
        "dst_bytes": 450,
        "count": 10,
        "serror_rate": 0.0,
        "class": "normal"
    }
    evt = DatasetNormalizer.normalize_nsl_kdd(row)
    assert isinstance(evt, CanonicalEvent)
    assert evt.attack_type == "BENIGN"
    assert evt.label == 0
