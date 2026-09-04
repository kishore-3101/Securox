import os
import sys
import pytest
import asyncio
from datetime import datetime, timezone, timedelta

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from auth.access_control import access_engine, Action, ResourceType, AccessContext, Decision
from database.store import store


@pytest.mark.asyncio
async def test_rbac_matrix_permissions():
    """Verify static RBAC rules across Healthcare, Traffic, and Finance roles."""
    # 1. Doctor permissions
    assert access_engine.check_rbac("doctor", ResourceType.PATIENT_RECORD, Action.VIEW) is True
    assert access_engine.check_rbac("doctor", ResourceType.CLINICAL_NOTE, Action.CREATE) is True
    assert access_engine.check_rbac("doctor", ResourceType.TRAFFIC_SIGNAL, Action.UPDATE) is False
    assert access_engine.check_rbac("doctor", ResourceType.TRANSACTION, Action.CREATE) is False

    # 2. Ambulance Driver permissions
    assert access_engine.check_rbac("ambulance_driver", ResourceType.AMBULANCE_DISPATCH, Action.UPDATE) is True
    assert access_engine.check_rbac("ambulance_driver", ResourceType.PATIENT_RECORD, Action.VIEW) is False

    # 3. Auditor permissions (strictly read-only)
    assert access_engine.check_rbac("auditor", ResourceType.AUDIT_LOG, Action.VIEW) is True
    assert access_engine.check_rbac("auditor", ResourceType.TRANSACTION, Action.VIEW) is True
    assert access_engine.check_rbac("auditor", ResourceType.TRANSACTION, Action.CREATE) is False
    assert access_engine.check_rbac("auditor", ResourceType.PATIENT_RECORD, Action.UPDATE) is False

    # 4. Traffic Operator permissions
    assert access_engine.check_rbac("traffic_operator", ResourceType.TRAFFIC_SIGNAL, Action.UPDATE) is True
    assert access_engine.check_rbac("traffic_operator", ResourceType.BANK_ACCOUNT, Action.VIEW) is False


@pytest.mark.asyncio
async def test_abac_context_and_risk_evaluation():
    """Verify contextual factors (time, device, impossible travel, volume)."""
    # Nominal daytime doctor access
    ctx_nominal = AccessContext(
        user_id="doctor",
        username="doctor",
        role="doctor",
        domain="HEALTHCARE",
        department="Cardiology",
        device_id="DEV-HOSP-01",
        device_trust=100.0,
        is_known_device=True,
        client_ip="10.0.4.12",
        geo_location="Bengaluru, IN",
        timestamp=datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc),
        record_count=1,
        patient_assignment="assigned"
    )
    res_nominal = access_engine.evaluate_access(ctx_nominal, ResourceType.PATIENT_RECORD, Action.VIEW)
    assert res_nominal.decision == Decision.ALLOW
    assert res_nominal.risk_score <= 25.0
    assert res_nominal.incident_created is False

    # High-risk off-hours exfiltration attack (London at 02:45 AM, unknown device, 2,000 records)
    ctx_attack = AccessContext(
        user_id="doctor",
        username="doctor",
        role="doctor",
        domain="HEALTHCARE",
        department="Cardiology",
        device_id="DEV-ROGUE-EXT-88",
        device_trust=20.0,
        is_known_device=False,
        client_ip="185.220.101.5",
        geo_location="London, UK",
        previous_geo="Bengaluru, IN",
        previous_login_time=datetime(2026, 9, 4, 2, 40, tzinfo=timezone.utc),
        timestamp=datetime(2026, 9, 4, 2, 45, tzinfo=timezone.utc),
        record_count=2000,
        patient_assignment="unassigned",
        network_trust="PUBLIC_VPN"
    )
    res_attack = access_engine.evaluate_access(ctx_attack, ResourceType.PATIENT_RECORD, Action.VIEW)
    assert res_attack.decision == Decision.BLOCK
    assert res_attack.risk_score >= 75.0
    assert res_attack.risk_category == "CRITICAL"
    assert res_attack.incident_created is True
    assert len(res_attack.factors) >= 4

    # Verify specific XAI factors are present
    factor_names = [f["factor"] for f in res_attack.factors]
    assert any("Impossible Travel" in name for name in factor_names)
    assert any("Unregistered" in name for name in factor_names)
    assert any("Mass Data Volume" in name for name in factor_names)
    assert any("Off-Hours" in name for name in factor_names)


@pytest.mark.asyncio
async def test_database_store_multi_domain_queries():
    """Verify store helper methods query domain tables properly."""
    # 1. Patients query
    patients = await store.get_patients()
    assert len(patients) >= 5
    p1 = await store.get_patient("P-1001")
    assert p1 is not None
    assert p1["name"] == "Aarav Sharma"
    assert p1["department"] == "Cardiology"

    # 2. Medical records query
    records = await store.get_medical_records("P-1001")
    assert len(records) >= 1
    assert "Coronary" in records[0]["diagnosis"]

    # 3. Ambulances query & state transition
    ambulances = await store.get_ambulances()
    assert len(ambulances) >= 3
    updated = await store.update_ambulance_status("AMB-01", "AT_HOSPITAL", location="ER Bay 01", eta=0)
    assert updated is True

    # 4. Traffic signals query
    signals = await store.get_traffic_signals()
    assert len(signals) >= 6
    assert any(s["mode"] in ("GREEN_CORRIDOR", "ADAPTIVE") for s in signals)

    # 5. Bank accounts & transactions
    accounts = await store.get_bank_accounts()
    assert len(accounts) >= 4
    txs = await store.get_bank_transactions()
    assert len(txs) >= 4

    # 6. Policies & Cross-domain threats
    policies = await store.get_security_policies()
    assert len(policies) >= 4
    threats = await store.get_cross_domain_threats()
    assert len(threats) >= 1
    assert "HEALTHCARE" in threats[0]["domains_involved"]
