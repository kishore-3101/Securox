import pytest
from services.event_bus import NormalizedEvent
from services.correlation_engine import ThreatCorrelationEngine
from services.risk_engine import risk_engine
from services.cyber_engine import cyber_engine

def test_cyber_physical_correlation():
    engine = ThreatCorrelationEngine(correlation_window_sec=300)

    # 1. Network event
    ev_net = NormalizedEvent(
        event_type="NETWORK_PORT_SCAN",
        severity="HIGH",
        asset_id="IP-192.168.10.84",
        location="Intersection 12",
        source="NETWORK_IDS",
        title="Port Scan",
        description="Port scan on controller"
    )
    engine.ingest_event(ev_net)

    # 2. Signal event
    ev_sig = NormalizedEvent(
        event_type="SIGNAL_ANOMALY",
        severity="CRITICAL",
        asset_id="CTRL-INT12",
        location="Intersection 12",
        source="NTCIP_IDS",
        title="Signal Override",
        description="Phase timing forced to RED"
    )
    engine.ingest_event(ev_sig)

    # 3. Traffic congestion event
    ev_traf = NormalizedEvent(
        event_type="TRAFFIC_CONGESTION",
        severity="CRITICAL",
        asset_id="ROAD-NH44-02",
        location="Intersection 12",
        source="TRAFFIC_ENGINE",
        title="Severe Queue",
        description="Queue length 400m"
    )
    corr = engine.ingest_event(ev_traf)

    assert corr is not None
    assert corr.incident_type == "CYBER_PHYSICAL"
    assert corr.severity == "CRITICAL"
    assert corr.verdict == "CONFIRMED"
    assert corr.composite_risk_score >= 85.0
    assert len(corr.factors) >= 3

def test_risk_engine_score_calculation():
    report = risk_engine.calculate_system_risk(
        active_critical_incidents=1,
        active_high_incidents=2,
        active_cyber_threats=2,
        max_congestion_score=88.0,
        offline_cameras=1,
        compromised_controllers=1
    )
    assert report.overall_score >= 80.0
    assert report.severity == "CRITICAL"
    assert len(report.contributing_factors) >= 4
    # Check explainability factor names
    factor_names = [f.name for f in report.contributing_factors]
    assert "Compromised Signal Controllers" in factor_names
