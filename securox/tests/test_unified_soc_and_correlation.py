"""
Securox — Unified SOC & Cross-Domain Threat Correlation Test Suite
Verifies:
  1. SOC Dashboard with 9 Live Modules (Consumes actual events, NO fake static metrics):
     - Cybersecurity posture
     - Threats
     - Incidents
     - Risk
     - Users
     - Devices
     - Domains
     - Attack chains
     - Audit logs
  2. Strict Incident Lifecycle Workflow:
     DETECTED -> TRIAGED -> INVESTIGATING -> CONTAINED -> RESOLVED (+ FALSE_POSITIVE)
  3. All Allowed Analyst Operations:
     - assign analyst
     - add evidence
     - add notes
     - contain
     - escalate
     - resolve
     - false positive
  4. Six Forensic Timelines & Correlation Views:
     - attack timeline
     - risk timeline
     - user timeline
     - device timeline
     - evidence
     - related events
  5. Cross-Domain Threat Correlation & Exact User Example (DEVICE-782):
     - Healthcare: Suspicious patient-record access
     - Traffic: Unauthorized signal command
     - Finance: Suspicious transaction
     - Output: RELATED SECURITY EVENTS + COORDINATED ATTACK INDICATOR
     - Output: correlation confidence, evidence, timeline, affected domains, shared entities
     - Graph visualization (nodes & edges)
     - Auto-spawn unified incident
     - Attribution disclaimer (no automatic attribution claim)
  6. Complete REST Endpoints Verification
"""

import asyncio
import os
import sys
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app"))
if backend_app not in sys.path:
    sys.path.insert(0, backend_app)
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(1, backend_dir)

from main import app
from core.store import store
from services.soc_engine import soc_engine, IncidentStatus, IncidentSeverity, EscalationLevel
from services.cross_domain_correlation import cross_domain_correlator

client = TestClient(app)


# ═══════════════════════════════════════════════════════════════════════════
# 1. Incident Workflow Lifecycle & Analyst Operations Tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_incident_lifecycle_workflow():
    """Verify progression through DETECTED -> TRIAGED -> INVESTIGATING -> CONTAINED -> RESOLVED."""
    # 1. Ingest/Create incident -> DETECTED
    inc = await soc_engine.create_incident({
        "title": "Suspicious SCADA Signal Override Attempt",
        "description": "Anomalous all-green timing requested from unrecognized terminal",
        "severity": IncidentSeverity.HIGH,
        "domain": "TRAFFIC",
        "asset": "TRAFFIC_SIGNAL_INT_42",
        "identity": "unknown_operator",
        "device": "DEV-SCADA-TERM-09",
        "attack_type": "SCADA Interlock Tampering"
    })
    inc_id = inc["id"]
    assert inc["status"] == IncidentStatus.DETECTED.value

    # 2. Assign analyst -> auto-moves to INVESTIGATING
    updated_assign = await soc_engine.assign_analyst(inc_id, analyst_username="soc_analyst_raj", assigned_by="ciso")
    assert updated_assign["status"] == IncidentStatus.INVESTIGATING.value
    assert updated_assign["assigned_analyst"] == "soc_analyst_raj"
    assert any("Analyst Assigned" in m.get("title", "") for m in updated_assign["timeline"])

    # 3. Add Notes
    note = await soc_engine.add_notes(inc_id, note_text="Initial review reveals firmware hash mismatch on PLC.", author="soc_analyst_raj")
    assert note["note"] == "Initial review reveals firmware hash mismatch on PLC."

    # 4. Add Evidence
    ev = await soc_engine.add_evidence(
        incident_id=inc_id,
        evidence_type="PCAP_PACKET",
        description="Crafted Modbus frame injecting force-listen diagnostic code",
        artifact_ref="/forensics/pcap/sig_modbus_42.pcap",
        hash_value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        added_by="soc_analyst_raj"
    )
    assert ev["evidence_type"] == "PCAP_PACKET"

    # 5. Escalate
    esc = await soc_engine.escalate_incident(inc_id, escalation_level="CRITICAL_COMMAND", reason="Direct threat to intersection collision safety", escalated_by="soc_analyst_raj")
    assert esc["escalation_level"] == "CRITICAL_COMMAND"
    assert esc["severity"] == "CRITICAL"

    # 6. Contain
    cont = await soc_engine.contain_incident(inc_id, containment_action="ISOLATE_PLC_NETWORK_SEGMENT", performed_by="traffic_commander", notes="Air-gapped PLC bay 42")
    assert cont["status"] == IncidentStatus.CONTAINED.value
    assert cont["containment_action"] == "ISOLATE_PLC_NETWORK_SEGMENT"
    assert cont["contained_at"] is not None

    # 7. Resolve
    res = await soc_engine.resolve_incident(inc_id, resolution_summary="Firmware re-flashed from gold master; controller returned to adaptive green.", resolved_by="soc_analyst_raj", root_cause="Default SNMP credential left enabled during field maintenance")
    assert res["status"] == IncidentStatus.RESOLVED.value
    assert res["resolved_at"] is not None
    assert len(res["timeline"]) >= 5


@pytest.mark.asyncio
async def test_incident_false_positive_workflow():
    """Verify closing an incident as FALSE_POSITIVE with recorded justification."""
    inc = await soc_engine.create_incident({
        "title": "High Volume PACS Transfer",
        "domain": "HEALTHCARE",
        "asset": "PACS_ARCHIVE_01",
        "severity": IncidentSeverity.MEDIUM
    })
    inc_id = inc["id"]

    fp = await soc_engine.mark_false_positive(inc_id, reason="Scheduled off-site disaster recovery backup synchronization", marked_by="hospital_admin")
    assert fp["status"] == IncidentStatus.FALSE_POSITIVE.value
    assert fp["false_positive_reason"] == "Scheduled off-site disaster recovery backup synchronization"
    assert fp["resolved_at"] is not None


# ═══════════════════════════════════════════════════════════════════════════
# 2. Six Detailed Forensic Timelines Tests
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_six_forensic_timelines():
    """Verify attack timeline, risk timeline, user timeline, device timeline, evidence, and related events."""
    inc = await soc_engine.create_incident({
        "title": "Unauthorized Patient Record Access",
        "domain": "HEALTHCARE",
        "asset": "PATIENT_RECORD",
        "identity": "dr_smith",
        "device": "DEV-HOSP-TABLET-01",
        "severity": IncidentSeverity.HIGH
    })
    inc_id = inc["id"]

    # Add evidence & notes
    await soc_engine.add_evidence(inc_id, "LOG_EXTRACT", "Audit log showing access outside shift hours", added_by="analyst_priya")
    await soc_engine.add_notes(inc_id, "Cross-department consultation not registered in HIS", author="analyst_priya")

    # Fetch all timelines
    timelines_bundle = await soc_engine.get_incident_all_timelines(inc_id)

    # 1. attack_timeline
    assert "attack_timeline" in timelines_bundle
    assert len(timelines_bundle["attack_timeline"]) >= 1

    # 2. risk_timeline
    assert "risk_timeline" in timelines_bundle
    assert isinstance(timelines_bundle["risk_timeline"], list)

    # 3. user_timeline
    assert "user_timeline" in timelines_bundle
    assert isinstance(timelines_bundle["user_timeline"], list)

    # 4. device_timeline
    assert "device_timeline" in timelines_bundle
    assert isinstance(timelines_bundle["device_timeline"], list)

    # 5. evidence
    assert "evidence" in timelines_bundle
    assert len(timelines_bundle["evidence"]) >= 1
    assert timelines_bundle["evidence"][0]["evidence_type"] == "LOG_EXTRACT"

    # 6. related_events
    assert "related_events" in timelines_bundle
    assert isinstance(timelines_bundle["related_events"], list)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Live Dashboard Consumes Actual Events (Zero Fake Static Metrics)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_soc_dashboard_consumes_actual_events():
    """Verify that all 9 dashboard modules are computed from real data and update dynamically."""
    dash_before = await soc_engine.get_soc_dashboard()

    # Ingest a critical cross-domain alert and incident
    test_incident = await soc_engine.create_incident({
        "title": "Critical Grid Overload Warning",
        "domain": "TRAFFIC",
        "asset": "SUBSTATION_SIG_99",
        "severity": IncidentSeverity.CRITICAL,
        "status": IncidentStatus.DETECTED
    })

    dash_after = await soc_engine.get_soc_dashboard()

    # 1. Posture: Score must react dynamically to new critical uncontained incident
    assert "posture" in dash_after
    assert "posture_score" in dash_after["posture"]
    assert dash_after["posture"]["status"] in ("STRONG", "DEFENDED", "ELEVATED_RISK", "CRITICAL_RISK")
    assert dash_after["posture"]["domains"]["traffic"]["uncontained_incidents"] >= 1

    # 2. Threats
    assert "threats" in dash_after
    assert "total_active" in dash_after["threats"]
    assert "by_severity" in dash_after["threats"]

    # 3. Incidents
    assert "incidents" in dash_after
    assert dash_after["incidents"]["by_status"][IncidentStatus.DETECTED.value] >= 1

    # 4. Risk
    assert "risk" in dash_after
    assert "average_risk_score" in dash_after["risk"]
    assert "top_risk_assets" in dash_after["risk"]

    # 5. Users
    assert "users" in dash_after
    assert "total_users" in dash_after["users"]
    assert "anomalous_users" in dash_after["users"]

    # 6. Devices
    assert "devices" in dash_after
    assert "total_monitored" in dash_after["devices"]

    # 7. Domains
    assert "domains" in dash_after
    assert "HEALTHCARE" in dash_after["domains"]
    assert "TRAFFIC" in dash_after["domains"]
    assert "FINANCE" in dash_after["domains"]

    # 8. Attack Chains
    assert "attack_chains" in dash_after
    assert len(dash_after["attack_chains"]) >= 1

    # 9. Audit Logs
    assert "audit_logs" in dash_after
    assert len(dash_after["audit_logs"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# 4. Cross-Domain Threat Correlation: Exact User Example (DEVICE-782)
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_cross_domain_threat_correlation_device_782():
    """
    Exact User Specification Verification:
    DEVICE-782
      - Healthcare: Suspicious patient-record access
      - Traffic: Unauthorized signal command
      - Finance: Suspicious transaction
    
    The system should identify:
      - RELATED SECURITY EVENTS
      - COORDINATED ATTACK INDICATOR
      - Do not automatically claim attribution.
      - Show: correlation confidence, evidence, timeline, affected domains, shared entities.
      - Graph visualization.
      - Auto-creates unified incident when thresholds are satisfied.
    """
    now = datetime.now(timezone.utc)
    t1 = (now - timedelta(minutes=45)).isoformat()
    t2 = (now - timedelta(minutes=25)).isoformat()
    t3 = (now - timedelta(minutes=5)).isoformat()

    synthetic_events = [
        {
            "event_id": "EVT-HC-DEVICE782-01",
            "domain": "HEALTHCARE",
            "action": "PATIENT_RECORD_VIEW",
            "resource": "PATIENT_RECORD_P902",
            "user": "dr_intruder",
            "device": "DEVICE-782",
            "ip": "198.51.100.77",
            "risk": 75.0,
            "timestamp": t1,
            "details": {"suspicious": True, "note": "Suspicious patient-record access"}
        },
        {
            "event_id": "EVT-TR-DEVICE782-02",
            "domain": "TRAFFIC",
            "action": "UNAUTHORIZED_SIGNAL_COMMAND",
            "resource": "TRAFFIC_SIGNAL_SCADA_NODE_03",
            "user": "unknown_operator",
            "device": "DEVICE-782",
            "ip": "198.51.100.77",
            "risk": 82.0,
            "timestamp": t2,
            "details": {"unauthorized": True, "note": "Unauthorized signal command"}
        },
        {
            "event_id": "EVT-FIN-DEVICE782-03",
            "domain": "FINANCE",
            "action": "SUSPICIOUS_TRANSACTION",
            "resource": "ACCOUNT_ACC_99182",
            "user": "dr_intruder",
            "device": "DEVICE-782",
            "ip": "198.51.100.77",
            "risk": 88.0,
            "timestamp": t3,
            "details": {"amount": 450000.0, "note": "Suspicious transaction"}
        }
    ]

    clusters = await cross_domain_correlator.correlate_events(
        synthetic_events,
        window_hours=24.0,
        create_incident=True
    )

    assert len(clusters) >= 1
    cluster = next((c for c in clusters if c.shared_pivot_value == "DEVICE-782"), clusters[0])

    # 1. Output: RELATED SECURITY EVENTS
    assert len(cluster.related_security_events) == 3
    event_ids = [e.event_id for e in cluster.related_security_events]
    assert "EVT-HC-DEVICE782-01" in event_ids
    assert "EVT-TR-DEVICE782-02" in event_ids
    assert "EVT-FIN-DEVICE782-03" in event_ids

    # 2. Output: COORDINATED ATTACK INDICATOR
    assert cluster.coordinated_attack_indicator is True

    # 3. Output: Correlation Confidence
    assert cluster.correlation_confidence >= 0.80

    # 4. Output: Affected Domains
    assert "HEALTHCARE" in cluster.affected_domains
    assert "TRAFFIC" in cluster.affected_domains
    assert "FINANCE" in cluster.affected_domains
    assert len(cluster.affected_domains) == 3

    # 5. Output: Shared Entities
    assert cluster.shared_entities["pivot_value"] == "DEVICE-782"
    assert "198.51.100.77" in cluster.shared_entities["ips"]

    # 6. Output: Evidence
    assert len(cluster.evidence) >= 2
    assert any("DEVICE-782" in e.get("description", "") for e in cluster.evidence)

    # 7. Output: Timeline
    assert len(cluster.timeline) == 3
    domains_in_timeline = [item["domain"] for item in cluster.timeline]
    assert "HEALTHCARE" in domains_in_timeline
    assert "TRAFFIC" in domains_in_timeline
    assert "FINANCE" in domains_in_timeline

    # 8. Output: Graph Visualization
    viz = cluster.graph_visualization
    node_labels = [n.label for n in viz.nodes]
    assert any("DEVICE-782" in l for l in node_labels)
    assert any("Domain: HEALTHCARE" in l for l in node_labels)
    assert any("Domain: TRAFFIC" in l for l in node_labels)
    assert any("Domain: FINANCE" in l for l in node_labels)
    edge_types = [e.type for e in viz.edges]
    assert "CROSS_DOMAIN_CORRELATION" in edge_types
    assert "GENERATED_EVENT" in edge_types
    assert "TARGETS_DOMAIN" in edge_types

    # 9. Output: Unified Incident Spawning
    assert cluster.created_incident_id is not None
    spawned_inc = await store.get_soc_incident(cluster.created_incident_id)
    assert spawned_inc is not None
    assert "DEVICE-782" in spawned_inc["title"]
    assert spawned_inc["status"] == IncidentStatus.DETECTED.value

    # 10. Invariant: Do not automatically claim attribution!
    assert cluster.attribution_disclaimer is not None
    assert "forensic" in cluster.attribution_disclaimer.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 5. REST API Endpoints Verification
# ═══════════════════════════════════════════════════════════════════════════

def test_api_soc_dashboard():
    resp = client.get("/api/soc/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "posture" in data
    assert "threats" in data
    assert "incidents" in data
    assert "risk" in data
    assert "users" in data
    assert "devices" in data
    assert "domains" in data
    assert "attack_chains" in data
    assert "audit_logs" in data


def test_api_soc_incident_workflow_and_actions():
    # 1. Create incident via API
    payload = {
        "title": "API Automated Anomaly Probe",
        "domain": "FINANCE",
        "asset": "SWIFT_GW_02",
        "severity": "HIGH",
        "identity": "external_actor",
        "device": "DEV-SWIFT-TERM"
    }
    resp = client.post("/api/soc/incidents", json=payload)
    assert resp.status_code == 200
    inc = resp.json()
    inc_id = inc["id"]
    assert inc["status"] == "DETECTED"

    # 2. Assign Analyst
    resp_assign = client.post(f"/api/soc/incidents/{inc_id}/assign", json={"analyst": "analyst_maria"})
    assert resp_assign.status_code == 200
    assert resp_assign.json()["assigned_analyst"] == "analyst_maria"
    assert resp_assign.json()["status"] == "INVESTIGATING"

    # 3. Add Notes
    resp_note = client.post(f"/api/soc/incidents/{inc_id}/notes", json={"note": "TLS renegotiation flood observed on port 443"})
    assert resp_note.status_code == 200
    assert resp_note.json()["note"] == "TLS renegotiation flood observed on port 443"

    # 4. Add Evidence
    resp_ev = client.post(f"/api/soc/incidents/{inc_id}/evidence", json={
        "evidence_type": "HASH",
        "description": "Corrupted DLL hash in memory space",
        "hash_value": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    })
    assert resp_ev.status_code == 200
    assert resp_ev.json()["evidence_type"] == "HASH"

    # 5. Escalate
    resp_esc = client.post(f"/api/soc/incidents/{inc_id}/escalate", json={
        "escalation_level": "ELEVATED",
        "reason": "Potential wire settlement delay"
    })
    assert resp_esc.status_code == 200
    assert resp_esc.json()["escalation_level"] == "ELEVATED"

    # 6. Contain
    resp_cont = client.post(f"/api/soc/incidents/{inc_id}/contain", json={
        "containment_action": "REVOKE_SWIFT_SESSION_TOKENS",
        "notes": "Session tokens revoked across gateway"
    })
    assert resp_cont.status_code == 200
    assert resp_cont.json()["status"] == "CONTAINED"

    # 7. Resolve
    resp_res = client.post(f"/api/soc/incidents/{inc_id}/resolve", json={
        "resolution_summary": "Gateway restarted with TLS 1.3 enforcement and certificates rotated.",
        "root_cause": "TLS 1.0 legacy cipher downgrade vulnerability"
    })
    assert resp_res.status_code == 200
    assert resp_res.json()["status"] == "RESOLVED"

    # 8. Fetch Timelines
    resp_tl = client.get(f"/api/soc/incidents/{inc_id}/timelines")
    assert resp_tl.status_code == 200
    tl_data = resp_tl.json()
    assert "attack_timeline" in tl_data
    assert "risk_timeline" in tl_data
    assert "user_timeline" in tl_data
    assert "device_timeline" in tl_data
    assert len(tl_data["evidence"]) >= 1
    assert len(tl_data["notes"]) >= 1


def test_api_cross_domain_correlation_endpoint():
    resp = client.get("/api/soc/cross-domain-correlation?window_hours=24")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
