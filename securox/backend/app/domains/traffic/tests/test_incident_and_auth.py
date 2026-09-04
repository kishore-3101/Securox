import pytest
from traffic_core.traffic_db import SessionLocal
from traffic_core import traffic_models as models
from traffic_core.services.incident_service import incident_service
from traffic_core.services.auth_service import hash_password, verify_password, create_access_token
import jwt
from traffic_core.config import settings

def test_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123!"
    h, s = hash_password(raw_pwd)
    assert verify_password(raw_pwd, h, s) is True
    assert verify_password("WrongPassword!", h, s) is False

def test_jwt_token_flow():
    token = create_access_token({"sub": "analyst", "role": "ANALYST"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "analyst"
    assert payload["role"] == "ANALYST"

def test_incident_lifecycle():
    db = SessionLocal()
    try:
        # Create incident
        inc = incident_service.create_incident_from_correlation(
            db=db,
            title="Automated Test Incident",
            incident_type="CYBER_PHYSICAL",
            severity="HIGH",
            asset_id="TEST-ASSET-01",
            location="Sector 4 Approach",
            risk_score=78.0,
            evidence={"test_metric": 123},
            root_cause="Test verification root cause"
        )
        assert inc.status == "DETECTED"

        # Triage -> Acknowledge
        inc = incident_service.update_incident_status(
            db=db,
            incident_id=inc.incident_id,
            new_status="ACKNOWLEDGED",
            operator_name="UnitTester",
            note="Acknowledged in test"
        )
        assert inc.status == "ACKNOWLEDGED"
        assert inc.assigned_to == "UnitTester"

        # Resolve
        inc = incident_service.update_incident_status(
            db=db,
            incident_id=inc.incident_id,
            new_status="RESOLVED",
            operator_name="UnitTester",
            note="Resolved test incident"
        )
        assert inc.status == "RESOLVED"
        assert inc.resolved_at is not None

        # Verify forensic dossier
        dossier = incident_service.get_forensic_dossier(db, inc.incident_id)
        assert dossier["incident_id"] == inc.incident_id
        assert len(dossier["timeline"]) >= 3
    finally:
        db.close()
