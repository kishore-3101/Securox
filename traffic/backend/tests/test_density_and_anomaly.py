import pytest
from services.traffic_intelligence import traffic_intelligence

def test_congestion_free_flow():
    analysis = traffic_intelligence.calculate_congestion(
        current_volume=120,
        capacity=400,
        current_speed=95.0,
        speed_limit=100.0,
        lanes=4
    )
    assert analysis.congestion_level in ["FREE_FLOW", "MODERATE"]
    assert analysis.congestion_score < 40.0
    assert analysis.color_code in ["#10b981", "#f59e0b"]

def test_congestion_critical():
    analysis = traffic_intelligence.calculate_congestion(
        current_volume=450,
        capacity=400,
        current_speed=15.0,
        speed_limit=100.0,
        lanes=4,
        queue_length=25
    )
    assert analysis.congestion_level in ["SEVERE", "CRITICAL"]
    assert analysis.congestion_score >= 70.0
    assert analysis.severity in ["HIGH", "CRITICAL"]

def test_sensor_disagreement_anomaly():
    res = traffic_intelligence.detect_traffic_anomaly(
        road_id="ROAD-NH44-01",
        current_volume=380,
        current_speed=40.0,
        sensor_reading=0  # Disagreement: sensor says 0
    )
    assert res.is_anomaly is True
    assert res.anomaly_type == "SENSOR_DISAGREEMENT"
    assert res.severity == "HIGH"
    assert "Sensor reads 0" in res.reason

def test_sudden_traffic_surge():
    res = traffic_intelligence.detect_traffic_anomaly(
        road_id="ROAD-NH44-01",
        current_volume=580,  # High surge above 280 baseline
        current_speed=35.0
    )
    assert res.is_anomaly is True
    assert res.anomaly_type == "SUDDEN_TRAFFIC_SURGE"
