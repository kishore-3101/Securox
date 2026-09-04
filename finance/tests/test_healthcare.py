import pytest
import requests

BASE_URL = 'http://127.0.0.1:8000'

def test_healthcare_health():
    resp = requests.get(f'{BASE_URL}/api/healthcare/health', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'UP'
    assert data.get('service') == 'CAREGUARD'

def test_healthcare_overview():
    resp = requests.get(f'{BASE_URL}/api/healthcare/overview', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert 'composite_risk_score' in data
    assert data.get('zero_synthetic_data_guarantee') is True

def test_healthcare_threats():
    resp = requests.get(f'{BASE_URL}/api/healthcare/threats', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('total_threats', 0) > 0
    assert isinstance(data.get('threats'), list)

def test_healthcare_dependencies():
    resp = requests.get(f'{BASE_URL}/api/healthcare/dependencies', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert 'nodes' in data
    assert 'links' in data
    assert len(data['nodes']) >= 7

def test_healthcare_pathways():
    resp = requests.get(f'{BASE_URL}/api/healthcare/pathways', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert 'pathways' in data
    assert len(data['pathways']) >= 5

def test_healthcare_exposure():
    resp = requests.get(f'{BASE_URL}/api/healthcare/exposure', timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert 'pathway_exposures' in data
    assert len(data['pathway_exposures']) >= 4

def test_healthcare_blast_radius():
    resp = requests.get(f'{BASE_URL}/api/healthcare/blast-radius', params={'asset_id': 'EHR_CORE_GATEWAY'}, timeout=5.0)
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
    resp = requests.post(f'{BASE_URL}/api/healthcare/response', json=payload, timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') == 'LOGGED_INTENT'
    assert data.get('asset_id') == 'EHR_CORE_GATEWAY'

def test_healthcare_evidence_query():
    resp = requests.get(f'{BASE_URL}/api/healthcare/evidence', params={'table_name': 'mimic_ed_triage', 'limit': 3}, timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('table_name') == 'mimic_ed_triage'
    assert data.get('count') > 0
    assert len(data.get('records', [])) > 0
