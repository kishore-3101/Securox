"""
Securox Operational Financial Security — Complete Lifecycle & RBAC Test Suite
Tests:
  1. Customer Account Isolation (Customers only see their own accounts)
  2. Branch Staff Scoping (Tellers/Branch Managers limited to branch scope)
  3. Auditor Read-Only Enforcement (403 on mutate + ACCESS_DENIED audit)
  4. End-to-End Lifecycle:
     Transaction -> Risk Assessment -> Fraud Detection -> Alert -> Case -> Investigation -> Decision -> Resolution
  5. Multi-Model Inference (XGBoost + Isolation Forest composite scoring)
  6. High-Confidence Fraud / Offshore Diversion Auto-Case Creation
  7. Account Quarantine / Freeze on Case Resolution
  8. AMLSim Graph Contagion & Mule Detection
  9. Regulatory SAR Filing Workflow
  10. Cyber-VaR Engine with Transparent Attribution Disclosure (LIVE INFERENCE / SIMULATION)
"""

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

client = TestClient(app)


# ── Stakeholder Persona Fixtures ──────────────────────────────────────────────

@pytest.fixture
def customer_token():
    return create_access_token({
        "sub": "customer",
        "username": "customer",
        "role": "customer",
        "customer_id": "CUST-101"
    })


@pytest.fixture
def teller_token():
    return create_access_token({
        "sub": "teller",
        "username": "teller",
        "role": "teller",
        "branch_id": "BR-01"
    })


@pytest.fixture
def branch_mgr_token():
    return create_access_token({
        "sub": "branch_manager",
        "username": "branch_manager",
        "role": "branch_manager",
        "branch_id": "BR-01"
    })


@pytest.fixture
def fraud_analyst_token():
    return create_access_token({
        "sub": "fraud_analyst",
        "username": "fraud_analyst",
        "role": "fraud_analyst"
    })


@pytest.fixture
def aml_analyst_token():
    return create_access_token({
        "sub": "aml_analyst",
        "username": "aml_analyst",
        "role": "aml_analyst"
    })


@pytest.fixture
def compliance_token():
    return create_access_token({
        "sub": "compliance_officer",
        "username": "compliance_officer",
        "role": "compliance_officer"
    })


@pytest.fixture
def risk_analyst_token():
    return create_access_token({
        "sub": "risk_analyst",
        "username": "risk_analyst",
        "role": "risk_analyst"
    })


@pytest.fixture
def auditor_token():
    return create_access_token({
        "sub": "auditor",
        "username": "auditor",
        "role": "auditor"
    })


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_customer_isolation(customer_token):
    """Customer can only see their own accounts and cannot see other customers' accounts."""
    resp = client.get("/api/finance/accounts", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 200
    accounts = resp.json()
    for acc in accounts:
        assert acc["customer_id"] == "CUST-101"

    # Blocked from viewing other customer profile
    block_resp = client.get("/api/finance/customers/CUST-103", headers={"Authorization": f"Bearer {customer_token}"})
    assert block_resp.status_code == 403


def test_branch_staff_scoping(teller_token):
    """Teller is restricted to accounts in branch BR-01."""
    resp = client.get("/api/finance/accounts", headers={"Authorization": f"Bearer {teller_token}"})
    assert resp.status_code == 200
    accounts = resp.json()
    for acc in accounts:
        assert acc["branch_id"] == "BR-01"


def test_auditor_read_only_enforcement(auditor_token):
    """Auditor cannot initiate transactions or mutate fraud cases."""
    tx_payload = {
        "account_id": "ACC-7001",
        "counterparty_account": "ACC-7003",
        "amount": 5000.0,
        "channel": "UPI"
    }
    resp = client.post("/api/finance/transactions", json=tx_payload, headers={"Authorization": f"Bearer {auditor_token}"})
    assert resp.status_code == 403
    assert "read-only" in resp.json()["detail"].lower()

    # Auditor read-only on case decisions
    case_payload = {
        "decision": "CONFIRMED_FRAUD",
        "decision_rationale": "Audit check",
        "resolution_notes": "None",
        "freeze_account": False
    }
    c_resp = client.post("/api/finance/fraud-cases/CASE-FRD-9001/decision", json=case_payload, headers={"Authorization": f"Bearer {auditor_token}"})
    assert c_resp.status_code == 403


def test_end_to_end_transaction_lifecycle_low_risk(teller_token):
    """
    Standard retail transfer -> Settled immediately with transparent model attribution.
    """
    tx_payload = {
        "account_id": "ACC-7001",
        "counterparty_account": "ACC-7003",
        "amount": 15000.0,
        "channel": "UPI",
        "currency": "INR",
        "ip_address": "192.168.1.45"
    }
    resp = client.post("/api/finance/transactions", json=tx_payload, headers={"Authorization": f"Bearer {teller_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction"]["status"] == "SETTLED"
    assert data["assessment"]["decision"] == "SETTLED"
    assert data["assessment"]["model_attribution"] in ("LIVE INFERENCE", "SIMULATION")
    assert "risk_score" in data["assessment"]
    assert "xgboost_score" in data["assessment"]
    assert "isolation_forest_score" in data["assessment"]


def test_high_risk_fraud_detection_and_auto_case(teller_token, fraud_analyst_token):
    """
    Rapid Offshore SWIFT Transfer with Threat Actor IP:
      Transaction -> Risk Assessment -> Fraud Detection -> Alert -> Case Created
    """
    tx_payload = {
        "account_id": "ACC-7002",
        "counterparty_account": "OFFSHORE-ESCROW-8841",
        "amount": 4800000.0,
        "channel": "SWIFT",
        "currency": "USD",
        "ip_address": "198.51.100.77",
        "location": "Offshore / Proxy"
    }
    resp = client.post("/api/finance/transactions", json=tx_payload, headers={"Authorization": f"Bearer {teller_token}"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["transaction"]["status"] == "BLOCKED"
    assert data["assessment"]["decision"] == "BLOCKED"
    assert data["assessment"]["risk_score"] >= 80.0
    assert data["assessment"]["case"] is not None
    case_id = data["assessment"]["case"]["id"]

    # Fraud analyst inspects the newly generated case
    case_resp = client.get(f"/api/finance/fraud-cases/{case_id}", headers={"Authorization": f"Bearer {fraud_analyst_token}"})
    assert case_resp.status_code == 200
    case_detail = case_resp.json()
    assert case_detail["id"] == case_id
    assert case_detail["status"] == "OPEN"
    assert case_detail["total_exposure_inr"] == 4800000.0


def test_case_investigation_and_resolution_freeze_account(fraud_analyst_token, teller_token):
    """
    Fraud Analyst investigates and decides case:
      Investigation -> Decision (CONFIRMED_FRAUD) -> Resolution -> Freeze Account
    """
    decision_payload = {
        "decision": "CONFIRMED_FRAUD",
        "decision_rationale": "SWIFT outflow linked to confirmed APT C2 server 198.51.100.77.",
        "resolution_notes": "Account quarantined and funds held in escrow.",
        "freeze_account": True
    }
    resp = client.post(
        "/api/finance/fraud-cases/CASE-FRD-9001/decision",
        json=decision_payload,
        headers={"Authorization": f"Bearer {fraud_analyst_token}"}
    )
    assert resp.status_code == 200
    resolved = resp.json()
    assert resolved["status"] == "RESOLVED"
    assert resolved["decision"] == "CONFIRMED_FRAUD"

    # Verify affected account is now FROZEN
    acc_resp = client.get("/api/finance/accounts", headers={"Authorization": f"Bearer {teller_token}"})
    assert acc_resp.status_code == 200

    # Attempting transaction on frozen account must be BLOCKED
    debit_payload = {
        "account_id": "ACC-7006",
        "counterparty_account": "ACC-7001",
        "amount": 1000.0,
        "channel": "UPI"
    }
    block_tx = client.post("/api/finance/transactions", json=debit_payload, headers={"Authorization": f"Bearer {teller_token}"})
    assert block_tx.status_code == 201
    assert block_tx.json()["transaction"]["status"] == "BLOCKED"
    assert "FROZEN" in block_tx.json()["assessment"]["reason"]


def test_amlsim_graph_contagion_and_mule_detection(aml_analyst_token):
    """AML Analyst runs graph contagion analysis and computes Mule Probability."""
    resp = client.post(
        "/api/finance/aml/analyze",
        json={"account_id": "ACC-7006"},
        headers={"Authorization": f"Bearer {aml_analyst_token}"}
    )
    assert resp.status_code == 200
    res = resp.json()
    assert "mule_probability" in res
    assert res["mule_probability"] > 0.5
    assert res["model_attribution"] == "LIVE INFERENCE"
    assert "topology" in res
    assert res["finding"]["primary_account"] == "ACC-7006"


def test_compliance_file_sar_report(compliance_token):
    """Compliance Officer reviews regulatory evidence and files SAR."""
    findings = client.get("/api/finance/aml/findings", headers={"Authorization": f"Bearer {compliance_token}"}).json()
    assert len(findings) > 0
    target_id = findings[0]["id"]

    sar_ref = f"SAR-2026-REG-{uuid.uuid4().hex[:6].upper()}"
    resp = client.post(
        f"/api/finance/aml/findings/{target_id}/file-sar",
        json={"sar_reference": sar_ref},
        headers={"Authorization": f"Bearer {compliance_token}"}
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["sar_filed"] == 1
    assert updated["sar_reference"] == sar_ref


def test_cyber_var_engine_and_attribution_disclosure(risk_analyst_token):
    """
    Risk Analyst retrieves Cyber-VaR.
    Clearly marks LIVE INFERENCE for current state and SIMULATION for stress scenarios.
    """
    # 1. Live inference on current portfolio
    live_resp = client.get("/api/finance/cyber-var", headers={"Authorization": f"Bearer {risk_analyst_token}"})
    assert live_resp.status_code == 200
    live_var = live_resp.json()
    assert live_var["model_attribution"] == "LIVE INFERENCE"
    assert live_var["cyber_var_95_1day_inr"] > 0
    assert live_var["cyber_var_99_1day_inr"] > live_var["cyber_var_95_1day_inr"]

    # 2. Simulation with stress scenario multiplier
    sim_resp = client.get("/api/finance/cyber-var?simulation_multiplier=2.5", headers={"Authorization": f"Bearer {risk_analyst_token}"})
    assert sim_resp.status_code == 200
    sim_var = sim_resp.json()
    assert sim_var["model_attribution"] == "SIMULATION"
    assert sim_var["cyber_var_95_1day_inr"] > live_var["cyber_var_95_1day_inr"]
