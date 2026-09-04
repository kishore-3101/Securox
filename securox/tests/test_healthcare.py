import os
import sys
import pytest
from fastapi.testclient import TestClient

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from main import app
from auth.jwt_auth import create_access_token

client = TestClient(app)

def test_healthcare_health():
    resp = client.get('/api/healthcare/health')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'UP'
    assert data.get('service') == 'CAREGUARD'

def test_healthcare_overview():
    resp = client.get('/api/healthcare/overview')
    assert resp.status_code == 200
    data = resp.json()
    assert 'composite_risk_score' in data
    assert data.get('zero_synthetic_data_guarantee') is True

def test_healthcare_threats():
    resp = client.get('/api/healthcare/threats')
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('total_threats', 0) > 0
    assert isinstance(data.get('threats'), list)

def test_healthcare_dependencies():
    resp = client.get('/api/healthcare/dependencies')
    assert resp.status_code == 200
    data = resp.json()
    assert 'nodes' in data
    assert 'links' in data
    assert len(data['nodes']) >= 7

def test_healthcare_pathways():
    resp = client.get('/api/healthcare/pathways')
    assert resp.status_code == 200
    data = resp.json()
    assert 'pathways' in data
    assert len(data['pathways']) >= 5

def test_healthcare_exposure():
    resp = client.get('/api/healthcare/exposure')
    assert resp.status_code == 200
    data = resp.json()
    assert 'pathway_exposures' in data
    assert len(data['pathway_exposures']) >= 4

def test_healthcare_blast_radius():
    resp = client.get('/api/healthcare/blast-radius', params={'asset_id': 'EHR_CORE_GATEWAY'})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('target_asset_id') == 'EHR_CORE_GATEWAY'
    assert 'cascading_failure_depth' in data

def test_healthcare_response_action():
    payload = {
        'asset_id': 'EHR_CORE_GATEWAY',
        'action_type': 'RATE_LIMIT_HL7_INGRESS',
        'operator_notes': 'Pytest automated safeguard test'
    }
    token = create_access_token({"sub": "hospital_admin", "role": "hospital_admin"})
    resp = client.post('/api/healthcare/response', json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'LOGGED_INTENT'
    assert data.get('asset_id') == 'EHR_CORE_GATEWAY'

def test_healthcare_evidence_query():
    resp = client.get('/api/healthcare/evidence', params={'table_name': 'mimic_ed_triage', 'limit': 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('table_name') == 'mimic_ed_triage'
    assert data.get('count') > 0
    assert len(data.get('records', [])) > 0
