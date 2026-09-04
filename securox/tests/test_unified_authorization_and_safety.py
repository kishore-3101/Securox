"""
Securox — Unified Authorization Pipeline & Critical Infrastructure Safety Guard Test Suite
Verifies:
  1. Fusion of RBAC + ABAC + AI + Risk into one authorization decision pipeline.
  2. The 5 canonical decision options:
     - ALLOW
     - ALLOW + MONITOR (or MONITOR)
     - STEP-UP AUTH
     - RESTRICT
     - BLOCK
  3. Exact User Examples:
     - Normal doctor: ALLOW
     - New device: STEP-UP AUTH
     - Abnormal patient access: MONITOR (ALLOW + MONITOR)
     - Mass export: RESTRICT (with ROW_CAP and REDACT_PII restrictions)
     - Critical exfiltration: BLOCK
  4. Every decision automatically creates a canonical audit event in the Central Event Fabric.
  5. Critical Infrastructure Safety Validation Guard:
     - Hospital: clinical impact, patient safety, active surgeries, ICU state, emergency state
     - Traffic: collision risk, active green corridor, emergency vehicles in transit
     - Finance: systemic freeze, open settlement clearinghouse window
     - Strict autonomous rejection: UNSAFE_FOR_AUTONOMOUS_EXECUTION
  6. Human-in-the-Loop Mitigation Approval Workflow (cmo, traffic_commander, financial_controller)
  7. REST API Endpoints:
     - POST /api/auth/authorize
     - GET /api/auth/decisions
     - POST /api/mitigations/evaluate-safety
     - POST /api/mitigations/propose
     - GET /api/mitigations/proposals
     - POST /api/mitigations/proposals/{id}/approve
     - POST /api/mitigations/proposals/{id}/reject
"""

import asyncio
import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

backend_app = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "app"))
if backend_app not in sys.path:
    sys.path.insert(0, backend_app)
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(1, backend_dir)

from main import app
from auth.jwt_auth import create_access_token
from services.unified_authorization import (
    unified_auth_pipeline, AuthDecision, AuthorizationDecisionResult
)
from services.safety_guard import (
    safety_guard, SafetyVerdict, ProposalStatus
)
from core.store import store

client = TestClient(app)


@pytest.fixture
def admin_token():
    return create_access_token({"sub": "admin", "username": "admin", "role": "admin"})


@pytest.fixture
def cmo_token():
    return create_access_token({"sub": "hospital_admin", "username": "hospital_admin", "role": "cmo"})


@pytest.fixture
def traffic_commander_token():
    return create_access_token({"sub": "traffic_supervisor", "username": "traffic_supervisor", "role": "traffic_commander"})


@pytest.fixture
def citizen_token():
    return create_access_token({"sub": "citizen", "username": "citizen", "role": "citizen"})


# ═══════════════════════════════════════════════════════════════════════════
# 1. Five Canonical Authorization Decisions & Exact User Examples
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_example_normal_doctor_allow():
    """User Example 1: Normal doctor -> ALLOW."""
    res = await unified_auth_pipeline.authorize(
        identity="dr_smith",
        role="doctor",
        domain="HEALTHCARE",
        resource="PATIENT_RECORD",
        action="VIEW",
        attributes={
            "device_id": "DEV-HOSP-TABLET-01",
            "is_known_device": True,
            "patient_assignment": "assigned",
            "department": "Cardiology",
            "patient_department": "Cardiology",
            "hour": 14,
            "record_count": 1
        }
    )
    assert res.decision == AuthDecision.ALLOW
    assert res.risk_category == "LOW"
    assert res.risk_score < 30.0
    assert res.rbac_granted is True
    assert len(res.restrictions) == 0


@pytest.mark.asyncio
async def test_example_new_device_step_up_auth():
    """User Example 2: New device -> STEP-UP AUTH."""
    res = await unified_auth_pipeline.authorize(
        identity="dr_smith",
        role="doctor",
        domain="HEALTHCARE",
        resource="PATIENT_RECORD",
        action="VIEW",
        attributes={
            "device_id": "DEV-UNKNOWN-NEW-PHONE",
            "is_known_device": False,
            "patient_assignment": "assigned",
            "department": "Cardiology",
            "patient_department": "Cardiology",
            "hour": 14,
            "record_count": 1
        }
    )
    assert res.decision == AuthDecision.STEP_UP_AUTH
    assert any("new device" in f.get("name", "").lower() for f in res.factors)


@pytest.mark.asyncio
async def test_example_abnormal_patient_access_monitor():
    """User Example 3: Abnormal patient access -> MONITOR (ALLOW + MONITOR)."""
    res = await unified_auth_pipeline.authorize(
        identity="dr_jones",
        role="doctor",
        domain="HEALTHCARE",
        resource="PATIENT_RECORD",
        action="VIEW",
        attributes={
            "device_id": "DEV-HOSP-TABLET-02",
            "is_known_device": True,
            "patient_assignment": "unassigned",  # Cross-department consultation
            "department": "Cardiology",
            "patient_department": "Neurology",
            "hour": 11,
            "record_count": 1
        }
    )
    # Both ALLOW + MONITOR and MONITOR are accepted canonical forms
    assert res.decision in (AuthDecision.ALLOW_MONITOR, "ALLOW + MONITOR", "MONITOR")
    assert res.rbac_granted is True


@pytest.mark.asyncio
async def test_example_mass_export_restrict():
    """User Example 4: Mass export -> RESTRICT (enforcing ROW_CAP and REDACT_PII)."""
    res = await unified_auth_pipeline.authorize(
        identity="auditor_claire",
        role="auditor",
        domain="HEALTHCARE",
        resource="PATIENT_RECORD",
        action="EXPORT",
        attributes={
            "device_id": "DEV-AUDITOR-01",
            "is_known_device": True,
            "record_count": 250,
            "is_export": True,
            "hour": 15
        }
    )
    assert res.decision == AuthDecision.RESTRICT
    assert len(res.restrictions) >= 2
    types = [r.restriction_type for r in res.restrictions]
    assert "ROW_CAP" in types
    assert "REDACT_PII" in types
    row_cap = next(r for r in res.restrictions if r.restriction_type == "ROW_CAP")
    assert row_cap.parameters.get("max_rows") == 25


@pytest.mark.asyncio
async def test_example_critical_exfiltration_block():
    """User Example 5: Critical exfiltration -> BLOCK."""
    res = await unified_auth_pipeline.authorize(
        identity="unknown_actor",
        role="doctor",
        domain="HEALTHCARE",
        resource="PATIENT_RECORD",
        action="EXPORT",
        attributes={
            "device_id": "DEV-UNKNOWN-EXFIL",
            "is_known_device": False,
            "network_trust": "TOR_EXIT",
            "client_ip": "198.51.100.10",
            "record_count": 1000,
            "critical_exfiltration": True
        }
    )
    assert res.decision == AuthDecision.BLOCK
    assert res.risk_category in ("HIGH", "CRITICAL")
    assert res.risk_score >= 70.0


@pytest.mark.asyncio
async def test_rbac_violation_triggers_block():
    """Verify that a role without permission on resource:action is blocked by RBAC."""
    res = await unified_auth_pipeline.authorize(
        identity="reception_clerk",
        role="receptionist",
        domain="HEALTHCARE",
        resource="SECURITY_POLICY",
        action="DELETE",
        attributes={"is_known_device": True}
    )
    assert res.decision == AuthDecision.BLOCK
    assert res.rbac_granted is False
    assert any("rbac" in f.get("name", "").lower() for f in res.factors)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Every Decision Creates an Ingested Audit Event
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_every_decision_creates_audit_event():
    res = await unified_auth_pipeline.authorize(
        identity="operator_dan",
        role="traffic_operator",
        domain="TRAFFIC",
        resource="TRAFFIC_SIGNAL",
        action="VIEW",
        attributes={"is_known_device": True}
    )
    assert res.event_id is not None
    assert res.event_id.startswith("EVT-AUTH-")

    # Verify persisted in database
    decisions = await store.get_auth_decisions(identity="operator_dan", limit=5)
    assert len(decisions) >= 1
    stored = decisions[0]
    assert stored["decision"] == res.decision.value
    assert stored["domain"] == "TRAFFIC"
    assert stored["resource"] == "TRAFFIC_SIGNAL"


# ═══════════════════════════════════════════════════════════════════════════
# 3. Critical Infrastructure Safety Guard
# ═══════════════════════════════════════════════════════════════════════════

def test_hospital_safety_guard_rejects_during_active_surgeries():
    """
    Hospital Invariant: Never automatically shut down hospital infrastructure
    if surgeries are in progress or patients are at risk.
    """
    eval_res = safety_guard.evaluate_mitigation_safety(
        domain="HEALTHCARE",
        action_name="SHUTDOWN_INFRASTRUCTURE",
        target_asset="HOSPITAL_MAIN_POWER_BUS",
        safety_context={
            "surgeries_in_progress": 3,
            "icu_occupancy_pct": 89.0,
            "active_ventilators": 12,
            "emergency_state": "NORMAL"
        }
    )
    assert eval_res.is_safe is False
    assert eval_res.verdict == SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION
    assert "REJECT AUTOMATED MITIGATION" in eval_res.rationale
    assert any("surgical" in r.lower() for r in eval_res.rejection_reasons)
    assert eval_res.required_approver_role == "cmo"


def test_hospital_safety_guard_rejects_during_code_blue():
    """Verify safety guard blocks PAC/EHR isolation during CODE_BLUE."""
    eval_res = safety_guard.evaluate_mitigation_safety(
        domain="HEALTHCARE",
        action_name="ISOLATE_PAC_SERVER",
        target_asset="PAC_ARCHIVE_01",
        safety_context={
            "emergency_state": "CODE_BLUE",
            "surgeries_in_progress": 0,
            "icu_occupancy_pct": 40.0
        }
    )
    assert eval_res.is_safe is False
    assert eval_res.verdict == SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION
    assert any("CODE_BLUE" in r for r in eval_res.rejection_reasons)


def test_traffic_safety_guard_rejects_during_green_corridor():
    """
    Traffic Invariant: Never halt signals or force all-red when green corridor
    or emergency vehicles are active.
    """
    eval_res = safety_guard.evaluate_mitigation_safety(
        domain="TRAFFIC",
        action_name="FORCE_ALL_RED_CORRIDOR",
        target_asset="INTERSECTION_JUNCTION_04",
        safety_context={
            "green_corridor_active": True,
            "active_emergency_vehicles": 2,
            "rush_hour": True
        }
    )
    assert eval_res.is_safe is False
    assert eval_res.verdict == SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION
    assert "REJECT AUTOMATED MITIGATION" in eval_res.rationale
    assert any("green corridor" in r.lower() for r in eval_res.rejection_reasons)
    assert eval_res.required_approver_role == "traffic_commander"


def test_finance_safety_guard_rejects_during_open_clearing_window():
    """
    Finance Invariant: Never autonomously freeze clearinghouse during open RTGS window.
    """
    eval_res = safety_guard.evaluate_mitigation_safety(
        domain="FINANCE",
        action_name="FREEZE_CLEARING_HOUSE",
        target_asset="RTGS_PAYMENT_SWITCH",
        safety_context={
            "settlement_window_open": True,
            "active_clearing_inr": 450_000_000.0,
            "is_market_hours": True
        }
    )
    assert eval_res.is_safe is False
    assert eval_res.verdict == SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION
    assert any("settlement window" in r.lower() for r in eval_res.rejection_reasons)
    assert eval_res.required_approver_role == "financial_risk_officer"


def test_safe_non_invasive_mitigation_auto_executes():
    """Verify non-invasive actions (e.g. session revocation, step-up MFA) are approved to auto-execute."""
    eval_res = safety_guard.evaluate_mitigation_safety(
        domain="HEALTHCARE",
        action_name="REQUIRE_STEP_UP_MFA",
        target_asset="USER_SESSION",
        safety_context={}
    )
    assert eval_res.is_safe is True
    assert eval_res.verdict == SafetyVerdict.SAFE_TO_AUTO_EXECUTE


# ═══════════════════════════════════════════════════════════════════════════
# 4. Mitigation Approval Workflow Lifecycle
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_mitigation_approval_workflow_lifecycle():
    """
    Lifecycle:
    1. Dangerous mitigation proposed -> REJECT AUTOMATED MITIGATION -> status PENDING_APPROVAL
    2. Unauthorized role attempts approval -> rejected with PermissionError
    3. Designated authority approves -> status APPROVED
    """
    # 1. Propose dangerous hospital isolation
    proposal = await safety_guard.propose_mitigation(
        domain="HEALTHCARE",
        action_name="POWER_OFF_ICU_SWITCH",
        target_asset="ICU_SWITCH_BAY_3",
        proposed_by="AI_ANOMALY_DETECTOR",
        safety_context={
            "surgeries_in_progress": 2,
            "icu_occupancy_pct": 85.0
        },
        comments="AI suggested power cut due to telemetry spike"
    )
    assert proposal["status"] == ProposalStatus.PENDING_APPROVAL.value
    assert proposal["safety_verdict"] == SafetyVerdict.UNSAFE_FOR_AUTONOMOUS_EXECUTION.value
    prop_id = proposal["id"]

    # 2. Unauthorized role (e.g. receptionist or citizen) attempts approval
    with pytest.raises(PermissionError):
        await safety_guard.approve_mitigation(
            proposal_id=prop_id,
            user="citizen_john",
            role="citizen"
        )

    # 3. Designated authority (CMO or Admin) approves
    approved = await safety_guard.approve_mitigation(
        proposal_id=prop_id,
        user="dr_director",
        role="cmo",
        comments="Approved by Chief Medical Officer with manual clinical backup plan"
    )
    assert approved["status"] == ProposalStatus.APPROVED.value
    assert approved["approved_by"] == "dr_director"

    # 4. Verify in database
    db_record = await store.get_mitigation_proposal(prop_id)
    assert db_record["status"] == ProposalStatus.APPROVED.value


@pytest.mark.asyncio
async def test_mitigation_rejection_workflow():
    """Verify human reviewer can explicitly reject dangerous proposal."""
    proposal = await safety_guard.propose_mitigation(
        domain="TRAFFIC",
        action_name="HALT_INTERSECTION_GRID",
        target_asset="CENTRAL_GRID",
        proposed_by="AI_SYSTEM",
        safety_context={"green_corridor_active": True}
    )
    prop_id = proposal["id"]

    rejected = await safety_guard.reject_mitigation(
        proposal_id=prop_id,
        user="traffic_chief",
        role="traffic_commander",
        reason="Rejected: Emergency corridor must not be disrupted"
    )
    assert rejected["status"] == ProposalStatus.REJECTED.value
    assert "Emergency corridor" in rejected["comments"]


# ═══════════════════════════════════════════════════════════════════════════
# 5. REST API Endpoints Verification
# ═══════════════════════════════════════════════════════════════════════════

def test_api_authorize_endpoint():
    payload = {
        "identity": "dr_smith",
        "role": "doctor",
        "domain": "HEALTHCARE",
        "resource": "PATIENT_RECORD",
        "action": "VIEW",
        "attributes": {
            "is_known_device": True,
            "patient_assignment": "assigned",
            "hour": 14,
            "department": "Cardiology",
            "patient_department": "Cardiology"
        }
    }
    resp = client.post("/api/auth/authorize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "ALLOW"
    assert "event_id" in data
    assert "risk_score" in data


def test_api_evaluate_safety_endpoint():
    payload = {
        "domain": "HEALTHCARE",
        "action_name": "SHUTDOWN_INFRASTRUCTURE",
        "target_asset": "HOSPITAL_CORE_POWER",
        "safety_context": {
            "surgeries_in_progress": 1
        }
    }
    resp = client.post("/api/mitigations/evaluate-safety", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_safe"] is False
    assert data["verdict"] == "UNSAFE_FOR_AUTONOMOUS_EXECUTION"


def test_api_propose_and_approve_mitigation(admin_token, citizen_token):
    # Propose
    payload = {
        "domain": "HEALTHCARE",
        "action_name": "ISOLATE_PAC_SERVER",
        "target_asset": "PAC_02",
        "proposed_by": "AI_INTRUSION_DETECTOR",
        "safety_context": {"surgeries_in_progress": 2}
    }
    resp = client.post("/api/mitigations/propose", json=payload)
    assert resp.status_code == 200
    prop_data = resp.json()
    prop_id = prop_data["id"]
    assert prop_data["status"] == "PENDING_APPROVAL"

    # Unauthorized approval attempt by citizen -> 403 Forbidden
    resp_citizen = client.post(
        f"/api/mitigations/proposals/{prop_id}/approve",
        json={"comments": "citizen attempting approval"},
        headers={"Authorization": f"Bearer {citizen_token}"}
    )
    assert resp_citizen.status_code == 403

    # Authorized approval by Admin -> 200 OK
    resp_admin = client.post(
        f"/api/mitigations/proposals/{prop_id}/approve",
        json={"comments": "Emergency override approved by administrator"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert resp_admin.status_code == 200
    assert resp_admin.json()["status"] == "APPROVED"


def test_api_get_decisions_audit():
    resp = client.get("/api/auth/decisions?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
