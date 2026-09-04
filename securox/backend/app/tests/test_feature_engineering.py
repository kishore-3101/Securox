import pytest
import numpy as np
from data.schema import CanonicalEvent
from data.feature_engineering import pipeline, FEATURE_COLUMNS

def test_feature_extraction_vector():
    evt = CanonicalEvent(
        source_ip="192.168.1.5",
        destination_ip="10.50.0.1",
        source_port=50000,
        destination_port=80,
        protocol="TCP",
        bytes_in=10000,
        bytes_out=5000,
        packets=150,
        duration=0.2,
        request_rate=750.0,
        error_rate=0.05,
        asset_id="TRAFFIC_CONTROL",
        attack_type="BENIGN",
        label=0
    )
    vec = pipeline.extract_features_from_event(evt)
    assert isinstance(vec, np.ndarray)
    assert len(vec) == len(FEATURE_COLUMNS)
    assert not np.isnan(vec).any()
    assert not np.isinf(vec).any()
