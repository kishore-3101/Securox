"""
Securox — Universal 5-Tuple Server-Side Authorization Guard & BOLA/IDOR Protection.
Integrates AccessControlEngine (Subject, Role, Action, Resource, Context) into FastAPI routes.
"""

import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, Depends, HTTPException, status

from auth.access_control import (
    access_engine,
    Action,
    ResourceType,
    AccessContext,
    Decision
)
from auth.jwt_auth import get_current_user
from database.store import store

logger = logging.getLogger("securox.security_guard")


def require_access(
    resource: ResourceType,
    action: Action,
    object_id_param: Optional[str] = None
):
    """
    Reusable FastAPI Dependency Factory enforcing:
      1. Authentication Verification (valid token & active user)
      2. Auditor Read-Only Rule Enforcement
      3. Role & Permission Verification (RBAC)
      4. Object-Level Authorization (BOLA/IDOR for Healthcare, Traffic, Finance)
      5. 5-Tuple Context Evaluation (ABAC: Device Trust, Geo, Network, Time)
    """
    async def dependency(
        request: Request,
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        username = current_user.get("username", "anonymous")
        role = current_user.get("role", "viewer")
        domain = current_user.get("domain", "GLOBAL")
        department = current_user.get("department")
        jurisdiction = current_user.get("jurisdiction")
        branch = current_user.get("branch")
        assigned_patients = current_user.get("assigned_patients", [])

        # ── 1. AUDITOR READ-ONLY ENFORCEMENT ─────────────────────────
        if role == "auditor" and action not in (Action.VIEW, Action.EXPORT, Action.DOWNLOAD):
            await store.audit(
                username,
                "AUDITOR_WRITE_VIOLATION",
                f"{resource.value}:{action.value}",
                {"status": "BLOCKED", "reason": "Auditors are strictly restricted to read-only actions"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role 'auditor' is strictly read-only. Action '{action.value}' is prohibited."
            )

        # ── 2. RBAC STATIC PERMISSION CHECK ──────────────────────────
        has_rbac = access_engine.check_rbac(role, resource, action)
        if not has_rbac and role not in ("admin", "superadmin"):
            await store.audit(
                username,
                "RBAC_ACCESS_DENIED",
                f"{resource.value}:{action.value}",
                {"status": "BLOCKED", "role": role, "reason": "Missing required RBAC permission"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role '{role}' does not possess permission '{action.value}' on '{resource.value}'."
            )

        # ── 3. RESOLVE TARGET OBJECT ID FOR BOLA/IDOR ────────────────
        target_object_id = None
        if object_id_param:
            target_object_id = request.path_params.get(object_id_param)
            if not target_object_id and object_id_param in request.query_params:
                target_object_id = request.query_params.get(object_id_param)

        # ── 4. BOLA / IDOR OBJECT-LEVEL PROTECTION ───────────────────
        # A. Healthcare: Doctor & Nurse Patient Isolation
        if resource in (ResourceType.PATIENT_RECORD, ResourceType.CLINICAL_NOTE, ResourceType.PRESCRIPTION, ResourceType.LAB_REPORT):
            if role in ("doctor", "nurse") and target_object_id:
                patient = await store.get_patient(target_object_id)
                if patient:
                    patient_dept = patient.get("department", "")
                    is_assigned = (
                        target_object_id in assigned_patients or
                        patient.get("assigned_doctor_id") == username or
                        patient.get("assigned_nurse_id") == username
                    )
                    dept_matches = bool(department and patient_dept and patient_dept.lower() == department.lower())
                    
                    # Emergency Break-Glass Override Check
                    is_emergency = request.headers.get("X-Emergency-Break-Glass", "").lower() == "true"
                    
                    if not is_assigned and not dept_matches and not is_emergency:
                        await store.audit(
                            username,
                            "BOLA_HEALTHCARE_BLOCKED",
                            f"patient:{target_object_id}",
                            {
                                "status": "BLOCKED",
                                "user_dept": department,
                                "patient_dept": patient_dept,
                                "reason": "Out-of-department unauthorized clinical record query"
                            }
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access Denied (BOLA/IDOR): Clinician in '{department}' department cannot access patient '{target_object_id}' in '{patient_dept}' without clinical assignment or emergency break-glass."
                        )

        # B. Smart Traffic: Operator Jurisdiction Enforcement
        if resource == ResourceType.TRAFFIC_SIGNAL and action in (Action.UPDATE, Action.CONFIGURE, Action.APPROVE):
            if role in ("traffic_operator", "signal_technician"):
                if target_object_id:
                    signal = await store.get_traffic_signal(target_object_id)
                    if signal:
                        signal_zone = signal.get("zone", "")
                        if jurisdiction and jurisdiction != "ALL" and signal_zone:
                            if signal_zone.lower() != jurisdiction.lower():
                                await store.audit(
                                    username,
                                    "BOLA_TRAFFIC_BLOCKED",
                                    f"signal:{target_object_id}",
                                    {
                                        "status": "BLOCKED",
                                        "operator_jurisdiction": jurisdiction,
                                        "signal_zone": signal_zone,
                                        "reason": "Out-of-jurisdiction signal modification attempt"
                                    }
                                )
                                raise HTTPException(
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    detail=f"Access Denied (BOLA/IDOR): Traffic operator assigned to '{jurisdiction}' zone cannot modify signal '{target_object_id}' in '{signal_zone}' zone."
                                )

        # C. Finance: Customer Account Isolation & Branch Scopes
        if resource in (ResourceType.BANK_ACCOUNT, ResourceType.TRANSACTION):
            if role == "customer" and target_object_id:
                account = await store.get_bank_account(target_object_id)
                if account:
                    owner = account.get("customer_id")
                    user_cust_id = current_user.get("customer_id") or username
                    if owner != username and owner != current_user.get("id") and owner != user_cust_id:
                        await store.audit(
                            username,
                            "BOLA_FINANCE_BLOCKED",
                            f"account:{target_object_id}",
                            {"status": "BLOCKED", "owner": owner, "requester": username}
                        )
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Access Denied (BOLA/IDOR): Customer '{username}' cannot access bank account '{target_object_id}' owned by another customer."
                        )
            elif role in ("branch_manager", "teller") and target_object_id:
                account = await store.get_bank_account(target_object_id)
                if account:
                    acc_branch = account.get("branch")
                    if branch and branch != "ALL" and acc_branch:
                        if acc_branch.lower() != branch.lower():
                            await store.audit(
                                username,
                                "BOLA_BRANCH_BLOCKED",
                                f"account:{target_object_id}",
                                {"status": "BLOCKED", "user_branch": branch, "account_branch": acc_branch}
                            )
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Access Denied (BOLA/IDOR): Branch employee at '{branch}' cannot access account registered at '{acc_branch}'."
                            )

        # ── 5. ABAC CONTEXTUAL EVALUATION VIA ACCESS ENGINE ──────────
        client_ip = request.client.host if request.client else "127.0.0.1"
        device_id = request.headers.get("X-Device-ID", "DEV-CORPORATE-01")
        network_trust = request.headers.get("X-Network-Trust", "CORPORATE_SECURE")
        auth_strength = request.headers.get("X-Auth-Strength", "MFA_HARDWARE")
        geo_location = request.headers.get("X-Geo-Location", "Bengaluru, IN")
        previous_geo = request.headers.get("X-Previous-Geo")

        patient_scope = "assigned"
        if resource in (ResourceType.PATIENT_RECORD, ResourceType.CLINICAL_NOTE):
            if role in ("doctor", "nurse"):
                patient_scope = "assigned" if target_object_id in assigned_patients else "department"

        ctx = AccessContext(
            user_id=current_user.get("id", username),
            username=username,
            role=role,
            domain=domain,
            department=department,
            device_id=device_id,
            client_ip=client_ip,
            geo_location=geo_location,
            previous_geo=previous_geo,
            resource_id=target_object_id,
            patient_assignment=patient_scope,
            network_trust=network_trust,
            auth_strength=auth_strength
        )

        eval_result = access_engine.evaluate_access(ctx, resource, action)

        if eval_result.decision == Decision.BLOCK:
            await store.audit(
                username,
                "ABAC_POLICY_BLOCKED",
                f"{resource.value}:{action.value}",
                {
                    "status": "BLOCKED",
                    "risk_score": eval_result.risk_score,
                    "policy": eval_result.policy_triggered,
                    "reason": eval_result.reason
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden by Security Policy: {eval_result.reason}"
            )

        if eval_result.decision == Decision.STEP_UP_AUTH:
            if not request.headers.get("X-MFA-Verified"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="MFA Step-up authentication required for high-risk context access."
                )

        return current_user

    return dependency