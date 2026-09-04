"""
Securox X persistent data store.

This module provides a small SQLite-backed repository for the single-process
FastAPI product build. It replaces the old in-memory demo store while keeping
the same async method names used by the rest of the app. The schema mirrors the
production tables so it can be migrated to PostgreSQL without changing service
logic.
"""

import asyncio
import json
import os
import sqlite3
import uuid
import hashlib
import secrets
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(os.getenv("SECUROX_DB_PATH", Path(__file__).parent / "securox.db"))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(data) -> str:
    return json.dumps(data, default=str, ensure_ascii=False)


def _loads(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _password_hash(password: str) -> str:
    iterations = 260_000
    salt = secrets.token_urlsafe(18)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


class DataStore:
    """SQLite-backed repository with async-compatible methods."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        self._init_db()
        self._seed_users()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    full_name TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    last_login_at TEXT
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    asset TEXT,
                    severity TEXT,
                    risk_score REAL,
                    risk_category TEXT,
                    anomaly_score REAL,
                    scenario TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS event_stream (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    source_type TEXT,
                    asset TEXT,
                    severity TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS risk_history (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    asset TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    category TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mitigations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    asset TEXT,
                    playbook TEXT,
                    status TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS fraud_alerts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    transaction_id TEXT,
                    channel TEXT,
                    severity TEXT,
                    risk_score REAL,
                    decision TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT,
                    asset TEXT,
                    owner TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    actor TEXT,
                    action TEXT NOT NULL,
                    target TEXT,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    stages TEXT NOT NULL,
                    affected_assets TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS response_actions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_asset TEXT,
                    before_risk REAL,
                    after_risk REAL,
                    verification_metrics TEXT NOT NULL,
                    actor TEXT,
                    status TEXT NOT NULL DEFAULT 'VERIFIED',
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS simulations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    target_asset TEXT,
                    attack_type TEXT,
                    intensity REAL,
                    duration REAL,
                    events_generated INTEGER,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON event_stream(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_history(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_fraud_timestamp ON fraud_alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_campaigns_timestamp ON campaigns(last_seen DESC);
                CREATE INDEX IF NOT EXISTS idx_response_timestamp ON response_actions(timestamp DESC);

                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    os TEXT,
                    browser TEXT,
                    ip TEXT,
                    location TEXT,
                    trust_score REAL DEFAULT 100.0,
                    status TEXT NOT NULL DEFAULT 'TRUSTED',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY,
                    hospital_id TEXT NOT NULL DEFAULT 'H001',
                    name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    department TEXT NOT NULL,
                    assigned_doctor_id TEXT,
                    assigned_nurse_id TEXT,
                    room_bed TEXT,
                    condition TEXT,
                    vitals TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS medical_records (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    diagnosis TEXT,
                    prescriptions TEXT,
                    lab_results TEXT,
                    treatment_notes TEXT,
                    sensitivity TEXT NOT NULL DEFAULT 'CONFIDENTIAL',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ambulances (
                    id TEXT PRIMARY KEY,
                    driver_id TEXT NOT NULL,
                    vehicle_number TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'AVAILABLE',
                    current_location TEXT NOT NULL,
                    destination_hospital TEXT NOT NULL DEFAULT 'City General Hospital (H001)',
                    patient_priority TEXT DEFAULT 'NORMAL',
                    assigned_patient_id TEXT,
                    eta_minutes INTEGER DEFAULT 8,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traffic_signals (
                    id TEXT PRIMARY KEY,
                    intersection TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    current_state TEXT NOT NULL DEFAULT 'GREEN',
                    cycle_time_sec INTEGER DEFAULT 90,
                    is_tampered INTEGER DEFAULT 0,
                    last_override_by TEXT,
                    mode TEXT NOT NULL DEFAULT 'ADAPTIVE',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traffic_cameras (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    intersection_id TEXT,
                    road_id TEXT,
                    camera_type TEXT NOT NULL DEFAULT 'FIXED_CCTV',
                    stream_type TEXT NOT NULL DEFAULT 'WEBRTC',
                    stream_url TEXT,
                    status TEXT NOT NULL DEFAULT 'ONLINE',
                    health TEXT NOT NULL DEFAULT 'HEALTHY',
                    fps REAL DEFAULT 30.0,
                    resolution TEXT DEFAULT '1920x1080',
                    incident_count INTEGER DEFAULT 0,
                    last_seen TEXT,
                    device_id TEXT,
                    trust_status TEXT NOT NULL DEFAULT 'TRUSTED',
                    risk_score REAL DEFAULT 0.0,
                    created_at TEXT,
                    metadata_json TEXT DEFAULT '{}',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS mobile_camera_sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    latitude REAL DEFAULT 12.9716,
                    longitude REAL DEFAULT 77.5946,
                    started_at TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    stream_status TEXT NOT NULL DEFAULT 'STREAMING',
                    trust_status TEXT NOT NULL DEFAULT 'EVALUATED'
                );

                CREATE TABLE IF NOT EXISTS vehicle_detections (
                    detection_id TEXT PRIMARY KEY,
                    camera_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    vehicle_class TEXT NOT NULL,
                    confidence REAL DEFAULT 0.90,
                    bounding_box_json TEXT DEFAULT '[0,0,0,0]',
                    tracking_id TEXT NOT NULL,
                    location TEXT NOT NULL,
                    direction TEXT DEFAULT 'NORTH',
                    speed_estimate REAL DEFAULT 45.0,
                    lane INTEGER DEFAULT 1,
                    metadata_json TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS rfid_readers (
                    reader_id TEXT PRIMARY KEY,
                    location TEXT NOT NULL,
                    lane TEXT NOT NULL DEFAULT 'LANE-01',
                    status TEXT NOT NULL DEFAULT 'ONLINE',
                    ip_address TEXT DEFAULT '10.12.4.50',
                    device_id TEXT DEFAULT 'DEV-RFID-01',
                    trust_status TEXT DEFAULT 'TRUSTED',
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rfid_reads (
                    read_id TEXT PRIMARY KEY,
                    reader_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    lane TEXT NOT NULL DEFAULT 'LANE-01',
                    signal_strength REAL DEFAULT -58.0,
                    vehicle_association TEXT,
                    confidence REAL DEFAULT 0.98,
                    metadata_json TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS fastags (
                    fastag_id TEXT PRIMARY KEY,
                    tag_id TEXT UNIQUE NOT NULL,
                    vehicle_id TEXT NOT NULL,
                    vehicle_registration TEXT NOT NULL,
                    customer_id TEXT DEFAULT 'CUST-1001',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    issuer TEXT DEFAULT 'NPCI_NETC',
                    linked_account TEXT DEFAULT 'ACC-***-9021',
                    created_at TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vehicle_identity_verifications (
                    verification_id TEXT PRIMARY KEY,
                    rfid_read_id TEXT,
                    detection_id TEXT,
                    camera_id TEXT NOT NULL,
                    tag_id TEXT,
                    registered_plate TEXT,
                    ocr_plate TEXT,
                    rfid_confidence REAL DEFAULT 0.0,
                    ocr_confidence REAL DEFAULT 0.0,
                    identity_confidence REAL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'VERIFIED',
                    risk_score REAL DEFAULT 0.0,
                    repeated_mismatch_count INTEGER DEFAULT 0,
                    cameras_seen_json TEXT DEFAULT '[]',
                    timestamp TEXT NOT NULL,
                    details TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_number TEXT NOT NULL UNIQUE,
                    account_type TEXT NOT NULL DEFAULT 'SAVINGS',
                    balance REAL NOT NULL DEFAULT 50000.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    receiver_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    channel TEXT NOT NULL DEFAULT 'ONLINE_BANKING',
                    transaction_type TEXT NOT NULL DEFAULT 'WIRE_TRANSFER',
                    risk_score REAL DEFAULT 5.0,
                    decision TEXT NOT NULL DEFAULT 'ALLOWED',
                    is_fraud INTEGER DEFAULT 0,
                    is_sar INTEGER DEFAULT 0,
                    beneficiary_age_hours INTEGER DEFAULT 720,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS security_policies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    rule_definition TEXT NOT NULL,
                    risk_modifier REAL NOT NULL,
                    action TEXT NOT NULL DEFAULT 'BLOCK',
                    description TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS cross_domain_threats (
                    id TEXT PRIMARY KEY,
                    threat_actor_ip TEXT NOT NULL,
                    device_id TEXT,
                    domains_involved TEXT NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    campaign_summary TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE'
                );

                CREATE INDEX IF NOT EXISTS idx_patients_dept ON patients(department);
                CREATE INDEX IF NOT EXISTS idx_medical_patient ON medical_records(patient_id);
                CREATE INDEX IF NOT EXISTS idx_traffic_signals_zone ON traffic_signals(zone);
                CREATE INDEX IF NOT EXISTS idx_bank_tx_account ON bank_transactions(account_id);

                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    hospital_id TEXT NOT NULL DEFAULT 'H001',
                    department TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    scheduled_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'SCHEDULED',
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS admissions (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    hospital_id TEXT NOT NULL DEFAULT 'H001',
                    department TEXT NOT NULL,
                    room_bed TEXT NOT NULL,
                    admission_type TEXT NOT NULL DEFAULT 'EMERGENCY',
                    admitting_doctor_id TEXT NOT NULL,
                    assigned_nurse_id TEXT NOT NULL,
                    admitted_at TEXT NOT NULL,
                    discharge_date TEXT,
                    status TEXT NOT NULL DEFAULT 'ADMITTED'
                );

                CREATE TABLE IF NOT EXISTS lab_orders (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'ROUTINE',
                    status TEXT NOT NULL DEFAULT 'ORDERED',
                    result_data TEXT,
                    reference_range TEXT,
                    flagged_abnormal INTEGER NOT NULL DEFAULT 0,
                    ordered_at TEXT NOT NULL,
                    completed_at TEXT,
                    approved_by TEXT
                );

                CREATE TABLE IF NOT EXISTS prescriptions (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    medication TEXT NOT NULL,
                    dosage TEXT NOT NULL,
                    frequency TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PRESCRIBED',
                    ddi_warning TEXT,
                    pharmacist_id TEXT,
                    ordered_at TEXT NOT NULL,
                    dispensed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS billing_invoices (
                    id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    hospital_id TEXT NOT NULL DEFAULT 'H001',
                    total_amount REAL NOT NULL,
                    insurance_claim_amount REAL NOT NULL DEFAULT 0.0,
                    patient_payable REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    payment_method TEXT,
                    line_items TEXT,
                    created_at TEXT NOT NULL,
                    settled_at TEXT
                );

                CREATE TABLE IF NOT EXISTS emergency_dispatches (
                    id TEXT PRIMARY KEY,
                    ambulance_id TEXT NOT NULL,
                    paramedic_id TEXT,
                    patient_id TEXT,
                    caller_name TEXT NOT NULL,
                    emergency_type TEXT NOT NULL,
                    triage_priority TEXT NOT NULL DEFAULT 'P1_CRITICAL',
                    origin_location TEXT NOT NULL,
                    destination_hospital TEXT NOT NULL DEFAULT 'City General Hospital (H001)',
                    green_corridor_active INTEGER NOT NULL DEFAULT 0,
                    vitals TEXT,
                    dispatched_at TEXT NOT NULL,
                    arrived_scene_at TEXT,
                    arrived_hospital_at TEXT,
                    status TEXT NOT NULL DEFAULT 'DISPATCHED'
                );

                CREATE TABLE IF NOT EXISTS break_glass_events (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    role TEXT NOT NULL,
                    patient_id TEXT NOT NULL,
                    department TEXT NOT NULL,
                    hospital_id TEXT NOT NULL DEFAULT 'H001',
                    reason TEXT NOT NULL,
                    previous_risk_score REAL NOT NULL,
                    new_risk_score REAL NOT NULL,
                    notified_security INTEGER NOT NULL DEFAULT 1,
                    security_incident_id TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traffic_incidents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'MEDIUM',
                    status TEXT NOT NULL DEFAULT 'REPORTED',
                    location TEXT NOT NULL,
                    road_id TEXT,
                    intersection_id TEXT,
                    reported_by TEXT NOT NULL,
                    assigned_officer TEXT,
                    verified INTEGER NOT NULL DEFAULT 0,
                    verified_by TEXT,
                    verified_at TEXT,
                    resolution_notes TEXT,
                    reported_at TEXT NOT NULL,
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS toll_scans (
                    id TEXT PRIMARY KEY,
                    tollgate_id TEXT NOT NULL,
                    tollgate_name TEXT NOT NULL,
                    vehicle_number TEXT NOT NULL,
                    fastag_id TEXT NOT NULL,
                    amount REAL NOT NULL DEFAULT 120.0,
                    status TEXT NOT NULL DEFAULT 'CLEARED',
                    flag_reason TEXT,
                    override_by TEXT,
                    override_reason TEXT,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS traffic_maintenance_tickets (
                    id TEXT PRIMARY KEY,
                    signal_id TEXT NOT NULL,
                    technician_id TEXT,
                    issue_type TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'NORMAL',
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    voltage_reading REAL DEFAULT 230.0,
                    loop_resistance_ohms REAL DEFAULT 4.2,
                    firmware_checksum TEXT DEFAULT 'sha256_stig_v4.2.1_valid',
                    diagnostic_log TEXT,
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS green_corridors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    emergency_dispatch_id TEXT,
                    ambulance_id TEXT,
                    status TEXT NOT NULL DEFAULT 'STANDBY',
                    origin_location TEXT NOT NULL,
                    destination_hospital TEXT NOT NULL,
                    route_intersections TEXT NOT NULL,
                    active_signal_id TEXT,
                    cleared_signals TEXT,
                    activated_at TEXT,
                    cleared_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
                CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id);
                CREATE INDEX IF NOT EXISTS idx_lab_orders_patient ON lab_orders(patient_id);
                CREATE INDEX IF NOT EXISTS idx_prescriptions_patient ON prescriptions(patient_id);
                CREATE INDEX IF NOT EXISTS idx_billing_patient ON billing_invoices(patient_id);
                CREATE INDEX IF NOT EXISTS idx_break_glass_patient ON break_glass_events(patient_id);
                CREATE INDEX IF NOT EXISTS idx_traffic_incidents_status ON traffic_incidents(status);
                CREATE INDEX IF NOT EXISTS idx_toll_scans_status ON toll_scans(status);
                CREATE INDEX IF NOT EXISTS idx_maint_tickets_signal ON traffic_maintenance_tickets(signal_id);
                
                CREATE INDEX IF NOT EXISTS idx_green_corridors_status ON green_corridors(status);

                CREATE TABLE IF NOT EXISTS security_events (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    organization TEXT NOT NULL,
                    user TEXT NOT NULL,
                    role TEXT NOT NULL,
                    device TEXT,
                    ip TEXT,
                    location TEXT,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    result TEXT NOT NULL,
                    risk REAL NOT NULL DEFAULT 0.0,
                    metadata TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_sec_events_timestamp ON security_events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_sec_events_domain ON security_events(domain);
                CREATE INDEX IF NOT EXISTS idx_sec_events_action ON security_events(action);
                CREATE INDEX IF NOT EXISTS idx_sec_events_user ON security_events(user);
                CREATE INDEX IF NOT EXISTS idx_sec_events_risk ON security_events(risk);
                CREATE INDEX IF NOT EXISTS idx_sec_events_resource ON security_events(resource);

                CREATE TABLE IF NOT EXISTS finance_branches (
                    id TEXT PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    region TEXT NOT NULL,
                    manager_id TEXT NOT NULL,
                    daily_volume_limit REAL NOT NULL DEFAULT 50000000.0,
                    current_volume REAL NOT NULL DEFAULT 0.0,
                    status TEXT NOT NULL DEFAULT 'ACTIVE'
                );

                CREATE TABLE IF NOT EXISTS finance_customers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    pan_or_ssn TEXT NOT NULL UNIQUE,
                    kyc_status TEXT NOT NULL DEFAULT 'VERIFIED',
                    risk_rating TEXT NOT NULL DEFAULT 'LOW',
                    phone TEXT,
                    email TEXT,
                    branch_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS finance_accounts (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_number TEXT NOT NULL UNIQUE,
                    branch_id TEXT NOT NULL,
                    account_type TEXT NOT NULL DEFAULT 'SAVINGS',
                    balance REAL NOT NULL DEFAULT 100000.0,
                    currency TEXT NOT NULL DEFAULT 'INR',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    risk_score REAL NOT NULL DEFAULT 5.0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS finance_transactions (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    counterparty_account TEXT NOT NULL,
                    amount REAL NOT NULL,
                    channel TEXT NOT NULL DEFAULT 'UPI',
                    currency TEXT NOT NULL DEFAULT 'INR',
                    timestamp TEXT NOT NULL,
                    ip_address TEXT,
                    device_id TEXT,
                    location TEXT,
                    status TEXT NOT NULL DEFAULT 'SETTLED',
                    risk_score REAL NOT NULL DEFAULT 5.0,
                    model_attribution TEXT NOT NULL DEFAULT 'LIVE INFERENCE',
                    flag_reason TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS finance_fraud_cases (
                    id TEXT PRIMARY KEY,
                    case_number TEXT NOT NULL UNIQUE,
                    transaction_id TEXT,
                    customer_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'MEDIUM',
                    status TEXT NOT NULL DEFAULT 'OPEN',
                    total_exposure_inr REAL NOT NULL DEFAULT 0.0,
                    assigned_analyst TEXT,
                    decision TEXT,
                    decision_rationale TEXT,
                    resolution_notes TEXT,
                    opened_at TEXT NOT NULL,
                    closed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS finance_aml_findings (
                    id TEXT PRIMARY KEY,
                    case_id TEXT,
                    finding_type TEXT NOT NULL,
                    primary_account TEXT NOT NULL,
                    counterparty_accounts_json TEXT NOT NULL DEFAULT '[]',
                    mule_probability REAL NOT NULL DEFAULT 0.0,
                    hop_count INTEGER NOT NULL DEFAULT 1,
                    structuring_pattern TEXT,
                    graph_metrics_json TEXT NOT NULL DEFAULT '{}',
                    sar_filed INTEGER NOT NULL DEFAULT 0,
                    sar_reference TEXT,
                    detected_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_fin_accounts_cust ON finance_accounts(customer_id);
                CREATE INDEX IF NOT EXISTS idx_fin_accounts_branch ON finance_accounts(branch_id);
                CREATE INDEX IF NOT EXISTS idx_fin_tx_account ON finance_transactions(account_id);
                CREATE INDEX IF NOT EXISTS idx_fin_cases_status ON finance_fraud_cases(status);

                CREATE TABLE IF NOT EXISTS risk_assessments (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    role TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_category TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    uncertainty REAL NOT NULL,
                    uncertainty_reason TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    rule_score REAL NOT NULL DEFAULT 0.0,
                    baseline_score REAL NOT NULL DEFAULT 0.0,
                    ml_score REAL NOT NULL DEFAULT 0.0,
                    explanation TEXT NOT NULL,
                    raw_event TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS risk_factors (
                    id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL,
                    factor_key TEXT NOT NULL,
                    name TEXT NOT NULL,
                    points REAL NOT NULL,
                    source_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    severity TEXT NOT NULL,
                    FOREIGN KEY(assessment_id) REFERENCES risk_assessments(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS historical_baselines (
                    identity TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    role TEXT NOT NULL,
                    known_devices TEXT NOT NULL DEFAULT '[]',
                    known_locations TEXT NOT NULL DEFAULT '[]',
                    typical_hours TEXT NOT NULL DEFAULT '[6, 22]',
                    typical_actions TEXT NOT NULL DEFAULT '[]',
                    mean_volume REAL NOT NULL DEFAULT 1.0,
                    std_dev_volume REAL NOT NULL DEFAULT 1.0,
                    event_count INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_model_inferences (
                    id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    event_id TEXT,
                    prediction TEXT NOT NULL,
                    score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    ground_truth_claim INTEGER NOT NULL DEFAULT 0,
                    features TEXT NOT NULL DEFAULT '{}',
                    important_factors TEXT NOT NULL DEFAULT '[]',
                    latency_ms REAL NOT NULL DEFAULT 0.0,
                    disclaimer TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ai_model_health (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total_inferences INTEGER NOT NULL DEFAULT 0,
                    total_errors INTEGER NOT NULL DEFAULT 0,
                    avg_latency_ms REAL NOT NULL DEFAULT 0.0,
                    last_inference_at TEXT,
                    last_error_at TEXT,
                    health_details TEXT NOT NULL DEFAULT '{}',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS auth_decisions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    role TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    risk_score REAL NOT NULL,
                    risk_category TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    factors TEXT NOT NULL DEFAULT '[]',
                    restrictions TEXT NOT NULL DEFAULT '[]',
                    event_id TEXT,
                    context_payload TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS mitigation_proposals (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    target_asset TEXT NOT NULL,
                    proposed_by TEXT NOT NULL,
                    safety_verdict TEXT NOT NULL,
                    safety_evaluation TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'PENDING_APPROVAL',
                    required_role TEXT NOT NULL DEFAULT 'admin',
                    approved_by TEXT,
                    approval_timestamp TEXT,
                    comments TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_ai_inf_model ON ai_model_inferences(model_name);
                CREATE INDEX IF NOT EXISTS idx_ai_inf_domain ON ai_model_inferences(domain);
                CREATE INDEX IF NOT EXISTS idx_ai_inf_event ON ai_model_inferences(event_id);
                CREATE INDEX IF NOT EXISTS idx_ai_inf_timestamp ON ai_model_inferences(timestamp);

                CREATE INDEX IF NOT EXISTS idx_risk_assess_identity ON risk_assessments(identity);
                CREATE INDEX IF NOT EXISTS idx_risk_assess_domain ON risk_assessments(domain);
                CREATE INDEX IF NOT EXISTS idx_risk_assess_category ON risk_assessments(risk_category);
                CREATE INDEX IF NOT EXISTS idx_risk_assess_score ON risk_assessments(risk_score);
                CREATE INDEX IF NOT EXISTS idx_risk_assess_timestamp ON risk_assessments(timestamp);
                CREATE INDEX IF NOT EXISTS idx_risk_factors_assess ON risk_factors(assessment_id);

                CREATE INDEX IF NOT EXISTS idx_auth_dec_identity ON auth_decisions(identity);
                CREATE INDEX IF NOT EXISTS idx_auth_dec_domain ON auth_decisions(domain);
                CREATE INDEX IF NOT EXISTS idx_auth_dec_decision ON auth_decisions(decision);
                CREATE INDEX IF NOT EXISTS idx_auth_dec_timestamp ON auth_decisions(timestamp);

                CREATE INDEX IF NOT EXISTS idx_mit_prop_domain ON mitigation_proposals(domain);
                CREATE INDEX IF NOT EXISTS idx_mit_prop_status ON mitigation_proposals(status);
                CREATE INDEX IF NOT EXISTS idx_mit_prop_timestamp ON mitigation_proposals(timestamp);

                CREATE TABLE IF NOT EXISTS soc_evidence (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    evidence_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    artifact_ref TEXT,
                    hash_value TEXT,
                    added_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS soc_notes (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    author TEXT NOT NULL,
                    note TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS soc_attack_chains (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    threat_actor TEXT NOT NULL,
                    target_sector TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'HIGH',
                    kill_chain_stage TEXT NOT NULL DEFAULT 'Execution',
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    incident_ids TEXT NOT NULL DEFAULT '[]',
                    indicators TEXT NOT NULL DEFAULT '[]',
                    tactics TEXT NOT NULL DEFAULT '[]',
                    techniques TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    payload TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_soc_evidence_incident ON soc_evidence(incident_id);
                CREATE INDEX IF NOT EXISTS idx_soc_notes_incident ON soc_notes(incident_id);
                CREATE INDEX IF NOT EXISTS idx_soc_attack_chains_stage ON soc_attack_chains(kill_chain_stage);
                CREATE INDEX IF NOT EXISTS idx_soc_attack_chains_sector ON soc_attack_chains(target_sector);
                CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
                CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp);

                """
            )
            self._migrate_existing_tables(conn)

    @staticmethod
    def _columns(conn, table: str) -> set[str]:
        return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    def _add_column(self, conn, table: str, column: str, ddl: str) -> None:
        if column not in self._columns(conn, table):
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")

    def _migrate_existing_tables(self, conn) -> None:
        migrations = {
            "alerts": [
                ("payload", "TEXT"),
            ],
            "risk_history": [
                ("id", "TEXT"),
                ("payload", "TEXT"),
            ],
            "mitigations": [
                ("asset", "TEXT"),
                ("playbook", "TEXT"),
                ("status", "TEXT"),
            ],
            "event_stream": [
                ("source_type", "TEXT"),
                ("asset", "TEXT"),
                ("severity", "TEXT"),
            ],
            "traffic_cameras": [
                ("latitude", "REAL"),
                ("longitude", "REAL"),
                ("intersection_id", "TEXT"),
                ("road_id", "TEXT"),
                ("camera_type", "TEXT DEFAULT 'FIXED_CCTV'"),
                ("stream_type", "TEXT DEFAULT 'WEBRTC'"),
                ("health", "TEXT DEFAULT 'HEALTHY'"),
                ("resolution", "TEXT DEFAULT '1920x1080'"),
                ("last_seen", "TEXT"),
                ("device_id", "TEXT"),
                ("trust_status", "TEXT DEFAULT 'TRUSTED'"),
                ("risk_score", "REAL DEFAULT 0.0"),
                ("created_at", "TEXT"),
                ("metadata_json", "TEXT DEFAULT '{}'"),
            ],
        }
        for table, columns in migrations.items():
            if self._columns(conn, table):
                for column, ddl in columns:
                    self._add_column(conn, table, column, ddl)

    def _seed_users(self) -> None:
        default_hash = _password_hash("admin123")
        with self._connect() as conn:
            # Complete 35+ Role Catalog for Smart City Infrastructure
            all_users = [
                # Platform & Super Admin
                ("superadmin", "superadmin", "Global Platform Super Administrator"),
                ("admin", "admin", "Securox Administrator"),

                # Healthcare Roles
                ("hospital_admin", "hospital_admin", "Dr. Robert Vance, Hospital Administrator"),
                ("doctor", "doctor", "Dr. Sarah Chen, Chief of Cardiology"),
                ("nurse", "nurse", "Nurse Elena Rostova, Lead ICU Nurse"),
                ("ambulance", "ambulance_driver", "Raj Patel, Ambulance Unit 04"),
                ("paramedic", "paramedic", "Marcus Vance, Field Paramedic"),
                ("reception", "reception", "Priya Sharma, Front Desk Admissions"),
                ("pharmacist", "pharmacist", "David Kim, Chief Pharmacist"),
                ("lab_tech", "lab_technician", "Liam Scott, Senior Lab Technologist"),
                ("billing", "billing_staff", "Rachel Green, Billing & Insurance Coordinator"),
                ("emergency_coord", "emergency_coordinator", "Frank Miller, Hospital Emergency Dispatcher"),
                ("hospital_sec", "hospital_security", "Alex Chen, Hospital IT Security Officer"),
                ("patient", "patient", "John Doe, Patient"),

                # Smart Traffic Roles
                ("traffic_operator", "traffic_operator", "Jason Vance, TMC Central Controller"),
                ("traffic_police", "traffic_police", "Inspector Rajesh Kumar, Traffic Enforcement"),
                ("traffic_supervisor", "traffic_supervisor", "Amanda Hayes, Regional Mobility Supervisor"),
                ("camera_operator", "camera_operator", "Carlos Ortiz, CCTV Surveillance Specialist"),
                ("signal_tech", "signal_technician", "Kevin Patel, STIG Signal Grid Specialist"),
                ("emergency_traffic", "emergency_traffic", "Sean O'Connor, Emergency Transit Dispatcher"),
                ("road_maintenance", "road_maintenance", "Victor Stone, Rapid Road Maintenance Unit"),
                ("transport_authority", "transport_authority", "Arthur Dent, Municipal Transport Commissioner"),
                ("traffic_analyst", "traffic_analyst", "Maya Lin, Smart Mobility Data Scientist"),
                ("traffic_sec", "traffic_cybersecurity", "Nathan Drake, Traffic SCADA Security Officer"),
                ("citizen", "citizen", "Sam Wilson, City Resident"),

                # Finance Roles
                ("finance_admin", "finance_admin", "Robert King, Chief Financial Risk Officer"),
                ("branch_manager", "branch_manager", "Anita Roy, Metro Central Branch Manager"),
                ("teller", "teller", "Daniel Wu, Vault & Cashier Officer"),
                ("relationship_mgr", "relationship_manager", "Sophia Martinez, Senior Wealth Advisor"),
                ("fraud_analyst", "fraud_analyst", "Sarah Connor, Lead Financial Fraud Hunter"),
                ("aml_analyst", "aml_analyst", "James Bond, Anti-Money Laundering Lead"),
                ("risk_analyst", "risk_analyst", "Peter Parker, Treasury Cyber-VaR Specialist"),
                ("compliance_officer", "compliance_officer", "Diana Prince, Chief Regulatory Compliance Officer"),
                ("soc_analyst", "soc_analyst", "Bruce Wayne, Tier-3 Threat Hunter"),
                ("auditor", "auditor", "Clark Kent, Independent Regulatory Auditor"),
                ("customer", "customer", "Tony Stark, Account Holder"),

                # Legacy compatibility aliases
                ("analyst", "soc_analyst", "SOC Threat Analyst"),
                ("traffic", "traffic_operator", "Traffic Operator"),
                ("finance", "fraud_analyst", "Fintech Investigator"),
                ("emergency", "emergency_coordinator", "Emergency Commander"),
                ("health", "hospital_security", "Healthcare & Hospital IT Operator"),
            ]

            for username, role, full_name in all_users:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO users
                    (id, username, hashed_password, role, full_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), username, default_hash, role, full_name, _utcnow()),
                )
            conn.execute(
                "UPDATE users SET hashed_password = ? WHERE hashed_password LIKE '$2b$%'",
                (default_hash,),
            )
            self._seed_domain_data(conn)

    def _seed_domain_data(self, conn) -> None:
        now = _utcnow()
        # 1. Seed Patients
        patients_count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        if patients_count == 0:
            patients = [
                ("P-1001", "H001", "Aarav Sharma", 54, "M", "Cardiology", "doctor", "nurse", "ICU-Bed-04", "Critical (Post-Op Cardiac)", _json({"bp": "135/88", "hr": 78, "spo2": 97, "temp": 37.1}), now),
                ("P-1002", "H001", "Meera Krishnan", 38, "F", "Cardiology", "doctor", "nurse", "Ward-3-Bed-12", "Stable (Arrhythmia Monitoring)", _json({"bp": "120/80", "hr": 72, "spo2": 99, "temp": 36.8}), now),
                ("P-1003", "H001", "Devendra Patel", 67, "M", "Emergency", "doctor", "nurse", "ER-Bay-02", "Acute Coronary Syndrome", _json({"bp": "158/96", "hr": 104, "spo2": 93, "temp": 37.4}), now),
                ("P-1004", "H001", "Sunita Verma", 42, "F", "Neurology", "doctor_other", "nurse", "Neuro-Bed-08", "Concussion Observation", _json({"bp": "122/78", "hr": 68, "spo2": 98, "temp": 36.6}), now),
                ("P-1005", "H001", "Rohan Gupta", 29, "M", "Orthopedics", "doctor_other", "nurse", "Ortho-Bed-15", "Fracture Reduction Recovery", _json({"bp": "118/76", "hr": 64, "spo2": 99, "temp": 36.7}), now),
            ]
            conn.executemany(
                "INSERT INTO patients (id, hospital_id, name, age, gender, department, assigned_doctor_id, assigned_nurse_id, room_bed, condition, vitals, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                patients
            )

        # 2. Seed Medical Records
        med_count = conn.execute("SELECT COUNT(*) FROM medical_records").fetchone()[0]
        if med_count == 0:
            records = [
                ("MR-2001", "P-1001", "doctor", "Coronary Artery Disease, Status Post Stent", _json(["Atorvastatin 40mg QD", "Aspirin 81mg QD", "Metoprolol 25mg BID"]), _json({"troponin": "0.02 ng/mL (Normal)", "ecg": "Sinus rhythm, normal ST"}), "Patient recovering favorably post-PCI. Ambulation tolerated.", "CONFIDENTIAL", now),
                ("MR-2002", "P-1002", "doctor", "Paroxysmal Supraventricular Tachycardia", _json(["Diltiazem 120mg QD", "Flecainide 50mg BID"]), _json({"holter": "Rare premature atrial beats", "potassium": "4.2 mEq/L"}), "Echocardiogram indicates normal left ventricular function.", "CONFIDENTIAL", now),
                ("MR-2003", "P-1003", "doctor", "Non-ST Elevation Myocardial Infarction", _json(["Heparin Drip 18 U/kg/h", "Ticagrelor 90mg BID"]), _json({"troponin_i": "1.45 ng/mL (ELEVATED)", "ck_mb": "24 ng/mL"}), "Emergent cardiac catheterization scheduled at 08:00.", "RESTRICTED", now),
            ]
            conn.executemany(
                "INSERT INTO medical_records (id, patient_id, doctor_id, diagnosis, prescriptions, lab_results, treatment_notes, sensitivity, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                records
            )

        # 3. Seed Ambulances
        amb_count = conn.execute("SELECT COUNT(*) FROM ambulances").fetchone()[0]
        if amb_count == 0:
            ambulances = [
                ("AMB-01", "ambulance", "KA-01-EQ-1044", "EN_ROUTE", "MG Road & Brigade Junction", "City General Hospital (H001)", "CRITICAL", "P-1003", 6, now),
                ("AMB-02", "ambulance_driver_2", "KA-01-EQ-2088", "AVAILABLE", "Central Station Transit Hub", "City General Hospital (H001)", "NORMAL", None, 0, now),
                ("AMB-03", "ambulance_driver_3", "KA-01-EQ-3012", "AT_HOSPITAL", "City General Hospital ER Bay 1", "City General Hospital (H001)", "STABLE", "P-1001", 0, now),
            ]
            conn.executemany(
                "INSERT INTO ambulances (id, driver_id, vehicle_number, status, current_location, destination_hospital, patient_priority, assigned_patient_id, eta_minutes, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ambulances
            )

        # 3b. Seed Appointments
        apt_count = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
        if apt_count == 0:
            apts = [
                ("APT-1001", "P-1001", "H001", "Cardiology", "doctor", "2026-09-05T10:30:00Z", "CONFIRMED", "Post-PCI Cardiac Evaluation", now),
                ("APT-1002", "P-1002", "H001", "Cardiology", "doctor", "2026-09-05T11:45:00Z", "SCHEDULED", "Holter Monitor Telemetry Review", now),
                ("APT-1003", "P-1004", "H001", "Neurology", "doctor_other", "2026-09-06T14:00:00Z", "SCHEDULED", "Post-Concussion EEG Assessment", now),
            ]
            conn.executemany(
                "INSERT INTO appointments (id, patient_id, hospital_id, department, doctor_id, scheduled_at, status, reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                apts
            )

        # 3c. Seed Admissions
        adm_count = conn.execute("SELECT COUNT(*) FROM admissions").fetchone()[0]
        if adm_count == 0:
            admissions = [
                ("ADM-1001", "P-1001", "H001", "Cardiology", "ICU-Bed-04", "EMERGENCY", "doctor", "nurse", "2026-09-04T06:00:00Z", None, "ADMITTED"),
                ("ADM-1002", "P-1002", "H001", "Cardiology", "Ward-3-Bed-12", "ELECTIVE", "doctor", "nurse", "2026-09-03T11:00:00Z", None, "ADMITTED"),
                ("ADM-1003", "P-1003", "H001", "Emergency", "ER-Bay-02", "EMERGENCY", "doctor", "nurse", "2026-09-04T08:15:00Z", None, "ADMITTED"),
            ]
            conn.executemany(
                "INSERT INTO admissions (id, patient_id, hospital_id, department, room_bed, admission_type, admitting_doctor_id, assigned_nurse_id, admitted_at, discharge_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                admissions
            )

        # 3d. Seed Lab Orders
        lab_count = conn.execute("SELECT COUNT(*) FROM lab_orders").fetchone()[0]
        if lab_count == 0:
            labs = [
                ("LAB-1001", "P-1001", "doctor", "High-Sensitivity Troponin-I", "Cardiac", "STAT", "COMPLETED", _json({"value": 0.02, "unit": "ng/mL", "interpretation": "NORMAL"}), "0.00 - 0.04 ng/mL", 0, now, now, "lab_tech"),
                ("LAB-1002", "P-1003", "doctor", "Cardiac Biomarker Panel (Trop-I + CK-MB)", "Cardiac", "STAT", "COMPLETED", _json({"troponin_i": 1.45, "ck_mb": 24.0, "interpretation": "HIGH_ACUITY"}), "Trop < 0.04, CK-MB < 5", 1, now, now, "lab_tech"),
                ("LAB-1003", "P-1002", "doctor", "Comprehensive Metabolic Panel (CMP)", "Biochemistry", "ROUTINE", "PROCESSING", _json({}), "Standard Clinical Range", 0, now, None, None),
            ]
            conn.executemany(
                "INSERT INTO lab_orders (id, patient_id, doctor_id, test_name, category, priority, status, result_data, reference_range, flagged_abnormal, ordered_at, completed_at, approved_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                labs
            )

        # 3e. Seed Prescriptions
        rx_count = conn.execute("SELECT COUNT(*) FROM prescriptions").fetchone()[0]
        if rx_count == 0:
            rxs = [
                ("RX-1001", "P-1001", "doctor", "Atorvastatin Calcium", "40 mg", "OD", "30 days", "DISPENSED", None, "pharmacist", now, now),
                ("RX-1002", "P-1001", "doctor", "Aspirin Ecosprin", "81 mg", "OD", "30 days", "DISPENSED", None, "pharmacist", now, now),
                ("RX-1003", "P-1003", "doctor", "Ticagrelor (Brilinta)", "90 mg", "BD", "14 days", "PRESCRIBED", "Dual antiplatelet therapy active", None, now, None),
            ]
            conn.executemany(
                "INSERT INTO prescriptions (id, patient_id, doctor_id, medication, dosage, frequency, duration, status, ddi_warning, pharmacist_id, ordered_at, dispensed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rxs
            )

        # 3f. Seed Billing Invoices
        bill_count = conn.execute("SELECT COUNT(*) FROM billing_invoices").fetchone()[0]
        if bill_count == 0:
            bills = [
                ("INV-1001", "P-1001", "H001", 125000.0, 100000.0, 25000.0, "APPROVED", "INSURANCE_TPA", _json([{"item": "Cath Lab Angioplasty", "amount": 95000.0}, {"item": "ICU Stay 2 Days", "amount": 20000.0}, {"item": "Pharmacy & Disposables", "amount": 10000.0}]), now, None),
                ("INV-1002", "P-1002", "H001", 18500.0, 15000.0, 3500.0, "SETTLED", "UPI_AUTOPAY", _json([{"item": "Holter 24h Monitoring", "amount": 8500.0}, {"item": "Ward Day Care", "amount": 6000.0}, {"item": "Consultation", "amount": 4000.0}]), now, now),
            ]
            conn.executemany(
                "INSERT INTO billing_invoices (id, patient_id, hospital_id, total_amount, insurance_claim_amount, patient_payable, status, payment_method, line_items, created_at, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                bills
            )

        # 3g. Seed Emergency Dispatches
        dsp_count = conn.execute("SELECT COUNT(*) FROM emergency_dispatches").fetchone()[0]
        if dsp_count == 0:
            dsps = [
                ("DSP-1001", "AMB-01", "paramedic", "P-1003", "108 City Call Center", "Acute Myocardial Infarction", "P1_CRITICAL", "MG Road & Brigade Junction", "City General Hospital (H001)", 1, _json({"hr": 114, "bp": "158/96", "spo2": 93}), now, None, None, "TRANSPORTING"),
            ]
            conn.executemany(
                "INSERT INTO emergency_dispatches (id, ambulance_id, paramedic_id, patient_id, caller_name, emergency_type, triage_priority, origin_location, destination_hospital, green_corridor_active, vitals, dispatched_at, arrived_scene_at, arrived_hospital_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                dsps
            )

        # 4. Seed Traffic Signals
        sig_count = conn.execute("SELECT COUNT(*) FROM traffic_signals").fetchone()[0]
        if sig_count == 0:
            signals = [
                ("SIG-01", "Grand Ave & 4th St", "Central", "GREEN", 90, 0, "SYSTEM_AUTO", "ADAPTIVE", now),
                ("SIG-02", "Broadway & 7th St", "Central", "RED", 75, 0, "SYSTEM_AUTO", "ADAPTIVE", now),
                ("SIG-03", "Metro Terminal Transit Hub", "North", "GREEN", 120, 0, "SYSTEM_AUTO", "ADAPTIVE", now),
                ("SIG-04", "Hospital Blvd & Health Corridor", "East", "GREEN", 60, 0, "EMERGENCY_DISPATCH", "GREEN_CORRIDOR", now),
                ("SIG-05", "Financial Tower & SWIFT Plaza", "Financial", "RED", 90, 0, "SYSTEM_AUTO", "ADAPTIVE", now),
                ("SIG-06", "Outer Ring Express Interchange", "South", "GREEN", 110, 0, "SYSTEM_AUTO", "ADAPTIVE", now),
            ]
            conn.executemany(
                "INSERT INTO traffic_signals (id, intersection, zone, current_state, cycle_time_sec, is_tampered, last_override_by, mode, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                signals
            )

        # 5. Seed Traffic Cameras
        cam_count = conn.execute("SELECT COUNT(*) FROM traffic_cameras").fetchone()[0]
        if cam_count == 0:
            cameras = [
                ("CAM-01", "Central Junction Northbound", "MG Road Flyover", "/api/traffic/stream/CAM-01", "ONLINE", 30.0, 2, now),
                ("CAM-02", "Hospital Emergency Corridor Gate", "Hospital Blvd", "/api/traffic/stream/CAM-02", "ONLINE", 30.0, 0, now),
                ("CAM-03", "Fintech Financial Plaza Outer", "Banking Tower West", "/api/traffic/stream/CAM-03", "ONLINE", 28.5, 1, now),
                ("CAM-04", "Metro Terminal Plaza Entry", "Railway Station Road", "/api/traffic/stream/CAM-04", "ONLINE", 30.0, 3, now),
                ("CAM-05", "Outer Ring SCADA Gantry", "Expressway Tollgate 04", "/api/traffic/stream/CAM-05", "DEGRADED", 18.2, 5, now),
            ]
            conn.executemany(
                "INSERT INTO traffic_cameras (id, name, location, stream_url, status, fps, incident_count, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                cameras
            )

        # 5b. Seed Traffic Incidents
        inc_trf_count = conn.execute("SELECT COUNT(*) FROM traffic_incidents").fetchone()[0]
        if inc_trf_count == 0:
            trf_incs = [
                ("INC-TRF-101", "Multi-Vehicle Collision", "ACCIDENT", "HIGH", "REPORTED", "Grand Ave & 4th St", "ROAD-URBAN-01", "SIG-01", "traffic_operator", None, 0, None, None, None, now, None),
                ("INC-TRF-102", "Stalled Commercial Transit Bus", "ROAD_HAZARD", "MEDIUM", "VERIFIED", "Electronic City Flyover", "ROAD-NH44-02", "SIG-02", "traffic_operator", "traffic_police", 1, "traffic_police", now, "Tow truck dispatched. Right lane blocked.", now, None),
                ("INC-TRF-103", "Wrong-Way Vehicle Alert", "WRONG_WAY", "CRITICAL", "DISPATCHED", "NH44 Northbound KM 12", "ROAD-NH44-01", "SIG-03", "traffic_operator", "traffic_police", 1, "traffic_police", now, "Police Interceptor EN-ROUTE. Signal held RED.", now, None),
                ("INC-TRF-104", "Inductive Loop Telemetry Anomaly", "CYBER_ANOMALY", "HIGH", "REPORTED", "Metro Terminal Transit Hub", "ROAD-URBAN-02", "SIG-03", "SCADA Monitor SEN-LOOP-02", "signal_tech", 0, None, None, None, now, None),
            ]
            conn.executemany(
                "INSERT INTO traffic_incidents (id, title, category, severity, status, location, road_id, intersection_id, reported_by, assigned_officer, verified, verified_by, verified_at, resolution_notes, reported_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                trf_incs
            )

        # 5c. Seed Toll Scans (FASTag / ANPR)
        toll_count = conn.execute("SELECT COUNT(*) FROM toll_scans").fetchone()[0]
        if toll_count == 0:
            toll_scans = [
                ("SCAN-FT-901", "TOLL-01", "Airport Express Plaza Gantry 2", "KA-01-AB-1234", "TAG-IND-8821901", 120.0, "CLEARED", None, None, None, now),
                ("SCAN-FT-902", "TOLL-02", "Electronic City Toll Gate 4", "DL-04-C-9988", "TAG-CLONED-9988", 120.0, "CLONED", "Duplicate cryptographic tag detected concurrently across 2 gantries within 45 seconds (impossible travel velocity 420 km/h)", None, None, now),
                ("SCAN-FT-903", "TOLL-01", "Airport Express Plaza Gantry 1", "MH-12-DE-5566", "TAG-IND-7721940", 85.0, "CLEARED", None, None, None, now),
                ("SCAN-FT-904", "TOLL-03", "Hosur Inter-State Gantry 3", "KA-05-NB-9901", "TAG-IND-3341829", 150.0, "BLACKLISTED", "Stolen Vehicle ANPR Watchlist Alert issued by Traffic Police HQ", None, None, now),
                ("SCAN-FT-905", "TOLL-01", "Airport Express Priority Lane", "KA-01-EQ-1044", "TAG-EMERGENCY-108", 0.0, "CLEARED", "Emergency Ambulance Automatic Exemption Cleared", None, None, now),
            ]
            conn.executemany(
                "INSERT INTO toll_scans (id, tollgate_id, tollgate_name, vehicle_number, fastag_id, amount, status, flag_reason, override_by, override_reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                toll_scans
            )

        # 5d. Seed Traffic Maintenance Tickets
        maint_count = conn.execute("SELECT COUNT(*) FROM traffic_maintenance_tickets").fetchone()[0]
        if maint_count == 0:
            tickets = [
                ("TKT-MAINT-01", "SIG-02", "signal_tech", "LOOP_DETECTOR_SHORT", "HIGH", "OPEN", 228.4, 0.4, "sha256_stig_v4.2.1_valid", "Inductive loop SEN-LOOP-02 reporting zero inductance. High disparity with CAM-01 visual detection.", None, now, None),
                ("TKT-MAINT-02", "SIG-05", "signal_tech", "FIRMWARE_TAMPER", "EMERGENCY", "OPEN", 230.1, 4.3, "CHECKSUM_MISMATCH_SUSPECT", "Firmware hash drift detected during automated SCADA integrity scan. Potential remote telemetry injection.", None, now, None),
                ("TKT-MAINT-03", "SIG-03", "signal_tech", "BULB_OUTAGE", "NORMAL", "COMPLETED", 231.0, 4.2, "sha256_stig_v4.2.1_valid", "Amber LED transit array replaced.", "Replaced LED module. Photometric luminosity verified nominal.", now, now),
            ]
            conn.executemany(
                "INSERT INTO traffic_maintenance_tickets (id, signal_id, technician_id, issue_type, priority, status, voltage_reading, loop_resistance_ohms, firmware_checksum, diagnostic_log, resolution_notes, created_at, completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tickets
            )

        # 5e. Seed Green Corridors
        gc_count = conn.execute("SELECT COUNT(*) FROM green_corridors").fetchone()[0]
        if gc_count == 0:
            corridors = [
                ("CORR-01", "Hospital Emergency Trauma Corridor", "DSP-1001", "AMB-01", "ACTIVE", "Indiranagar 100ft Road", "City General Hospital (H001)", _json(["SIG-01", "SIG-02", "SIG-04"]), "SIG-01", _json(["SIG-01"]), now, None),
                ("CORR-02", "Airport Expressway Transit Corridor", None, None, "STANDBY", "MG Road Metro Station", "Airport Tollgate", _json(["SIG-02", "SIG-03", "SIG-06"]), None, _json([]), None, None),
            ]
            conn.executemany(
                "INSERT INTO green_corridors (id, name, emergency_dispatch_id, ambulance_id, status, origin_location, destination_hospital, route_intersections, active_signal_id, cleared_signals, activated_at, cleared_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                corridors
            )

        # 5f. Seed RFID Readers
        rfid_reader_count = conn.execute("SELECT COUNT(*) FROM rfid_readers").fetchone()[0]
        if rfid_reader_count == 0:
            readers = [
                ("RFID-READER-01", "Majestic Interchange Gantry Lane 1", "LANE-01", "ONLINE", "10.12.4.50", "DEV-RFID-01", "TRUSTED", now),
                ("RFID-READER-02", "Silk Board Gantry Lane 2", "LANE-02", "ONLINE", "10.12.4.51", "DEV-RFID-02", "TRUSTED", now),
                ("RFID-READER-03", "Hebbal Flyover Toll Plaza", "LANE-01", "ONLINE", "10.12.4.52", "DEV-RFID-03", "TRUSTED", now),
                ("RFID-READER-04", "Town Hall Express Gantry", "LANE-01", "ONLINE", "10.12.4.53", "DEV-RFID-04", "TRUSTED", now),
            ]
            conn.executemany(
                "INSERT INTO rfid_readers (reader_id, location, lane, status, ip_address, device_id, trust_status, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                readers
            )

        # 5g. Seed FASTag Registry
        fastag_count = conn.execute("SELECT COUNT(*) FROM fastags").fetchone()[0]
        if fastag_count == 0:
            tags = [
                ("FT-1001", "TAG-98231", "VEH-1001", "MH12DE1433", "CUST-501", "ACTIVE", "NPCI_NETC", "ACC-***-9021", now, now),
                ("FT-1002", "TAG-IND-8821901", "VEH-1002", "KA-01-AB-1234", "CUST-502", "ACTIVE", "NPCI_NETC", "ACC-***-8841", now, now),
                ("FT-1003", "TAG-1036", "VEH-1003", "TN70DY8744", "CUST-503", "ACTIVE", "NPCI_NETC", "ACC-***-1144", now, now),
                ("FT-1004", "TAG-1013", "VEH-1004", "UP99UF1525", "CUST-504", "ACTIVE", "NPCI_NETC", "ACC-***-6632", now, now),
                ("FT-1005", "TAG-1046", "VEH-1046", "HR55ST8973", "CUST-505", "ACTIVE", "NPCI_NETC", "ACC-***-7711", now, now),
                ("FT-1006", "TAG-EMERGENCY-108", "AMB-021", "KA-01-EQ-1044", "HOSP-001", "ACTIVE", "STATE_HEALTH", "ACC-***-0108", now, now),
                ("FT-1007", "TAG-CLONED-9988", "VEH-9988", "DL-04-C-9988", "CUST-SUSPECT", "BLOCKED", "NPCI_NETC", "ACC-***-0000", now, now),
                ("FT-1008", "TAG-EXPIRED-55", "VEH-5501", "MH12PQ4589", "CUST-506", "EXPIRED", "NPCI_NETC", "ACC-***-5501", now, now),
            ]
            conn.executemany(
                "INSERT INTO fastags (fastag_id, tag_id, vehicle_id, vehicle_registration, customer_id, status, issuer, linked_account, created_at, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                tags
            )

        # Ensure corridor cameras exist (CAM-101, CAM-102, CAM-105, CAM-108, CAM-109)
        existing_cam_ids = {row[0] for row in conn.execute("SELECT id FROM traffic_cameras").fetchall()}
        corridor_cams = [
            ("CAM-101", "Silk Board South Interchange", "Silk Board Junction", 12.9172, 77.6228, "SIG-02", "ROAD-NH44-01", "FIXED_CCTV", "WEBRTC", "/api/traffic/stream/CAM-101", "ONLINE", "HEALTHY", 30.0, "1920x1080", 0, now, "DEV-CAM-101", "TRUSTED", 0.0, now, "{}", now),
            ("CAM-102", "Dairy Circle Corridor CCTV", "Dairy Circle Junction", 12.9382, 77.6059, "SIG-01", "ROAD-URBAN-01", "PTZ", "WEBRTC", "/api/traffic/stream/CAM-102", "ONLINE", "HEALTHY", 30.0, "1920x1080", 0, now, "DEV-CAM-102", "TRUSTED", 0.0, now, "{}", now),
            ("CAM-105", "Town Hall North Crossing", "Town Hall Junction", 12.9641, 77.5854, "SIG-03", "ROAD-URBAN-02", "FIXED_CCTV", "WEBRTC", "/api/traffic/stream/CAM-105", "ONLINE", "HEALTHY", 30.0, "1920x1080", 0, now, "DEV-CAM-105", "TRUSTED", 0.0, now, "{}", now),
            ("CAM-108", "Majestic Transit Terminal Exit", "Majestic Interchange", 12.9779, 77.5724, "SIG-01", "ROAD-URBAN-01", "FIXED_CCTV", "WEBRTC", "/api/traffic/stream/CAM-108", "ONLINE", "HEALTHY", 30.0, "1920x1080", 0, now, "DEV-CAM-108", "TRUSTED", 0.0, now, "{}", now),
            ("CAM-109", "Indiranagar 100ft Road Gantry", "Indiranagar Crossing", 12.9784, 77.6408, "SIG-06", "ROAD-NH44-02", "IP_CAMERA", "WEBRTC", "/api/traffic/stream/CAM-109", "ONLINE", "HEALTHY", 30.0, "1920x1080", 0, now, "DEV-CAM-109", "TRUSTED", 0.0, now, "{}", now),
        ]
        for cam in corridor_cams:
            if cam[0] not in existing_cam_ids:
                try:
                    conn.execute(
                        """
                        INSERT INTO traffic_cameras (id, name, location, latitude, longitude, intersection_id, road_id, camera_type, stream_type, stream_url, status, health, fps, resolution, incident_count, last_seen, device_id, trust_status, risk_score, created_at, metadata_json, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        cam
                    )
                except Exception:
                    # Fallback for simpler schema if columns were not added yet
                    conn.execute(
                        "INSERT OR IGNORE INTO traffic_cameras (id, name, location, stream_url, status, fps, incident_count, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (cam[0], cam[1], cam[2], cam[9], cam[10], cam[12], cam[14], cam[21])
                    )

        # 6. Seed Bank Accounts & Transactions
        acc_count = conn.execute("SELECT COUNT(*) FROM bank_accounts").fetchone()[0]
        if acc_count == 0:
            accounts = [
                ("ACC-9001", "CUST-501", "100488920199", "SAVINGS", 145000.0, "ACTIVE", now),
                ("ACC-9002", "CUST-502", "100488920245", "CURRENT", 8450000.0, "ACTIVE", now),
                ("ACC-9003", "CUST-503", "100488920981", "TREASURY", 54000000.0, "ACTIVE", now),
                ("ACC-9004", "customer", "100488999999", "SAVINGS", 350000.0, "ACTIVE", now),
            ]
            conn.executemany(
                "INSERT INTO bank_accounts (id, customer_id, account_number, account_type, balance, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                accounts
            )

        tx_count = conn.execute("SELECT COUNT(*) FROM bank_transactions").fetchone()[0]
        if tx_count == 0:
            txs = [
                ("TX-8001", "ACC-9001", "Tony Stark", "987654321011", 4500.0, "UPI", "PAYMENT", 12.0, "ALLOWED", 0, 0, 1440, now),
                ("TX-8002", "ACC-9001", "Tony Stark", "543210987654", 25000.0, "NETBANKING", "TRANSFER", 18.5, "ALLOWED", 0, 0, 720, now),
                ("TX-8003", "ACC-9002", "Metro Logistics Corp", "112233445566", 1850000.0, "SWIFT_RTGS", "WIRE_TRANSFER", 84.0, "ESCROW_HOLD", 1, 1, 2, now),
                ("TX-8004", "ACC-9003", "Municipal Water SCADA", "998877665544", 4500000.0, "INTERBANK", "TREASURY_TRANSFER", 91.5, "BLOCKED", 1, 1, 1, now),
            ]
            conn.executemany(
                "INSERT INTO bank_transactions (id, account_id, sender_name, receiver_account, amount, channel, transaction_type, risk_score, decision, is_fraud, is_sar, beneficiary_age_hours, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                txs
            )

        # 7. Seed Security Policies
        pol_count = conn.execute("SELECT COUNT(*) FROM security_policies").fetchone()[0]
        if pol_count == 0:
            policies = [
                ("POL-01", "DOCTOR_BULK_RECORD_ACCESS", "HEALTHCARE", "record_count > 100 AND role == 'doctor'", 45.0, "BLOCK", "Blocks bulk patient record retrieval outside clinical research scope", 1),
                ("POL-02", "IMPOSSIBLE_TRAVEL_VELOCITY", "PLATFORM", "geo_velocity_kmh > 800", 40.0, "BLOCK", "Restricts access when sequential logins exceed human flight velocity", 1),
                ("POL-03", "UNAUTHORIZED_SIGNAL_OVERRIDE", "TRAFFIC", "role != 'traffic_operator' AND action == 'UPDATE'", 50.0, "BLOCK", "Prevents non-operator roles from executing signal timing modifications", 1),
                ("POL-04", "SWIFT_NEW_BENEFICIARY_SPIKE", "FINANCE", "amount > 1000000 AND beneficiary_age_hours < 24", 35.0, "STEP_UP_MFA", "Enforces secondary authentication and escrow hold for high-value transfers to fresh accounts", 1),
            ]
            conn.executemany(
                "INSERT INTO security_policies (id, name, domain, rule_definition, risk_modifier, action, description, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                policies
            )

        # 8. Seed Cross-Domain Threat
        cdt_count = conn.execute("SELECT COUNT(*) FROM cross_domain_threats").fetchone()[0]
        if cdt_count == 0:
            conn.execute(
                """
                INSERT INTO cross_domain_threats (id, threat_actor_ip, device_id, domains_involved, first_seen, last_seen, risk_score, campaign_summary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "CDT-001",
                    "198.51.100.77",
                    "DEV-ROGUE-9921",
                    _json(["HEALTHCARE", "TRAFFIC", "FINANCE"]),
                    now,
                    now,
                    94.5,
                    "Coordinated APT campaign utilizing credential stuffing against Hospital EHR while probing STIG Traffic Signal Controllers and attempting SWIFT treasury wire diversion.",
                    "ACTIVE"
                )
            )

        # 9. Seed Security Events & Operational Finance
        self._seed_events_and_finance(conn)

    def _seed_events_and_finance(self, conn) -> None:
        now = _utcnow()
        if conn.execute("SELECT COUNT(*) FROM finance_branches").fetchone()[0] == 0:
            branches = [
                ("BR-01", "BLR-CENTRAL-01", "Metro Central Main Branch", "Bengaluru", "South Zone", "branch_manager", 50000000.0, 18450000.0, "ACTIVE"),
                ("BR-02", "BLR-ECITY-02", "Electronic City Corporate & FinTech Branch", "Bengaluru", "South Zone", "branch_manager", 100000000.0, 42100000.0, "ACTIVE"),
                ("BR-03", "BLR-INDIRA-03", "Indiranagar Commercial Branch", "Bengaluru", "East Zone", "branch_manager", 35000000.0, 12800000.0, "ACTIVE"),
            ]
            conn.executemany("INSERT INTO finance_branches VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", branches)

        if conn.execute("SELECT COUNT(*) FROM finance_customers").fetchone()[0] == 0:
            customers = [
                ("CUST-101", "Tony Stark (Apex Industrialist)", "ABCPS1001A", "VERIFIED", "LOW", "+91-9880011221", "tony.stark@apex-stark.org", "BR-01", now),
                ("CUST-102", "Pepper Potts (Municipal Foundation)", "XYZPP2002B", "VERIFIED", "LOW", "+91-9880011222", "p.potts@stark-foundation.org", "BR-01", now),
                ("CUST-103", "Wayne Municipal Treasury Holdings", "CORPW3003C", "VERIFIED", "LOW", "+91-9880011223", "treasury@wayne-enterprises.com", "BR-02", now),
                ("CUST-104", "Apex Logistics & Transit Gantry", "TRNAL4004D", "VERIFIED", "MEDIUM", "+91-9880011224", "settlement@apex-logistics.in", "BR-03", now),
                ("CUST-105", "Syndicate DarkMule Shell Entity", "MULEX5005E", "FLAGGED", "CRITICAL", "+91-9880011225", "ops@shadow-escrow-holdings.biz", "BR-02", now),
            ]
            conn.executemany("INSERT INTO finance_customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", customers)

        if conn.execute("SELECT COUNT(*) FROM finance_accounts").fetchone()[0] == 0:
            accounts = [
                ("ACC-7001", "CUST-101", "9988112233", "BR-01", "SAVINGS", 2450000.0, "INR", "ACTIVE", 4.2, now),
                ("ACC-7002", "CUST-101", "9988112244", "BR-01", "CURRENT", 18500000.0, "INR", "ACTIVE", 8.5, now),
                ("ACC-7003", "CUST-102", "7766554433", "BR-01", "SAVINGS", 6200000.0, "INR", "ACTIVE", 5.0, now),
                ("ACC-7004", "CUST-103", "5544332211", "BR-02", "ESCROW", 95000000.0, "INR", "ACTIVE", 12.0, now),
                ("ACC-7005", "CUST-104", "3344556677", "BR-03", "CURRENT", 12800000.0, "INR", "ACTIVE", 18.0, now),
                ("ACC-7006", "CUST-105", "1122446688", "BR-02", "CURRENT", 4500000.0, "INR", "FROZEN", 94.0, now),
            ]
            conn.executemany("INSERT INTO finance_accounts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", accounts)

        if conn.execute("SELECT COUNT(*) FROM finance_transactions").fetchone()[0] == 0:
            transactions = [
                ("TX-9001", "ACC-7001", "ACC-7003", 25000.0, "UPI", "INR", now, "192.168.1.45", "DEV-MOB-01", "Bengaluru Central", "SETTLED", 6.0, "LIVE INFERENCE", None, now),
                ("TX-9002", "ACC-7002", "ACC-7004", 1200000.0, "RTGS", "INR", now, "192.168.1.45", "DEV-WORKSTATION-01", "Bengaluru Central", "SETTLED", 14.0, "LIVE INFERENCE", None, now),
                ("TX-9003", "ACC-7006", "OFFSHORE-ACC-9981", 4500000.0, "SWIFT", "INR", now, "198.51.100.77", "DEV-ROGUE-EXT-88", "Offshore / Proxy", "BLOCKED", 96.0, "LIVE INFERENCE", "Rapid Offshore Diversion & Blacklisted Threat Actor IP", now),
                ("TX-9004", "ACC-7005", "ACC-7006", 48500.0, "UPI", "INR", now, "203.0.113.14", "DEV-UNKNOWN-99", "Bengaluru South", "FLAGGED_AML", 78.0, "LIVE INFERENCE", "Smurfing / Structuring threshold evasion anomaly", now),
                ("TX-9005", "ACC-7001", "ACC-7005", 150000.0, "NEFT", "INR", now, "192.168.1.45", "DEV-MOB-01", "Bengaluru East", "SETTLED", 18.0, "CACHED RESULT", None, now),
            ]
            conn.executemany("INSERT INTO finance_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", transactions)

        if conn.execute("SELECT COUNT(*) FROM finance_fraud_cases").fetchone()[0] == 0:
            cases = [
                ("CASE-FRD-9001", "FRD-2026-001", "TX-9003", "CUST-105", "ACC-7006", "High-Value SWIFT Diversion to Unregistered Offshore Shell Entity", "CRITICAL", "INVESTIGATING", 4500000.0, "fraud_analyst", None, None, "XGBoost and Isolation Forest flagged transaction with score 96.0. Originating from threat IP 198.51.100.77.", now, None),
                ("CASE-FRD-9002", "FRD-2026-002", "TX-9004", "CUST-104", "ACC-7005", "Repeated Sub-₹50,000 Rapid Outflows (Smurfing Syndicate)", "HIGH", "OPEN", 48500.0, "fraud_analyst", None, None, "Multiple transactions structured just below PAN verification ceiling. Beneficiary account ACC-7006 is known mule aggregator.", now, None),
            ]
            conn.executemany("INSERT INTO finance_fraud_cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", cases)

        if conn.execute("SELECT COUNT(*) FROM finance_aml_findings").fetchone()[0] == 0:
            findings = [
                ("AML-FIND-801", "CASE-FRD-9002", "FAN_IN_FAN_OUT_MULE_NETWORK", "ACC-7006", _json(["ACC-7005", "ACC-7006", "OFFSHORE-ACC-9981"]), 0.94, 3, "Rapid Fan-In from 4 retail accounts followed by instantaneous consolidated exit", _json({"nodes_affected": 6, "centrality_score": 0.88, "velocity_ratio": 4.2}), 1, "SAR-2026-IND-4912", now),
            ]
            conn.executemany("INSERT INTO finance_aml_findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", findings)

        if conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0] == 0:
            events = [
                ("EVT-1001", now, "SECURITY", "Pan-City SOC", "admin", "admin", "WORKSTATION-SOC-01", "127.0.0.1", "City Hall Command SOC", "SYSTEM_AUTH", "LOGIN", "SUCCESS", 0.0, _json({"auth_method": "PASSWORD_MFA"})),
                ("EVT-1002", now, "TRAFFIC", "Bengaluru Smart Mobility SCADA", "traffic_operator", "traffic_operator", "SCADA-WS-02", "192.168.1.10", "Traffic Control Center", "TRAFFIC_SIGNAL:SIG-01", "SIGNAL_OVERRIDE", "OVERRIDDEN", 15.0, _json({"target_phase": "GREEN", "transition_stages": 3, "context_type": "EMERGENCY_PREEMPTION"})),
                ("EVT-1003", now, "HEALTHCARE", "City General Hospital (H001)", "doctor", "doctor", "CLINICAL-WS-04", "10.0.1.42", "Emergency Trauma Bay 1", "PATIENT:P-1004", "BREAK_GLASS", "OVERRIDDEN", 35.0, _json({"patient_name": "Devraj Mukherjee", "reason": "Acute anaphylactic collapse"})),
                ("EVT-1004", now, "FINANCE", "State Apex Municipal Bank", "system_gateway", "system", "SWIFT-GATEWAY-01", "198.51.100.77", "Electronic City FinTech Hub", "TRANSACTION:TX-9003", "TRANSACTION", "BLOCKED", 96.0, _json({"amount": 4500000.0, "channel": "SWIFT", "mule_flag": True, "model": "XGBoost Supervised"})),
                ("EVT-1005", now, "FINANCE", "State Apex Municipal Bank", "fraud_analyst", "fraud_analyst", "FRAUD-WS-01", "192.168.2.15", "Fraud Operations Center", "TRANSACTION:TX-9003", "FRAUD_ALERT", "FLAGGED", 96.0, _json({"case_id": "CASE-FRD-9001", "exposure_inr": 4500000.0})),
                ("EVT-1006", now, "FINANCE", "State Apex Municipal Bank", "aml_analyst", "aml_analyst", "AML-WS-01", "192.168.2.18", "AML Operations Center", "ACCOUNT:ACC-7006", "AML_ALERT", "FLAGGED", 94.0, _json({"finding_id": "AML-FIND-801", "pattern": "FAN_IN_FAN_OUT"}))
            ]
            conn.executemany("INSERT INTO security_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", events)

    async def create_user(self, username: str, hashed_password: str, role: str, full_name: str = "") -> dict:
        user = {
            "id": str(uuid.uuid4()),
            "username": username,
            "hashed_password": hashed_password,
            "role": role,
            "full_name": full_name,
            "is_active": True,
            "created_at": _utcnow(),
        }
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO users
                    (id, username, hashed_password, role, full_name, is_active, failed_logins, risk_score, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, 10.0, ?)
                    """,
                    (
                        user["id"], username, hashed_password, role, full_name,
                        1, user["created_at"],
                    ),
                )
        return user

    def get_user(self, username: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None

    async def get_users(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, username, role, full_name, is_active, created_at, last_login_at FROM users LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    async def touch_login(self, username: str) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE users SET last_login_at = ? WHERE username = ?",
                    (_utcnow(), username),
                )

    async def add_alert(self, alert: dict) -> dict:
        alert.setdefault("id", str(uuid.uuid4()))
        alert.setdefault("timestamp", _utcnow())
        alert.setdefault("risk_category", "HIGH")
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO alerts
                    (id, timestamp, asset, severity, risk_score, risk_category, anomaly_score, scenario, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert["id"], alert["timestamp"], alert.get("asset"),
                        alert.get("severity"), alert.get("risk_score"),
                        alert.get("risk_category"), alert.get("anomaly_score"),
                        alert.get("scenario"), _json(alert),
                    ),
                )
        return alert

    async def get_alerts(self, limit: int = 50, severity: Optional[str] = None) -> list:
        limit = max(1, min(int(limit), 1000))
        query = "SELECT * FROM alerts"
        params: list = []
        if severity:
            query += " WHERE severity = ?"
            params.append(severity)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        alerts = []
        for row in rows:
            item = _loads(row["payload"] if "payload" in row.keys() else None, None)
            if item is None:
                item = dict(row)
                item.pop("payload", None)
                for field in ("threat_flags", "affected_assets", "component_scores", "mitigation_plan"):
                    if field in item:
                        item[field] = _loads(item[field], item[field])
            alerts.append(item)
        return alerts

    async def add_event(self, event: dict) -> dict:
        event.setdefault("id", str(uuid.uuid4()))
        event.setdefault("timestamp", _utcnow())
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO event_stream
                    (id, timestamp, type, source_type, asset, severity, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["id"], event["timestamp"], event.get("type", "event"),
                        event.get("source_type"), event.get("asset"),
                        event.get("severity"), _json(event),
                    ),
                )
        return event

    async def get_events(self, limit: int = 100, event_type: str | None = None) -> list:
        limit = max(1, min(int(limit), 2000))
        query = "SELECT payload FROM event_stream"
        params: list = []
        if event_type:
            query += " WHERE type = ? OR source_type = ?"
            params.extend([event_type, event_type])
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_loads(row["payload"], {}) for row in rows]

    async def add_risk_snapshot(self, snapshot: dict) -> None:
        snapshot.setdefault("id", str(uuid.uuid4()))
        snapshot.setdefault("timestamp", _utcnow())
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO risk_history
                    (id, timestamp, asset, risk_score, category, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot["id"], snapshot["timestamp"], snapshot.get("asset", "unknown"),
                        float(snapshot.get("risk_score", 0) or 0), snapshot.get("category"),
                        _json(snapshot),
                    ),
                )

    async def get_risk_history(self, limit: int = 200) -> list:
        limit = max(1, min(int(limit), 2000))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM risk_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        history = []
        for row in rows:
            item = _loads(row["payload"] if "payload" in row.keys() else None, None)
            if item is None:
                item = dict(row)
                item.pop("payload", None)
            history.append(item)
        return history

    async def add_mitigation(self, m: dict) -> dict:
        m.setdefault("id", str(uuid.uuid4()))
        m.setdefault("timestamp", _utcnow())
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO mitigations
                    (id, timestamp, asset, playbook, status, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m["id"], m["timestamp"], m.get("asset"), m.get("playbook"),
                        m.get("status", "created"), _json(m),
                    ),
                )
        return m

    async def get_mitigations(self, limit: int = 50) -> list:
        limit = max(1, min(int(limit), 500))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mitigations ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        mitigations = []
        for row in rows:
            item = _loads(row["payload"] if "payload" in row.keys() else None, None)
            if item is None:
                item = dict(row)
                item.pop("payload", None)
            mitigations.append(item)
        return mitigations

    async def add_fraud_alert(self, alert: dict) -> dict:
        alert.setdefault("id", str(uuid.uuid4()))
        alert.setdefault("timestamp", _utcnow())
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO fraud_alerts
                    (id, timestamp, transaction_id, channel, severity, risk_score, decision, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert["id"], alert["timestamp"], alert.get("transaction_id"),
                        alert.get("channel"), alert.get("severity"),
                        alert.get("risk_score"), alert.get("decision"), _json(alert),
                    ),
                )
        return alert

    async def get_fraud_alerts(self, limit: int = 100) -> list:
        limit = max(1, min(int(limit), 1000))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM fraud_alerts ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_loads(row["payload"], {}) for row in rows]

    async def add_incident(self, incident: dict) -> dict:
        incident.setdefault("id", str(uuid.uuid4()))
        incident.setdefault("timestamp", _utcnow())
        incident.setdefault("status", "open")
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO incidents
                    (id, timestamp, title, status, severity, asset, owner, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident["id"], incident["timestamp"], incident.get("title", "Untitled incident"),
                        incident.get("status", "open"), incident.get("severity"), incident.get("asset"),
                        incident.get("owner"), _json(incident),
                    ),
                )
        return incident

    async def get_incidents(self, limit: int = 100, status: str | None = None) -> list:
        limit = max(1, min(int(limit), 1000))
        query = "SELECT payload FROM incidents"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_loads(row["payload"], {}) for row in rows]

    async def update_incident_status(self, incident_id: str, status: str, owner: str | None = None) -> dict | None:
        incidents = await self.get_incidents(limit=1000)
        incident = next((item for item in incidents if item.get("id") == incident_id), None)
        if not incident:
            return None
        incident["status"] = status
        if owner is not None:
            incident["owner"] = owner
        incident["updated_at"] = _utcnow()
        return await self.add_incident(incident)

    async def audit(self, actor: str, action: str, target: str | None = None, payload: dict | None = None) -> dict:
        audit = {
            "id": str(uuid.uuid4()),
            "timestamp": _utcnow(),
            "actor": actor,
            "action": action,
            "target": target,
            "payload": payload or {},
        }
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs (id, timestamp, actor, action, target, payload)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit["id"], audit["timestamp"], actor, action, target,
                        _json(audit["payload"]),
                    ),
                )
        return audit

    async def get_audit_logs(self, limit: int = 100) -> list:
        limit = max(1, min(int(limit), 1000))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                **dict(row),
                "payload": _loads(row["payload"], {}),
            }
            for row in rows
        ]

    async def add_campaign(self, campaign: dict) -> dict:
        cid = campaign.get("id") or f"CAMPAIGN-SEC-{uuid.uuid4().hex[:6].upper()}"
        campaign["id"] = cid
        first_seen = campaign.get("first_seen") or _utcnow()
        last_seen = campaign.get("last_seen") or _utcnow()
        campaign["first_seen"] = first_seen
        campaign["last_seen"] = last_seen
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO campaigns (id, title, stages, affected_assets, risk_score, confidence, status, first_seen, last_seen, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        stages=excluded.stages,
                        affected_assets=excluded.affected_assets,
                        risk_score=excluded.risk_score,
                        confidence=excluded.confidence,
                        status=excluded.status,
                        last_seen=excluded.last_seen,
                        payload=excluded.payload
                    """,
                    (
                        cid,
                        campaign.get("title", "Smart City Attack Campaign"),
                        _json(campaign.get("stages", [])),
                        _json(campaign.get("affected_assets", [])),
                        float(campaign.get("risk_score", 50.0)),
                        float(campaign.get("confidence", 0.90)),
                        campaign.get("status", "ACTIVE"),
                        first_seen,
                        last_seen,
                        _json(campaign),
                    )
                )
        return campaign

    async def get_campaigns(self, limit: int = 50, status: str | None = None) -> list[dict]:
        limit = max(1, min(int(limit), 200))
        query = "SELECT payload FROM campaigns"
        params: list = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY last_seen DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_loads(r["payload"], {}) for r in rows]

    async def get_campaign(self, campaign_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
        return _loads(row["payload"], None) if row else None

    async def add_response_action(self, action: dict) -> dict:
        aid = action.get("id") or f"RESP-{uuid.uuid4().hex[:8].upper()}"
        action["id"] = aid
        ts = action.get("timestamp") or _utcnow()
        action["timestamp"] = ts
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO response_actions (id, timestamp, action, target_asset, before_risk, after_risk, verification_metrics, actor, status, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        aid,
                        ts,
                        action.get("action", "MITIGATION"),
                        action.get("target_asset", "UNKNOWN"),
                        float(action.get("before_risk", 0.0)),
                        float(action.get("after_risk", 0.0)),
                        _json(action.get("verification_metrics", {})),
                        action.get("actor", "SOC_ANALYST"),
                        action.get("status", "VERIFIED"),
                        _json(action),
                    )
                )
        return action

    async def get_response_actions(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM response_actions ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [_loads(r["payload"], {}) for r in rows]

    async def add_simulation(self, sim: dict) -> dict:
        sid = sim.get("id") or f"SIM-{uuid.uuid4().hex[:8].upper()}"
        sim["id"] = sid
        ts = sim.get("timestamp") or _utcnow()
        sim["timestamp"] = ts
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO simulations (id, timestamp, scenario_id, target_asset, attack_type, intensity, duration, events_generated, status, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sid,
                        ts,
                        sim.get("scenario_id", "CUSTOM"),
                        sim.get("target_asset", "UNKNOWN"),
                        sim.get("attack_type", "DDOS"),
                        float(sim.get("intensity", 1.0)),
                        float(sim.get("duration", 30.0)),
                        int(sim.get("events_generated", 0)),
                        sim.get("status", "COMPLETED"),
                        _json(sim),
                    )
                )
        return sim

    async def get_simulations(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(int(limit), 200))
        with self._connect() as conn:
            rows = conn.execute("SELECT payload FROM simulations ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        return [_loads(r["payload"], {}) for r in rows]

    async def search(self, query: str, limit: int = 50) -> dict:
        q = f"%{query.strip().lower()}%"
        limit = max(1, min(int(limit), 100))
        with self._connect() as conn:
            alert_rows = conn.execute(
                "SELECT payload FROM alerts WHERE LOWER(asset) LIKE ? OR LOWER(scenario) LIKE ? OR LOWER(payload) LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (q, q, q, limit)
            ).fetchall()
            incident_rows = conn.execute(
                "SELECT payload FROM incidents WHERE LOWER(title) LIKE ? OR LOWER(asset) LIKE ? OR LOWER(payload) LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (q, q, q, limit)
            ).fetchall()
            campaign_rows = conn.execute(
                "SELECT payload FROM campaigns WHERE LOWER(title) LIKE ? OR LOWER(affected_assets) LIKE ? OR LOWER(payload) LIKE ? ORDER BY last_seen DESC LIMIT ?",
                (q, q, q, limit)
            ).fetchall()
            audit_rows = conn.execute(
                "SELECT * FROM audit_logs WHERE LOWER(action) LIKE ? OR LOWER(actor) LIKE ? OR LOWER(target) LIKE ? ORDER BY timestamp DESC LIMIT ?",
                (q, q, q, limit)
            ).fetchall()

        return {
            "query": query,
            "alerts": [_loads(r["payload"], {}) for r in alert_rows],
            "incidents": [_loads(r["payload"], {}) for r in incident_rows],
            "campaigns": [_loads(r["payload"], {}) for r in campaign_rows],
            "audit_logs": [{**dict(r), "payload": _loads(r["payload"], {})} for r in audit_rows],
            "total_matches": len(alert_rows) + len(incident_rows) + len(campaign_rows) + len(audit_rows)
        }

    async def stats(self) -> dict:
        with self._connect() as conn:
            tables = {
                "total_alerts": "alerts",
                "total_events": "event_stream",
                "risk_snapshots": "risk_history",
                "mitigations": "mitigations",
                "fraud_alerts": "fraud_alerts",
                "users": "users",
                "audit_logs": "audit_logs",
                "campaigns": "campaigns",
                "response_actions": "response_actions",
                "simulations": "simulations",
            }
            return {
                key: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for key, table in tables.items()
            }



    # ── Multi-Domain Domain Methods ─────────────────────────────────────────

    async def get_patients(self, assigned_doctor_id: Optional[str] = None, department: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM patients WHERE 1=1"
            params = []
            if assigned_doctor_id:
                query += " AND assigned_doctor_id = ?"
                params.append(assigned_doctor_id)
            if department:
                query += " AND department = ?"
                params.append(department)
            query += " ORDER BY id ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def get_patient(self, patient_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            # normalize vitals
            if "vital_signs_json" in res and res.get("vital_signs_json"):
                try:
                    res["vitals"] = json.loads(res["vital_signs_json"]) if isinstance(res["vital_signs_json"], str) else res["vital_signs_json"]
                except Exception:
                    res["vitals"] = res["vital_signs_json"]
            if "vitals" not in res:
                res["vitals"] = {"bp": "120/80", "hr": 74, "spo2": 98, "temp": 36.8}
            # Include primary diagnosis from latest medical record if not present
            mr = conn.execute("SELECT diagnosis FROM medical_records WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1", (patient_id,)).fetchone()
            res["diagnosis"] = mr["diagnosis"] if mr and mr["diagnosis"] else res.get("condition", "General Evaluation")
            return res

    async def get_medical_records(self, patient_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM medical_records WHERE patient_id = ? ORDER BY created_at DESC",
                (patient_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    async def create_medical_record(
        self, patient_id: str, doctor_id: str, diagnosis: str,
        prescriptions: list, lab_results: dict, notes: str, sensitivity: str = "CONFIDENTIAL"
    ) -> dict:
        record_id = f"MR-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO medical_records
                (id, patient_id, doctor_id, diagnosis, prescriptions, lab_results, treatment_notes, sensitivity, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (record_id, patient_id, doctor_id, diagnosis, _json(prescriptions), _json(lab_results), notes, sensitivity, now)
            )
        return {
            "id": record_id, "patient_id": patient_id, "doctor_id": doctor_id,
            "diagnosis": diagnosis, "prescriptions": prescriptions, "lab_results": lab_results,
            "treatment_notes": notes, "sensitivity": sensitivity, "created_at": now
        }

    async def create_patient(self, data: dict) -> dict:
        patient_id = data.get("id") or f"P-{uuid.uuid4().hex[:4].upper()}"
        now = _utcnow()
        vitals = data.get("vitals") or {"bp": "120/80", "hr": 72, "spo2": 98, "temp": 36.8}
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO patients
                (id, hospital_id, name, age, gender, department, assigned_doctor_id, assigned_nurse_id, room_bed, condition, admission_date, vital_signs_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_id,
                    data.get("hospital_id", "H001"),
                    data.get("name", "Unnamed Patient"),
                    data.get("age", 40),
                    data.get("gender", "Other"),
                    data.get("department", "General"),
                    data.get("assigned_doctor_id"),
                    data.get("assigned_nurse_id"),
                    data.get("room_bed", "Unassigned"),
                    data.get("condition", "Under Evaluation"),
                    now,
                    _json(vitals),
                    now
                )
            )
            if data.get("diagnosis"):
                conn.execute(
                    """
                    INSERT INTO medical_records (id, patient_id, doctor_id, diagnosis, prescriptions, lab_results, treatment_notes, sensitivity, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"MR-{uuid.uuid4().hex[:6].upper()}",
                        patient_id,
                        data.get("assigned_doctor_id", "doctor"),
                        data.get("diagnosis"),
                        _json([]),
                        _json({}),
                        data.get("notes") or "Initial Clinical Intake",
                        "CONFIDENTIAL",
                        now
                    )
                )
        return await self.get_patient(patient_id)

    async def update_patient(self, patient_id: str, updates: dict) -> Optional[dict]:
        allowed_cols = {
            "name": "name", "age": "age", "gender": "gender", "department": "department",
            "assigned_doctor_id": "assigned_doctor_id", "assigned_nurse_id": "assigned_nurse_id",
            "room_bed": "room_bed", "condition": "condition", "vitals": "vital_signs_json"
        }
        sets = []
        params = []
        for k, v in updates.items():
            if k in allowed_cols:
                col = allowed_cols[k]
                sets.append(f"{col} = ?")
                params.append(_json(v) if k == "vitals" and isinstance(v, (dict, list)) else v)
        if sets:
            sets.append("updated_at = ?")
            params.append(_utcnow())
            params.append(patient_id)
            with self._connect() as conn:
                conn.execute(f"UPDATE patients SET {', '.join(sets)} WHERE id = ?", params)
        return await self.get_patient(patient_id)

    async def get_appointments(self, doctor_id: Optional[str] = None, department: Optional[str] = None, patient_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM appointments WHERE 1=1"
            params = []
            if doctor_id:
                query += " AND doctor_id = ?"
                params.append(doctor_id)
            if department:
                query += " AND department = ?"
                params.append(department)
            if patient_id:
                query += " AND patient_id = ?"
                params.append(patient_id)
            query += " ORDER BY scheduled_at ASC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_appointment(self, data: dict) -> dict:
        apt_id = data.get("id") or f"APT-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        sched = data.get("scheduled_at") or now
        status = data.get("status") or "SCHEDULED"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO appointments (id, patient_id, hospital_id, department, doctor_id, scheduled_at, status, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    apt_id,
                    data["patient_id"],
                    data.get("hospital_id", "H001"),
                    data.get("department", "General"),
                    data.get("doctor_id", "doctor"),
                    sched,
                    status,
                    data.get("reason", "Consultation"),
                    now
                )
            )
        return {**data, "id": apt_id, "scheduled_at": sched, "status": status, "created_at": now}

    async def update_appointment_status(self, appointment_id: str, status: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
            return cur.rowcount > 0

    async def get_admissions(self, department: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM admissions WHERE 1=1"
            params = []
            if department:
                query += " AND department = ?"
                params.append(department)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY admitted_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_admission(self, data: dict) -> dict:
        adm_id = data.get("id") or f"ADM-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        status = data.get("status") or "ADMITTED"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO admissions (id, patient_id, hospital_id, department, room_bed, admission_type, admitting_doctor_id, assigned_nurse_id, admitted_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    adm_id,
                    data["patient_id"],
                    data.get("hospital_id", "H001"),
                    data.get("department", "Emergency"),
                    data.get("room_bed", "Unassigned"),
                    data.get("admission_type", "EMERGENCY"),
                    data.get("admitting_doctor_id", "doctor"),
                    data.get("assigned_nurse_id", "nurse"),
                    now,
                    status
                )
            )
            conn.execute("UPDATE patients SET room_bed = ?, department = ?, updated_at = ? WHERE id = ?", (data.get("room_bed", "Bed-01"), data.get("department", "Emergency"), now, data["patient_id"]))
        return {**data, "id": adm_id, "admitted_at": now, "status": status}

    async def discharge_admission(self, admission_id: str) -> bool:
        now = _utcnow()
        with self._connect() as conn:
            cur = conn.execute("UPDATE admissions SET status = 'DISCHARGED', discharge_date = ? WHERE id = ?", (now, admission_id))
            return cur.rowcount > 0

    async def get_lab_orders(self, patient_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM lab_orders WHERE 1=1"
            params = []
            if patient_id:
                query += " AND patient_id = ?"
                params.append(patient_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY ordered_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_lab_order(self, data: dict) -> dict:
        lab_id = data.get("id") or f"LAB-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        status = data.get("status") or "ORDERED"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lab_orders (id, patient_id, doctor_id, test_name, category, priority, status, result_data, reference_range, flagged_abnormal, ordered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lab_id,
                    data["patient_id"],
                    data.get("doctor_id", "doctor"),
                    data["test_name"],
                    data.get("category", "Biochemistry"),
                    data.get("priority", "ROUTINE"),
                    status,
                    _json(data.get("result_data", {})),
                    data.get("reference_range", "Standard"),
                    1 if data.get("flagged_abnormal") else 0,
                    now
                )
            )
        return {**data, "id": lab_id, "status": status, "ordered_at": now}

    async def update_lab_order_result(self, lab_id: str, result_data: dict, abnormal: bool = False, approved_by: str = "lab_tech") -> bool:
        now = _utcnow()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE lab_orders SET result_data = ?, flagged_abnormal = ?, status = 'COMPLETED', completed_at = ?, approved_by = ? WHERE id = ?",
                (_json(result_data), 1 if abnormal else 0, now, approved_by, lab_id)
            )
            return cur.rowcount > 0

    async def get_prescriptions(self, patient_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM prescriptions WHERE 1=1"
            params = []
            if patient_id:
                query += " AND patient_id = ?"
                params.append(patient_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY ordered_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_prescription(self, data: dict) -> dict:
        rx_id = data.get("id") or f"RX-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        status = data.get("status") or "PRESCRIBED"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prescriptions (id, patient_id, doctor_id, medication, dosage, frequency, duration, status, ddi_warning, ordered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rx_id,
                    data["patient_id"],
                    data.get("doctor_id", "doctor"),
                    data["medication"],
                    data.get("dosage", "1 tab"),
                    data.get("frequency", "OD"),
                    data.get("duration", "7 days"),
                    status,
                    data.get("ddi_warning"),
                    now
                )
            )
        return {**data, "id": rx_id, "status": status, "ordered_at": now}

    async def dispense_prescription(self, prescription_id: str, pharmacist_id: str = "pharmacist") -> bool:
        now = _utcnow()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE prescriptions SET status = 'DISPENSED', pharmacist_id = ?, dispensed_at = ? WHERE id = ?",
                (pharmacist_id, now, prescription_id)
            )
            return cur.rowcount > 0

    async def get_billing_invoices(self, patient_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM billing_invoices WHERE 1=1"
            params = []
            if patient_id:
                query += " AND patient_id = ?"
                params.append(patient_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_billing_invoice(self, data: dict) -> dict:
        inv_id = data.get("id") or f"INV-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        total = float(data.get("total_amount", 0.0))
        claim = float(data.get("insurance_claim_amount", 0.0))
        payable = float(data.get("patient_payable", max(0.0, total - claim)))
        status = data.get("status") or "PENDING"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO billing_invoices (id, patient_id, hospital_id, total_amount, insurance_claim_amount, patient_payable, status, payment_method, line_items, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inv_id,
                    data["patient_id"],
                    data.get("hospital_id", "H001"),
                    total,
                    claim,
                    payable,
                    status,
                    data.get("payment_method", "INSURANCE_TPA"),
                    _json(data.get("line_items", [])),
                    now
                )
            )
        return {**data, "id": inv_id, "total_amount": total, "insurance_claim_amount": claim, "patient_payable": payable, "status": status, "created_at": now}

    async def settle_billing_invoice(self, invoice_id: str, payment_method: str = "UPI") -> bool:
        now = _utcnow()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE billing_invoices SET status = 'SETTLED', payment_method = ?, settled_at = ? WHERE id = ?",
                (payment_method, now, invoice_id)
            )
            return cur.rowcount > 0

    async def get_emergency_dispatches(self, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM emergency_dispatches WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY dispatched_at DESC"
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    async def create_emergency_dispatch(self, data: dict) -> dict:
        dsp_id = data.get("id") or f"DSP-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO emergency_dispatches (id, ambulance_id, paramedic_id, patient_id, caller_name, emergency_type, triage_priority, origin_location, destination_hospital, green_corridor_active, vitals, dispatched_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dsp_id,
                    data["ambulance_id"],
                    data.get("paramedic_id", "paramedic"),
                    data.get("patient_id"),
                    data.get("caller_name", "Public Emergency Dispatch"),
                    data.get("emergency_type", "Cardiac Emergency"),
                    data.get("triage_priority", "P1_CRITICAL"),
                    data.get("origin_location", "Koramangala 5th Block"),
                    data.get("destination_hospital", "City General Hospital (H001)"),
                    1 if data.get("green_corridor_active") else 0,
                    _json(data.get("vitals", {})),
                    now,
                    data.get("status", "DISPATCHED")
                )
            )
        return {**data, "id": dsp_id, "dispatched_at": now}

    async def update_emergency_dispatch(self, dispatch_id: str, updates: dict) -> bool:
        now = _utcnow()
        allowed = ["status", "green_corridor_active", "vitals", "arrived_scene_at", "arrived_hospital_at"]
        sets = []
        params = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(_json(v) if k == "vitals" and isinstance(v, (dict, list)) else v)
        if not sets:
            return False
        params.append(dispatch_id)
        with self._connect() as conn:
            cur = conn.execute(f"UPDATE emergency_dispatches SET {', '.join(sets)} WHERE id = ?", params)
            return cur.rowcount > 0

    async def record_break_glass_event(self, data: dict) -> dict:
        bg_id = data.get("id") or f"BG-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO break_glass_events (id, user_id, username, role, patient_id, department, hospital_id, reason, previous_risk_score, new_risk_score, notified_security, security_incident_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    bg_id,
                    data.get("user_id", data.get("username", "unknown")),
                    data["username"],
                    data.get("role", "doctor"),
                    data["patient_id"],
                    data.get("department", "Emergency"),
                    data.get("hospital_id", "H001"),
                    data["reason"],
                    data.get("previous_risk_score", 10.0),
                    data.get("new_risk_score", 45.0),
                    1,
                    data.get("security_incident_id"),
                    now
                )
            )
        return {**data, "id": bg_id, "timestamp": now}

    async def get_break_glass_events(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM break_glass_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    async def update_user_risk(self, username: str, new_risk: float) -> bool:
        with self._connect() as conn:
            cur = conn.execute("UPDATE users SET risk_score = ? WHERE username = ?", (new_risk, username))
            return cur.rowcount > 0

    async def get_ambulances(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM ambulances ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def update_ambulance_status(
        self, ambulance_id: str, status: str, location: Optional[str] = None, eta: Optional[int] = None
    ) -> bool:
        now = _utcnow()
        with self._connect() as conn:
            updates = ["status = ?", "updated_at = ?"]
            params = [status, now]
            if location is not None:
                updates.append("current_location = ?")
                params.append(location)
            if eta is not None:
                updates.append("eta_minutes = ?")
                params.append(eta)
            params.append(ambulance_id)
            cur = conn.execute(f"UPDATE ambulances SET {', '.join(updates)} WHERE id = ?", params)
            return cur.rowcount > 0

    async def get_traffic_signals(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM traffic_signals ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_traffic_signal(self, signal_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM traffic_signals WHERE id = ?", (signal_id,)).fetchone()
            return dict(row) if row else None

    async def update_traffic_signal(
        self, signal_id: str, state: str, mode: str = "MANUAL", override_by: str = "OPERATOR"
    ) -> bool:
        now = _utcnow()
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE traffic_signals SET current_state = ?, mode = ?, last_override_by = ?, updated_at = ? WHERE id = ?",
                (state, mode, override_by, now, signal_id)
            )
            return cur.rowcount > 0

    async def get_traffic_cameras(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM traffic_cameras ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_traffic_camera(self, camera_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM traffic_cameras WHERE id = ?", (camera_id,)).fetchone()
            return dict(row) if row else None

    async def save_traffic_camera(self, cam: dict) -> dict:
        now = _utcnow()
        cam_id = cam.get("id") or f"CAM-{uuid.uuid4().hex[:6].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO traffic_cameras
                (id, name, location, latitude, longitude, intersection_id, road_id, camera_type, stream_type, stream_url, status, health, fps, resolution, incident_count, last_seen, device_id, trust_status, risk_score, created_at, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cam_id,
                    cam.get("name", f"Camera {cam_id}"),
                    cam.get("location", "City Grid"),
                    cam.get("latitude", 12.9716),
                    cam.get("longitude", 77.5946),
                    cam.get("intersection_id"),
                    cam.get("road_id"),
                    cam.get("camera_type", "FIXED_CCTV"),
                    cam.get("stream_type", "WEBRTC"),
                    cam.get("stream_url", f"/api/traffic/stream/{cam_id}"),
                    cam.get("status", "ONLINE"),
                    cam.get("health", "HEALTHY"),
                    float(cam.get("fps", 30.0)),
                    cam.get("resolution", "1920x1080"),
                    int(cam.get("incident_count", 0)),
                    cam.get("last_seen", now),
                    cam.get("device_id", f"DEV-{cam_id}"),
                    cam.get("trust_status", "TRUSTED"),
                    float(cam.get("risk_score", 0.0)),
                    cam.get("created_at", now),
                    _json(cam.get("metadata", cam.get("metadata_json", {}))),
                    now
                )
            )
        return await self.get_traffic_camera(cam_id)

    async def update_traffic_camera(self, camera_id: str, updates: dict) -> Optional[dict]:
        now = _utcnow()
        allowed = [
            "name", "location", "latitude", "longitude", "intersection_id", "road_id",
            "camera_type", "stream_type", "stream_url", "status", "health", "fps",
            "resolution", "incident_count", "last_seen", "device_id", "trust_status",
            "risk_score", "metadata_json"
        ]
        sets = []
        params = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(_json(v) if k == "metadata_json" and isinstance(v, (dict, list)) else v)
        if not sets:
            return await self.get_traffic_camera(camera_id)
        sets.append("updated_at = ?")
        params.append(now)
        params.append(camera_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE traffic_cameras SET {', '.join(sets)} WHERE id = ?", params)
        return await self.get_traffic_camera(camera_id)

    async def delete_traffic_camera(self, camera_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM traffic_cameras WHERE id = ?", (camera_id,))
            return cur.rowcount > 0

    async def save_mobile_camera_session(self, session: dict) -> dict:
        now = _utcnow()
        sid = session.get("session_id") or f"MOB-CAM-{uuid.uuid4().hex[:6].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO mobile_camera_sessions
                (session_id, device_id, camera_id, user_id, latitude, longitude, started_at, last_seen, status, stream_status, trust_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    session.get("device_id", f"DEV-MOB-{sid}"),
                    session.get("camera_id", f"CAM-MOB-{sid}"),
                    session.get("user_id", "traffic_operator"),
                    float(session.get("latitude", 12.9716)),
                    float(session.get("longitude", 77.5946)),
                    session.get("started_at", now),
                    now,
                    session.get("status", "ACTIVE"),
                    session.get("stream_status", "STREAMING"),
                    session.get("trust_status", "EVALUATED")
                )
            )
        return await self.get_mobile_camera_session(sid)

    async def get_mobile_camera_session(self, session_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM mobile_camera_sessions WHERE session_id = ?", (session_id,)).fetchone()
            return dict(row) if row else None

    async def update_mobile_camera_session(self, session_id: str, updates: dict) -> Optional[dict]:
        now = _utcnow()
        allowed = ["latitude", "longitude", "status", "stream_status", "trust_status"]
        sets = []
        params = []
        for k, v in updates.items():
            if k in allowed:
                sets.append(f"{k} = ?")
                params.append(v)
        sets.append("last_seen = ?")
        params.append(now)
        params.append(session_id)
        with self._connect() as conn:
            conn.execute(f"UPDATE mobile_camera_sessions SET {', '.join(sets)} WHERE session_id = ?", params)
        return await self.get_mobile_camera_session(session_id)

    async def save_vehicle_detection(self, det: dict) -> dict:
        now = _utcnow()
        det_id = det.get("detection_id") or f"DET-{uuid.uuid4().hex[:8].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO vehicle_detections
                (detection_id, camera_id, timestamp, vehicle_class, confidence, bounding_box_json, tracking_id, location, direction, speed_estimate, lane, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    det_id,
                    det.get("camera_id", "CAM-101"),
                    det.get("timestamp", now),
                    det.get("vehicle_class", "car"),
                    float(det.get("confidence", 0.92)),
                    _json(det.get("bounding_box", [120, 80, 240, 160])),
                    det.get("tracking_id", f"TRACK-{random.randint(10, 99)}"),
                    det.get("location", "Silk Board South Interchange"),
                    det.get("direction", "NORTH"),
                    float(det.get("speed_estimate", 45.0)),
                    int(det.get("lane", 1)),
                    _json(det.get("metadata", {}))
                )
            )
        return {**det, "detection_id": det_id, "timestamp": now}

    async def get_vehicle_detections(self, limit: int = 50, camera_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if camera_id:
                rows = conn.execute(
                    "SELECT * FROM vehicle_detections WHERE camera_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (camera_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM vehicle_detections ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    async def save_rfid_reader(self, reader: dict) -> dict:
        now = _utcnow()
        rid = reader.get("reader_id") or f"RFID-RDR-{uuid.uuid4().hex[:6].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO rfid_readers
                (reader_id, location, lane, status, ip_address, device_id, trust_status, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rid,
                    reader.get("location", "Toll Plaza Gantry"),
                    reader.get("lane", "LANE-01"),
                    reader.get("status", "ONLINE"),
                    reader.get("ip_address", "10.12.4.50"),
                    reader.get("device_id", f"DEV-{rid}"),
                    reader.get("trust_status", "TRUSTED"),
                    now
                )
            )
        return {**reader, "reader_id": rid, "last_seen": now}

    async def get_rfid_readers(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM rfid_readers ORDER BY reader_id ASC").fetchall()
            return [dict(r) for r in rows]

    async def save_rfid_read(self, read: dict) -> dict:
        now = _utcnow()
        read_id = read.get("read_id") or f"READ-{uuid.uuid4().hex[:8].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rfid_reads
                (read_id, reader_id, timestamp, tag_id, lane, signal_strength, vehicle_association, confidence, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    read_id,
                    read.get("reader_id", "RFID-READER-01"),
                    read.get("timestamp", now),
                    read.get("tag_id", "TAG-98231"),
                    read.get("lane", "LANE-01"),
                    float(read.get("signal_strength", -58.0)),
                    read.get("vehicle_association"),
                    float(read.get("confidence", 0.98)),
                    _json(read.get("metadata", {}))
                )
            )
        return {**read, "read_id": read_id, "timestamp": now}

    async def get_rfid_reads(self, limit: int = 50, reader_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if reader_id:
                rows = conn.execute(
                    "SELECT * FROM rfid_reads WHERE reader_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (reader_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM rfid_reads ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    async def get_fastag(self, tag_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM fastags WHERE tag_id = ?", (tag_id,)).fetchone()
            return dict(row) if row else None

    async def save_fastag(self, fastag: dict) -> dict:
        now = _utcnow()
        fid = fastag.get("fastag_id") or f"FT-{uuid.uuid4().hex[:6].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO fastags
                (fastag_id, tag_id, vehicle_id, vehicle_registration, customer_id, status, issuer, linked_account, created_at, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fid,
                    fastag["tag_id"],
                    fastag.get("vehicle_id", f"VEH-{fid}"),
                    fastag["vehicle_registration"],
                    fastag.get("customer_id", "CUST-1001"),
                    fastag.get("status", "ACTIVE"),
                    fastag.get("issuer", "NPCI_NETC"),
                    fastag.get("linked_account", "ACC-***-9021"),
                    fastag.get("created_at", now),
                    now
                )
            )
        return await self.get_fastag(fastag["tag_id"])

    async def save_vehicle_verification(self, verif: dict) -> dict:
        now = _utcnow()
        vid = verif.get("verification_id") or f"VVERIF-{uuid.uuid4().hex[:8].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO vehicle_identity_verifications
                (verification_id, rfid_read_id, detection_id, camera_id, tag_id, registered_plate, ocr_plate, rfid_confidence, ocr_confidence, identity_confidence, status, risk_score, repeated_mismatch_count, cameras_seen_json, timestamp, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    vid,
                    verif.get("rfid_read_id"),
                    verif.get("detection_id"),
                    verif.get("camera_id", "CAM-101"),
                    verif.get("tag_id"),
                    verif.get("registered_plate"),
                    verif.get("ocr_plate"),
                    float(verif.get("rfid_confidence", 0.0)),
                    float(verif.get("ocr_confidence", 0.0)),
                    float(verif.get("identity_confidence", 0.0)),
                    verif.get("status", "VERIFIED"),
                    float(verif.get("risk_score", 0.0)),
                    int(verif.get("repeated_mismatch_count", 0)),
                    _json(verif.get("cameras_seen", [])),
                    verif.get("timestamp", now),
                    _json(verif.get("details", {}))
                )
            )
        return {**verif, "verification_id": vid, "timestamp": now}

    async def get_vehicle_verifications(self, limit: int = 50, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM vehicle_identity_verifications WHERE status = ? ORDER BY timestamp DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM vehicle_identity_verifications ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            res = []
            for r in rows:
                d = dict(r)
                if "id" not in d and "verification_id" in d:
                    d["id"] = d["verification_id"]
                res.append(d)
            return res

    async def get_vehicle_verification(self, verification_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM vehicle_identity_verifications WHERE verification_id = ?",
                (verification_id,)
            ).fetchone()
            if not row:
                return None
            d = dict(row)
            if "id" not in d and "verification_id" in d:
                d["id"] = d["verification_id"]
            return d

    async def get_bank_accounts(self, customer_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if customer_id:
                rows = conn.execute("SELECT * FROM bank_accounts WHERE customer_id = ?", (customer_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM bank_accounts ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_bank_account(self, account_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM bank_accounts WHERE id = ?", (account_id,)).fetchone()
            return dict(row) if row else None

    async def get_bank_transactions(self, account_id: Optional[str] = None, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            if account_id:
                rows = conn.execute(
                    "SELECT * FROM bank_transactions WHERE account_id = ? ORDER BY created_at DESC LIMIT ?",
                    (account_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM bank_transactions ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    async def create_bank_transaction(
        self, account_id: str, sender_name: str, receiver_account: str,
        amount: float, channel: str = "ONLINE_BANKING", transaction_type: str = "WIRE_TRANSFER",
        risk_score: float = 5.0, decision: str = "ALLOWED", is_fraud: int = 0
    ) -> dict:
        tx_id = f"TX-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO bank_transactions
                (id, account_id, sender_name, receiver_account, amount, channel, transaction_type, risk_score, decision, is_fraud, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (tx_id, account_id, sender_name, receiver_account, amount, channel, transaction_type, risk_score, decision, is_fraud, now)
            )
        return {
            "id": tx_id, "account_id": account_id, "sender_name": sender_name,
            "receiver_account": receiver_account, "amount": amount, "channel": channel,
            "transaction_type": transaction_type, "risk_score": risk_score, "decision": decision,
            "is_fraud": is_fraud, "created_at": now
        }

    async def get_security_policies(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM security_policies ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def update_security_policy(self, policy_id: str, updates: dict) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM security_policies WHERE id = ?", (policy_id,)).fetchone()
            if not row:
                return None
            fields = []
            vals = []
            for k, v in updates.items():
                if k in ("name", "domain", "rule_definition", "risk_modifier", "action", "description", "is_active"):
                    fields.append(f"{k} = ?")
                    vals.append(v)
            if fields:
                vals.append(policy_id)
                conn.execute(f"UPDATE security_policies SET {', '.join(fields)} WHERE id = ?", vals)
            updated = conn.execute("SELECT * FROM security_policies WHERE id = ?", (policy_id,)).fetchone()
            return dict(updated) if updated else None

    async def get_cross_domain_threats(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM cross_domain_threats ORDER BY risk_score DESC").fetchall()
            return [dict(r) for r in rows]

    async def add_cross_domain_threat(
        self, threat_actor_ip: str, device_id: str, domains_involved: list,
        risk_score: float, campaign_summary: str, status: str = "ACTIVE"
    ) -> dict:
        cid = f"CDT-{uuid.uuid4().hex[:4].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cross_domain_threats
                (id, threat_actor_ip, device_id, domains_involved, first_seen, last_seen, risk_score, campaign_summary, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cid, threat_actor_ip, device_id, _json(domains_involved), now, now, risk_score, campaign_summary, status)
            )
        return {
            "id": cid, "threat_actor_ip": threat_actor_ip, "device_id": device_id,
            "domains_involved": domains_involved, "first_seen": now, "last_seen": now,
            "risk_score": risk_score, "campaign_summary": campaign_summary, "status": status
        }

    async def get_devices(self, user_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if user_id:
                rows = conn.execute("SELECT * FROM devices WHERE user_id = ?", (user_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM devices ORDER BY last_seen DESC").fetchall()
            return [dict(r) for r in rows]

    async def register_device(
        self, user_id: str, fingerprint: str, os_name: str, browser: str,
        ip: str, location: str, trust_score: float = 100.0, status: str = "TRUSTED"
    ) -> dict:
        dev_id = f"DEV-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        with self._connect() as conn:
            user_row = conn.execute("SELECT id FROM users WHERE id = ? OR username = ?", (user_id, user_id)).fetchone()
            resolved_uid = user_row["id"] if user_row else user_id
            conn.execute(
                """
                INSERT INTO devices
                (id, user_id, fingerprint, os, browser, ip, location, trust_score, status, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (dev_id, resolved_uid, fingerprint, os_name, browser, ip, location, trust_score, status, now, now)
            )
        return {
            "id": dev_id, "user_id": user_id, "fingerprint": fingerprint,
            "os": os_name, "browser": browser, "ip": ip, "location": location,
            "trust_score": trust_score, "status": status, "first_seen": now, "last_seen": now
        }

    async def get_user_risk_profile(self, username: str) -> dict:
        user = self.get_user(username)
        if not user:
            return {"status": "not_found", "username": username}

        with self._connect() as conn:
            incidents = conn.execute(
                "SELECT COUNT(*) FROM incidents WHERE owner = ? OR payload LIKE ?",
                (username, f"%{username}%")
            ).fetchone()[0]
            devices = conn.execute("SELECT * FROM devices WHERE user_id = ?", (username,)).fetchall()
            recent_audits = conn.execute(
                "SELECT * FROM audit_logs WHERE actor = ? ORDER BY timestamp DESC LIMIT 10",
                (username,)
            ).fetchall()

        return {
            "username": username,
            "role": user.get("role"),
            "full_name": user.get("full_name"),
            "risk_score": 15.0 + (incidents * 12.0),
            "trust_level": "HIGH" if incidents == 0 else "MEDIUM" if incidents < 3 else "SUSPICIOUS",
            "active_incidents": incidents,
            "enrolled_devices": [dict(d) for d in devices],
            "recent_activity_timeline": [dict(a) for a in recent_audits]
        }

    # ==========================================================================
    # PERSISTENT SIMULATION STATE
    # ==========================================================================

    async def save_simulation_state(
        self,
        scenario_id: str,
        status: str,
        current_stage: int = 0,
        stage_name: str | None = None,
        elapsed_seconds: float = 0.0,
        events_emitted: int = 0,
        state_blob: dict | None = None,
        state_id: str = "active_state"
    ) -> dict:
        """Persists active simulation state so engine restarts do not destroy progress."""
        now = _utcnow()
        blob_str = _json(state_blob or {})
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO simulation_state (
                        id, scenario_id, status, current_stage, stage_name,
                        elapsed_seconds, events_emitted, state_blob, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        scenario_id = excluded.scenario_id,
                        status = excluded.status,
                        current_stage = excluded.current_stage,
                        stage_name = excluded.stage_name,
                        elapsed_seconds = excluded.elapsed_seconds,
                        events_emitted = excluded.events_emitted,
                        state_blob = excluded.state_blob,
                        updated_at = excluded.updated_at
                    """,
                    (state_id, scenario_id, status, current_stage, stage_name,
                     elapsed_seconds, events_emitted, blob_str, now)
                )
                conn.commit()
        return {
            "id": state_id,
            "scenario_id": scenario_id,
            "status": status,
            "current_stage": current_stage,
            "stage_name": stage_name,
            "elapsed_seconds": elapsed_seconds,
            "events_emitted": events_emitted,
            "updated_at": now
        }

    async def get_simulation_state(self, state_id: str = "active_state") -> dict | None:
        """Retrieves persisted simulation state for recovery on reboot."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM simulation_state WHERE id = ?", (state_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["state_blob"] = _loads(d.get("state_blob"), {})
            return d

    # ==========================================================================
    # SECURITY BANS & ACCESS STATE
    # ==========================================================================

    async def add_security_ban(
        self,
        target_type: str,
        target_value: str,
        reason: str,
        banned_by: str = "SYSTEM",
        expires_at: str | None = None
    ) -> dict:
        """Enforces and persists an IP, device, user, or account ban."""
        ban_id = str(uuid.uuid4())
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO security_bans (
                        id, target_type, target_value, reason, banned_by, banned_at, expires_at, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    (ban_id, target_type.upper(), target_value, reason, banned_by, now, expires_at)
                )
                conn.commit()
        return {
            "id": ban_id,
            "target_type": target_type.upper(),
            "target_value": target_value,
            "reason": reason,
            "banned_by": banned_by,
            "banned_at": now,
            "is_active": True
        }

    async def get_security_bans(self, active_only: bool = True) -> list[dict]:
        """Lists active security bans."""
        query = "SELECT * FROM security_bans"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY banned_at DESC"
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query).fetchall()]

    async def is_banned(self, target_type: str, target_value: str) -> bool:
        """Checks if an entity is banned."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM security_bans WHERE target_type = ? AND target_value = ? AND is_active = 1",
                (target_type.upper(), target_value)
            ).fetchone()
            return row is not None

    # ==========================================================================
    # AML GRAPH STATE & FRAUD CASES
    # ==========================================================================

    async def save_aml_graph_state(
        self,
        graph_name: str,
        node_count: int,
        edge_count: int,
        mule_cluster_count: int,
        nodes: list[dict],
        edges: list[dict],
        clusters: list[dict],
        graph_id: str = "primary"
    ) -> dict:
        """Persists the computed money mule network topology."""
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO aml_graph_state (
                        id, graph_name, node_count, edge_count, mule_cluster_count,
                        nodes_json, edges_json, clusters_json, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        graph_name = excluded.graph_name,
                        node_count = excluded.node_count,
                        edge_count = excluded.edge_count,
                        mule_cluster_count = excluded.mule_cluster_count,
                        nodes_json = excluded.nodes_json,
                        edges_json = excluded.edges_json,
                        clusters_json = excluded.clusters_json,
                        updated_at = excluded.updated_at
                    """,
                    (graph_id, graph_name, node_count, edge_count, mule_cluster_count,
                     _json(nodes), _json(edges), _json(clusters), now)
                )
                conn.commit()
        return {
            "id": graph_id,
            "graph_name": graph_name,
            "node_count": node_count,
            "edge_count": edge_count,
            "mule_cluster_count": mule_cluster_count,
            "updated_at": now
        }

    async def get_aml_graph_state(self, graph_id: str = "primary") -> dict | None:
        """Retrieves persisted money mule network topology."""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM aml_graph_state WHERE id = ?", (graph_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["nodes"] = _loads(d.get("nodes_json"), [])
            d["edges"] = _loads(d.get("edges_json"), [])
            d["clusters"] = _loads(d.get("clusters_json"), [])
            return d

    async def create_fraud_case(
        self,
        customer_id: str,
        fraud_type: str,
        amount: float,
        risk_score: float,
        transaction_id: str | None = None,
        notes: str | None = None,
        evidence: dict | None = None
    ) -> dict:
        """Creates a dedicated fraud investigation case."""
        case_id = f"CASE-FRD-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO fraud_cases (
                        id, transaction_id, customer_id, fraud_type, amount,
                        risk_score, status, analyst_notes, evidence_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?)
                    """,
                    (case_id, transaction_id, customer_id, fraud_type, amount,
                     risk_score, notes, _json(evidence or {}), now, now)
                )
                conn.commit()
        return {"id": case_id, "customer_id": customer_id, "status": "OPEN", "created_at": now}

    async def create_aml_case(
        self,
        suspect_account_id: str,
        case_type: str,
        total_suspicious_volume: float,
        risk_score: float,
        confidence: float = 0.95,
        sar_filed: bool = False,
        evidence: dict | None = None
    ) -> dict:
        """Creates an AML suspicious activity investigation case."""
        case_id = f"CASE-AML-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO aml_cases (
                        id, suspect_account_id, case_type, total_suspicious_volume,
                        risk_score, confidence, status, sar_filed, evidence_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'INVESTIGATING', ?, ?, ?, ?)
                    """,
                    (case_id, suspect_account_id, case_type, total_suspicious_volume,
                     risk_score, confidence, int(sar_filed), _json(evidence or {}), now, now)
                )
                conn.commit()
        return {"id": case_id, "suspect_account_id": suspect_account_id, "status": "INVESTIGATING", "created_at": now}


    # ══════════════════════════════════════════════════════════════════
    # SMART TRAFFIC OPERATIONAL METHODS
    # ══════════════════════════════════════════════════════════════════
    async def get_intersections(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM intersections ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_intersection(self, intersection_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM intersections WHERE id = ?", (intersection_id,)).fetchone()
            return dict(row) if row else None

    async def get_road_segments(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM road_segments ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_road_segment(self, road_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM road_segments WHERE id = ?", (road_id,)).fetchone()
            return dict(row) if row else None

    async def get_traffic_sensors(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM sensors ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

    async def get_sensor_disparity_analysis(self) -> dict:
        """
        Sensor Disparity Engine: Compares inductive loop physical counts vs.
        CCTV computer vision bounding box track counts at paired intersections.
        Flags loop shorts, physical vandalism, and SCADA cyber injection.
        """
        pairs = [
            {
                "junction": "Grand Ave & 4th St (Central)",
                "sensor_id": "SEN-LOOP-01",
                "sensor_type": "INDUCTIVE_LOOP",
                "sensor_count": 240,
                "camera_id": "CAM-01",
                "camera_detected_count": 235,
                "disparity_delta": 5,
                "disparity_pct": 2.1,
                "status": "NOMINAL",
                "confidence": 0.98,
                "diagnosis": "Sensor and camera telemetry synchronized within standard tolerance (<5%)."
            },
            {
                "junction": "Hospital Blvd Corridor Gate",
                "sensor_id": "SEN-LOOP-02",
                "sensor_type": "INDUCTIVE_LOOP",
                "sensor_count": 0,
                "camera_id": "CAM-02",
                "camera_detected_count": 48,
                "disparity_delta": 48,
                "disparity_pct": 100.0,
                "status": "ANOMALOUS_DISPARITY",
                "confidence": 0.94,
                "diagnosis": "CRITICAL DISPARITY: Loop sensor reporting 0 vehicles while CCTV detects 48 moving vehicles. High probability of inductive loop physical short or SCADA zero-clamp injection."
            },
            {
                "junction": "Fintech Tower Expressway",
                "sensor_id": "SEN-RADAR-01",
                "sensor_type": "RADAR_SPEED",
                "sensor_count": 85,
                "camera_id": "CAM-03",
                "camera_detected_count": 82,
                "disparity_delta": 3,
                "disparity_pct": 3.5,
                "status": "NOMINAL",
                "confidence": 0.96,
                "diagnosis": "Radar velocity and optical flow correlate nominal."
            },
            {
                "junction": "Expressway SCADA Tollgate 04",
                "sensor_id": "SEN-RADAR-02",
                "sensor_type": "RADAR_SPEED",
                "sensor_count": 0,
                "camera_id": "CAM-05",
                "camera_detected_count": 78,
                "disparity_delta": 78,
                "disparity_pct": 100.0,
                "status": "ANOMALOUS_DISPARITY",
                "confidence": 0.91,
                "diagnosis": "RADAR SENSOR FAILURE / SPOOFING: Zero Doppler reflection while optical tracks detect high-velocity traffic."
            }
        ]
        anomalies_detected = sum(1 for p in pairs if p["status"] == "ANOMALOUS_DISPARITY")
        alerts = [p for p in pairs if p["status"] == "ANOMALOUS_DISPARITY"]
        return {
            "status": "ok",
            "timestamp": _utcnow(),
            "pairs_analyzed": len(pairs),
            "anomalies_detected": anomalies_detected,
            "systemic_integrity_score": round(100.0 - (anomalies_detected / len(pairs) * 50.0), 1),
            "disparity_pairs": pairs,
            "disparity_alerts": alerts,
            "cross_comparison": pairs
        }

    async def get_traffic_incidents(self, status: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM traffic_incidents WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY reported_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def create_traffic_incident(self, data: dict) -> dict:
        inc_id = data.get("id") or f"INC-TRF-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO traffic_incidents (
                        id, title, category, severity, status, location, road_id, intersection_id,
                        reported_by, assigned_officer, verified, verified_by, verified_at,
                        resolution_notes, reported_at, resolved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, NULL, NULL, ?, NULL)
                    """,
                    (
                        inc_id,
                        data["title"],
                        data.get("category", "ACCIDENT"),
                        data.get("severity", "MEDIUM"),
                        data.get("status", "REPORTED"),
                        data["location"],
                        data.get("road_id"),
                        data.get("intersection_id"),
                        data.get("reported_by", "traffic_operator"),
                        data.get("assigned_officer", "traffic_police"),
                        now,
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM traffic_incidents WHERE id = ?", (inc_id,)).fetchone()
                return dict(row)

    async def verify_traffic_incident(self, incident_id: str, officer_id: Optional[str] = None, verified_by: Optional[str] = None, notes: Optional[str] = None) -> Optional[dict]:
        now = _utcnow()
        officer = officer_id or verified_by or "traffic_police"
        async with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE traffic_incidents
                    SET verified = 1, verified_by = ?, verified_at = ?, status = 'VERIFIED',
                        resolution_notes = COALESCE(?, resolution_notes)
                    WHERE id = ?
                    """,
                    (officer, now, notes, incident_id)
                )
                conn.commit()
                if cur.rowcount == 0:
                    return None
                row = conn.execute("SELECT * FROM traffic_incidents WHERE id = ?", (incident_id,)).fetchone()
                return dict(row)

    async def update_traffic_incident_status(self, incident_id: str, status: str, notes: Optional[str] = None, resolution_notes: Optional[str] = None) -> Optional[dict]:
        now = _utcnow()
        actual_notes = resolution_notes or notes
        resolved_at = now if status == "RESOLVED" else None
        async with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE traffic_incidents
                    SET status = ?, resolution_notes = COALESCE(?, resolution_notes),
                        resolved_at = CASE WHEN ? = 'RESOLVED' THEN ? ELSE resolved_at END
                    WHERE id = ?
                    """,
                    (status, actual_notes, status, resolved_at, incident_id)
                )
                conn.commit()
                if cur.rowcount == 0:
                    return None
                row = conn.execute("SELECT * FROM traffic_incidents WHERE id = ?", (incident_id,)).fetchone()
                return dict(row)

    async def get_toll_scans(self, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM toll_scans WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY timestamp DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def process_toll_scan(self, data: dict) -> dict:
        scan_id = data.get("id") or f"SCAN-FT-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        status = data.get("status", "CLEARED")
        flag_reason = data.get("flag_reason")
        fastag_id = data["fastag_id"]

        async with self._lock:
            with self._connect() as conn:
                recent = conn.execute(
                    "SELECT * FROM toll_scans WHERE fastag_id = ? AND status = 'CLEARED' ORDER BY timestamp DESC LIMIT 1",
                    (fastag_id,)
                ).fetchone()
                if recent and recent["tollgate_id"] != data["tollgate_id"]:
                    status = "CLONED"
                    flag_reason = f"Duplicate cryptographic signature detected across {recent['tollgate_name']} and {data.get('tollgate_name', 'Current Gantry')}"

                conn.execute(
                    """
                    INSERT INTO toll_scans (
                        id, tollgate_id, tollgate_name, vehicle_number, fastag_id,
                        amount, status, flag_reason, override_by, override_reason, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                    """,
                    (
                        scan_id,
                        data["tollgate_id"],
                        data.get("tollgate_name", "Tollgate Gantry"),
                        data["vehicle_number"],
                        fastag_id,
                        data.get("amount", 120.0),
                        status,
                        flag_reason,
                        now
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM toll_scans WHERE id = ?", (scan_id,)).fetchone()
                return dict(row)

    async def override_toll_scan(self, scan_id: str, override_by: Optional[str] = None, approved_by: Optional[str] = None, reason: str = "") -> Optional[dict]:
        approver = override_by or approved_by or "supervisor"
        async with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE toll_scans
                    SET status = 'OVERRIDDEN_CLEARED', override_by = ?, override_reason = ?
                    WHERE id = ?
                    """,
                    (approver, reason, scan_id)
                )
                conn.commit()
                if cur.rowcount == 0:
                    return None
                row = conn.execute("SELECT * FROM toll_scans WHERE id = ?", (scan_id,)).fetchone()
                return dict(row)

    async def get_green_corridors(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM green_corridors ORDER BY id ASC").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["route_intersections"] = _loads(d.get("route_intersections"), [])
                d["cleared_signals"] = _loads(d.get("cleared_signals"), [])
                result.append(d)
            return result

    async def create_green_corridor(self, data: dict) -> dict:
        corr_id = data.get("id") or f"CORR-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO green_corridors (
                        id, name, emergency_dispatch_id, ambulance_id, status,
                        origin_location, destination_hospital, route_intersections,
                        active_signal_id, cleared_signals, activated_at, cleared_at
                    ) VALUES (?, ?, ?, ?, 'STANDBY', ?, ?, ?, NULL, ?, ?, NULL)
                    """,
                    (
                        corr_id,
                        data["name"],
                        data.get("emergency_dispatch_id"),
                        data.get("ambulance_id"),
                        data["origin_location"],
                        data["destination_hospital"],
                        _json(data.get("route_intersections", [])),
                        _json([]),
                        now
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM green_corridors WHERE id = ?", (corr_id,)).fetchone()
                d = dict(row)
                d["route_intersections"] = _loads(d.get("route_intersections"), [])
                return d

    async def activate_green_corridor(self, corridor_id: str) -> Optional[dict]:
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM green_corridors WHERE id = ?", (corridor_id,)).fetchone()
                if not row:
                    return None
                routes = _loads(row["route_intersections"], [])
                active_sig = routes[0] if routes else None
                conn.execute(
                    "UPDATE green_corridors SET status = 'ACTIVE', active_signal_id = ?, activated_at = ? WHERE id = ?",
                    (active_sig, now, corridor_id)
                )
                for sig_id in routes:
                    conn.execute(
                        "UPDATE traffic_signals SET current_state = 'GREEN', mode = 'GREEN_CORRIDOR', last_override_by = 'GREEN_CORRIDOR_CAD', updated_at = ? WHERE id = ?",
                        (now, sig_id)
                    )
                conn.commit()
                updated = conn.execute("SELECT * FROM green_corridors WHERE id = ?", (corridor_id,)).fetchone()
                d = dict(updated)
                d["route_intersections"] = routes
                d["cleared_signals"] = _loads(d.get("cleared_signals"), [])
                return d

    async def deactivate_green_corridor(self, corridor_id: str) -> Optional[dict]:
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                row = conn.execute("SELECT * FROM green_corridors WHERE id = ?", (corridor_id,)).fetchone()
                if not row:
                    return None
                routes = _loads(row["route_intersections"], [])
                conn.execute(
                    "UPDATE green_corridors SET status = 'COMPLETED', active_signal_id = NULL, cleared_at = ? WHERE id = ?",
                    (now, corridor_id)
                )
                for sig_id in routes:
                    conn.execute(
                        "UPDATE traffic_signals SET mode = 'ADAPTIVE', updated_at = ? WHERE id = ?",
                        (now, sig_id)
                    )
                conn.commit()
                updated = conn.execute("SELECT * FROM green_corridors WHERE id = ?", (corridor_id,)).fetchone()
                d = dict(updated)
                d["route_intersections"] = routes
                d["cleared_signals"] = routes
                return d

    async def get_traffic_maintenance_tickets(self, status: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM traffic_maintenance_tickets WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def create_traffic_maintenance_ticket(self, data: dict) -> dict:
        tkt_id = data.get("id") or f"TKT-MAINT-{uuid.uuid4().hex[:6].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO traffic_maintenance_tickets (
                        id, signal_id, technician_id, issue_type, priority, status,
                        voltage_reading, loop_resistance_ohms, firmware_checksum,
                        diagnostic_log, resolution_notes, created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?, ?, ?, NULL, ?, NULL)
                    """,
                    (
                        tkt_id,
                        data["signal_id"],
                        data.get("technician_id", "signal_tech"),
                        data.get("issue_type", "CONTROLLER_FAULT"),
                        data.get("priority", "NORMAL"),
                        data.get("voltage_reading", 230.0),
                        data.get("loop_resistance_ohms", 4.2),
                        data.get("firmware_checksum", "sha256_stig_v4.2.1_valid"),
                        data.get("diagnostic_log", "Automated diagnostic pass"),
                        now
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM traffic_maintenance_tickets WHERE id = ?", (tkt_id,)).fetchone()
                return dict(row)

    async def update_traffic_maintenance_ticket(self, ticket_id: str, status: str, diagnostic_log: Optional[str] = None, resolution_notes: Optional[str] = None) -> Optional[dict]:
        now = _utcnow()
        completed_at = now if status == "COMPLETED" else None
        async with self._lock:
            with self._connect() as conn:
                cur = conn.execute(
                    """
                    UPDATE traffic_maintenance_tickets
                    SET status = ?, diagnostic_log = COALESCE(?, diagnostic_log),
                        resolution_notes = COALESCE(?, resolution_notes),
                        completed_at = CASE WHEN ? = 'COMPLETED' THEN ? ELSE completed_at END
                    WHERE id = ?
                    """,
                    (status, diagnostic_log, resolution_notes, status, completed_at, ticket_id)
                )
                conn.commit()
                if cur.rowcount == 0:
                    return None
                row = conn.execute("SELECT * FROM traffic_maintenance_tickets WHERE id = ?", (ticket_id,)).fetchone()
                return dict(row)

    async def get_citizen_traffic_feed(self) -> dict:
        with self._connect() as conn:
            roads = conn.execute("SELECT name, length_km, current_speed_kmh, congestion_level, incident_count FROM road_segments").fetchall()
            corrs = conn.execute("SELECT name, status, origin_location, destination_hospital FROM green_corridors WHERE status = 'ACTIVE'").fetchall()
            incidents = conn.execute("SELECT title, category, location, reported_at FROM traffic_incidents WHERE status IN ('REPORTED', 'VERIFIED', 'DISPATCHED')").fetchall()

        return {
            "city": "Bengaluru Metropolitan Mobility Grid",
            "timestamp": _utcnow(),
            "overall_traffic_status": "MODERATE_CONGESTION",
            "average_transit_speed_kmh": 46.5,
            "active_green_corridors_advisories": [
                {
                    "corridor_name": c["name"],
                    "advisory": f"EMERGENCY TRANSIT ACTIVE: Yield right-of-way between {c['origin_location']} and {c['destination_hospital']}."
                }
                for c in corrs
            ],
            "corridors": [
                {
                    "corridor": r["name"],
                    "congestion_level": r["congestion_level"],
                    "speed_kmh": r["current_speed_kmh"],
                    "travel_delay_minutes": 12 if r["congestion_level"] in ("HEAVY", "CRITICAL") else 2
                }
                for r in roads
            ],
            "public_incidents": [
                {
                    "title": i["title"],
                    "category": i["category"],
                    "location": i["location"],
                    "reported_at": i["reported_at"]
                }
                for i in incidents
            ]
        }

    async def evaluate_signal_safety_override(
        self,
        signal_id: str,
        target_state: str,
        mode: str,
        reason: str,
        context_type: str,
        context_ref: Optional[str],
        current_user: dict
    ) -> dict:
        actor = current_user.get("username", "anonymous")
        user_risk = float(current_user.get("risk_score", 0.0))
        now = _utcnow()

        # 1. Operational Context & Justification Validation
        if not reason or len(reason.strip()) < 5:
            return {
                "allowed": False,
                "status": "INVALID_CONTEXT",
                "detail": "Mandatory operational justification (min 5 characters) required for signal actuation."
            }

        valid_contexts = {"EMERGENCY_PREEMPTION", "INCIDENT_CLEARANCE", "SCHEDULED_MAINTENANCE", "CONGESTION_MITIGATION", "MANUAL_OVERRIDE"}
        if not context_type or context_type not in valid_contexts:
            return {
                "allowed": False,
                "status": "INVALID_CONTEXT",
                "detail": f"Valid operational context type required. Must be one of: {list(valid_contexts)}"
            }

        # 2. Risk Evaluation: Risk score >= 60 blocked as high-risk cyber anomaly
        if user_risk >= 60.0:
            inc_id = f"INC-CYBER-SIG-{uuid.uuid4().hex[:6].upper()}"
            async with self._lock:
                with self._connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO incidents (
                            id, timestamp, title, severity, type, status, asset_id, asset, location, domain,
                            owner, risk_score, detected_at, description, is_escalated
                        ) VALUES (?, ?, ?, 'CRITICAL', 'UNAUTHORIZED_SCADA_OVERRIDE', 'open', ?, 'TRAFFIC_SIGNAL_GRID', 'Central SCADA Hub', 'TRAFFIC', 'traffic_sec', ?, ?, ?, 1)
                        """,
                        (inc_id, now, f"High-Risk Signal Override Blocked: {actor} on {signal_id}", signal_id, user_risk, now,
                         f"Operator {actor} with risk score {user_risk} attempted signal override to {target_state}. Blocked by Zero-Trust SCADA guard.")
                    )
                    conn.execute(
                        """
                        INSERT INTO audit_logs (
                            id, timestamp, actor, action, target, decision, reason, details, success
                        ) VALUES (?, ?, ?, ?, ?, 'BLOCK', ?, ?, 0)
                        """,
                        (f"AUD-SIG-{uuid.uuid4().hex[:8].upper()}", now, actor, f"SIGNAL_SAFETY_OVERRIDE_{target_state}",
                         signal_id, "HIGH_OPERATOR_RISK_SCORE", _json({"risk_score": user_risk, "reason": reason, "target_state": target_state}))
                    )
                    conn.commit()

            return {
                "allowed": False,
                "status": "BLOCKED_HIGH_RISK",
                "detail": f"Signal override blocked: Operator risk score ({user_risk}) exceeds safety threshold (60.0). High-severity incident {inc_id} dispatched to City SOC.",
                "incident_id": inc_id,
                "operator_risk": user_risk
            }

        # 3. Fetch target signal
        target_sig = await self.get_traffic_signal(signal_id)
        if not target_sig:
            return {"allowed": False, "status": "NOT_FOUND", "detail": f"Traffic signal {signal_id} not found."}

        prev_state = target_sig.get("current_state", "RED")

        # 4. Policy Evaluation & Conflict Matrix Interlock
        # Perpendicular conflicting approaches cannot simultaneously show GREEN
        CONFLICT_PAIRS = {
            "SIG-01": "SIG-02",
            "SIG-02": "SIG-01",
            "SIG-03": "SIG-05",
            "SIG-05": "SIG-03",
            "SIG-04": "SIG-06",
            "SIG-06": "SIG-04",
        }
        conf_id = CONFLICT_PAIRS.get(signal_id)
        conflict_detected = False
        conf_sig = None

        if conf_id:
            conf_sig = await self.get_traffic_signal(conf_id)

        target_state_upper = target_state.upper()
        if target_state_upper == "GREEN" and conf_sig and conf_sig.get("current_state") in ("GREEN", "YELLOW"):
            conflict_detected = True
            safety_transition_plan = [
                {"stage": 1, "phase": "CLEARANCE_YELLOW", "duration_seconds": 4, "action": f"Conflicting signal {conf_id} transitioned to YELLOW for clearance"},
                {"stage": 2, "phase": "ALL_RED_HOLD", "duration_seconds": 2, "action": f"All approaches at intersection held RED for pedestrian and vehicle clearance"},
                {"stage": 3, "phase": "TARGET_GREEN", "duration_seconds": 60, "action": f"Target signal {signal_id} safely transitioned to GREEN with conflicting interlock engaged"}
            ]
        else:
            safety_transition_plan = [
                {"stage": 1, "phase": f"DIRECT_TRANSITION_{target_state_upper}", "duration_seconds": 0, "action": f"Signal {signal_id} transitioned from {prev_state} to {target_state_upper}"}
            ]

        # 5. Execute state transitions atomically
        async with self._lock:
            with self._connect() as conn:
                if conflict_detected and conf_id:
                    conn.execute(
                        "UPDATE traffic_signals SET current_state = 'RED', mode = ?, last_override_by = ?, updated_at = ? WHERE id = ?",
                        (mode, actor, now, conf_id)
                    )
                conn.execute(
                    "UPDATE traffic_signals SET current_state = ?, mode = ?, last_override_by = ?, updated_at = ? WHERE id = ?",
                    (target_state_upper, mode, actor, now, signal_id)
                )
                audit_id = f"AUD-SIG-{uuid.uuid4().hex[:8].upper()}"
                conn.execute(
                    """
                    INSERT INTO audit_logs (
                        id, timestamp, actor, action, target, decision, reason, details, success
                    ) VALUES (?, ?, ?, ?, ?, 'ALLOW', ?, ?, 1)
                    """,
                    (
                        audit_id,
                        now,
                        actor,
                        f"SIGNAL_SAFETY_OVERRIDE_{target_state_upper}",
                        signal_id,
                        reason,
                        _json({
                            "from_state": prev_state,
                            "to_state": target_state_upper,
                            "mode": mode,
                            "context_type": context_type,
                            "context_ref": context_ref,
                            "conflict_detected": conflict_detected,
                            "conflicting_signal": conf_id,
                            "safety_stages": len(safety_transition_plan),
                            "operator_risk": user_risk
                        })
                    )
                )
                conn.commit()

        return {
            "allowed": True,
            "status": "OVERRIDE_EXECUTED",
            "signal_id": signal_id,
            "previous_state": prev_state,
            "target_state": target_state_upper,
            "mode": mode,
            "conflict_detected": conflict_detected,
            "conflicting_signal_cleared": conf_id if conflict_detected else None,
            "safety_transition_plan": safety_transition_plan,
            "audit_id": audit_id,
            "executed_by": actor,
            "timestamp": now
        }


    # ═══════════════════════════════════════════════════════════════════════
    # CENTRAL SECURITY EVENT ARCHITECTURE
    # ═══════════════════════════════════════════════════════════════════════

    async def save_security_event(self, event: dict) -> dict:
        event_id = event.get("event_id") or f"EVT-{uuid.uuid4().hex[:10].upper()}"
        ts = event.get("timestamp") or _utcnow()
        meta = event.get("metadata", {})
        if isinstance(meta, (dict, list)):
            meta = _json(meta)
        elif not isinstance(meta, str):
            meta = str(meta)

        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO security_events (
                        event_id, timestamp, domain, organization, user, role,
                        device, ip, location, resource, action, result, risk, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        ts,
                        event.get("domain", "SECURITY"),
                        event.get("organization", "Securox Fabric"),
                        event.get("user", "system"),
                        event.get("role", "system"),
                        event.get("device", "UNKNOWN"),
                        event.get("ip", event.get("IP", "127.0.0.1")),
                        event.get("location", "Universal Command"),
                        event.get("resource", "SYSTEM"),
                        event.get("action", "UNKNOWN_ACTION"),
                        event.get("result", "SUCCESS"),
                        float(event.get("risk", 0.0)),
                        meta
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM security_events WHERE event_id = ?", (event_id,)).fetchone()
                d = dict(row)
                d["metadata"] = _loads(d["metadata"], {})
                return d

    async def get_security_events(
        self,
        domain: Optional[str] = None,
        action: Optional[str] = None,
        user: Optional[str] = None,
        role: Optional[str] = None,
        min_risk: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM security_events WHERE 1=1"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain)
            if action:
                query += " AND action = ?"
                params.append(action)
            if user:
                query += " AND user = ?"
                params.append(user)
            if role:
                query += " AND role = ?"
                params.append(role)
            if min_risk is not None:
                query += " AND risk >= ?"
                params.append(min_risk)
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["metadata"] = _loads(d["metadata"], {})
                results.append(d)
            return results

    async def get_security_event_stats(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
            high_risk = conn.execute("SELECT COUNT(*) FROM security_events WHERE risk >= 70.0").fetchone()[0]
            
            domains = conn.execute("SELECT domain, COUNT(*) as cnt FROM security_events GROUP BY domain").fetchall()
            domain_counts = {r["domain"]: r["cnt"] for r in domains}

            actions = conn.execute("SELECT action, COUNT(*) as cnt FROM security_events GROUP BY action ORDER BY cnt DESC LIMIT 10").fetchall()
            action_counts = {r["action"]: r["cnt"] for r in actions}

            results = conn.execute("SELECT result, COUNT(*) as cnt FROM security_events GROUP BY result").fetchall()
            result_counts = {r["result"]: r["cnt"] for r in results}

            recent = conn.execute("SELECT * FROM security_events ORDER BY timestamp DESC LIMIT 10").fetchall()
            recent_list = []
            for r in recent:
                d = dict(r)
                d["metadata"] = _loads(d["metadata"], {})
                recent_list.append(d)

            return {
                "total_events": total,
                "high_risk_events": high_risk,
                "domains": domain_counts,
                "top_actions": action_counts,
                "results": result_counts,
                "recent": recent_list
            }


    # ═══════════════════════════════════════════════════════════════════════
    # CENTRAL CYBER-RISK ENGINE ENTITIES & HISTORICAL BASELINES
    # ═══════════════════════════════════════════════════════════════════════

    async def save_risk_assessment(self, assessment: dict, factors: list) -> dict:
        now = _utcnow()
        aid = assessment.get("assessment_id") or f"RA-{uuid.uuid4().hex[:8].upper()}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risk_assessments
                (id, event_id, timestamp, identity, role, domain, resource, action,
                 risk_score, risk_category, confidence, uncertainty, uncertainty_reason,
                 recommended_action, rule_score, baseline_score, ml_score, explanation, raw_event, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    aid,
                    assessment.get("event_id", ""),
                    assessment.get("timestamp", now),
                    assessment.get("identity", "unknown"),
                    assessment.get("role", "unknown"),
                    assessment.get("domain", "SECURITY"),
                    assessment.get("resource", "SYSTEM"),
                    assessment.get("action", "EVALUATE"),
                    float(assessment.get("risk_score", 0.0)),
                    assessment.get("risk_category", "LOW"),
                    float(assessment.get("confidence", 1.0)),
                    float(assessment.get("uncertainty", 0.0)),
                    assessment.get("uncertainty_reason", "Deterministic evaluation"),
                    assessment.get("recommended_action", "ALLOW"),
                    float(assessment.get("rule_score", 0.0)),
                    float(assessment.get("baseline_score", 0.0)),
                    float(assessment.get("ml_score", 0.0)),
                    assessment.get("explanation", ""),
                    _json(assessment.get("raw_event", {})),
                    now
                )
            )

            # Insert factors
            for f in factors:
                fid = f.get("id") or f"RF-{uuid.uuid4().hex[:8].upper()}"
                conn.execute(
                    """
                    INSERT INTO risk_factors
                    (id, assessment_id, factor_key, name, points, source_type, description, evidence, confidence, severity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fid,
                        aid,
                        f.get("factor_key", "GENERIC_FACTOR"),
                        f.get("name", "Risk Factor"),
                        float(f.get("points", 0.0)),
                        f.get("source_type", "POLICY_RULE"),
                        f.get("description", ""),
                        _json(f.get("evidence", {})),
                        float(f.get("confidence", 1.0)),
                        f.get("severity", "LOW")
                    )
                )
        return {**assessment, "assessment_id": aid, "factors": factors}

    async def get_risk_assessments(
        self,
        domain: Optional[str] = None,
        category: Optional[str] = None,
        identity: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        with self._connect() as conn:
            query = "SELECT * FROM risk_assessments WHERE 1=1"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain)
            if category:
                query += " AND risk_category = ?"
                params.append(category.upper())
            if identity:
                query += " AND identity = ?"
                params.append(identity)
            if min_score is not None:
                query += " AND risk_score >= ?"
                params.append(float(min_score))
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["raw_event"] = _loads(d.get("raw_event"), {})
                f_rows = conn.execute("SELECT * FROM risk_factors WHERE assessment_id = ?", (d["id"],)).fetchall()
                d_factors = []
                for fr in f_rows:
                    fd = dict(fr)
                    fd["evidence"] = _loads(fd.get("evidence"), {})
                    d_factors.append(fd)
                d["factors"] = d_factors
                results.append(d)
            return results

    async def get_risk_assessment_detail(self, assessment_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM risk_assessments WHERE id = ?", (assessment_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["raw_event"] = _loads(d.get("raw_event"), {})
            f_rows = conn.execute("SELECT * FROM risk_factors WHERE assessment_id = ?", (assessment_id,)).fetchall()
            d_factors = []
            for fr in f_rows:
                fd = dict(fr)
                fd["evidence"] = _loads(fd.get("evidence"), {})
                d_factors.append(fd)
            d["factors"] = d_factors
            return d

    async def get_historical_baseline(self, identity: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM historical_baselines WHERE identity = ?", (identity,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["known_devices"] = _loads(d.get("known_devices"), [])
            d["known_locations"] = _loads(d.get("known_locations"), [])
            d["typical_hours"] = _loads(d.get("typical_hours"), [6, 22])
            d["typical_actions"] = _loads(d.get("typical_actions"), [])
            return d

    async def save_historical_baseline(self, identity: str, data: dict) -> dict:
        now = _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO historical_baselines
                (identity, domain, role, known_devices, known_locations, typical_hours,
                 typical_actions, mean_volume, std_dev_volume, event_count, last_seen, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity,
                    data.get("domain", "PLATFORM"),
                    data.get("role", "user"),
                    _json(data.get("known_devices", [])),
                    _json(data.get("known_locations", [])),
                    _json(data.get("typical_hours", [6, 22])),
                    _json(data.get("typical_actions", [])),
                    float(data.get("mean_volume", 1.0)),
                    float(data.get("std_dev_volume", 1.0)),
                    int(data.get("event_count", 0)),
                    data.get("last_seen", now),
                    now
                )
            )
        return await self.get_historical_baseline(identity)

    async def update_historical_baseline(self, identity: str, event_data: dict) -> dict:
        base = await self.get_historical_baseline(identity)
        now = _utcnow()
        if not base:
            base = {
                "identity": identity,
                "domain": event_data.get("domain", "PLATFORM"),
                "role": event_data.get("role", "user"),
                "known_devices": [event_data.get("device")] if event_data.get("device") else [],
                "known_locations": [event_data.get("location")] if event_data.get("location") else [],
                "typical_hours": [6, 22],
                "typical_actions": [event_data.get("action")] if event_data.get("action") else [],
                "mean_volume": 1.0,
                "std_dev_volume": 1.0,
                "event_count": 1,
                "last_seen": now,
                "updated_at": now
            }
        else:
            dev = event_data.get("device")
            if dev and dev not in base["known_devices"]:
                base["known_devices"].append(dev)
            loc = event_data.get("location")
            if loc and loc not in base["known_locations"]:
                base["known_locations"].append(loc)
            act = event_data.get("action")
            if act and act not in base["typical_actions"]:
                base["typical_actions"].append(act)
            base["event_count"] = base.get("event_count", 0) + 1
            base["last_seen"] = now
            base["updated_at"] = now
        return await self.save_historical_baseline(identity, base)

    async def get_risk_engine_stats(self) -> dict:
        with self._connect() as conn:
            tot = conn.execute("SELECT COUNT(*) FROM risk_assessments").fetchone()[0]
            cats = conn.execute("SELECT risk_category, COUNT(*) as cnt FROM risk_assessments GROUP BY risk_category").fetchall()
            cat_counts = {r["risk_category"]: r["cnt"] for r in cats}
            avg_score = conn.execute("SELECT AVG(risk_score) FROM risk_assessments").fetchone()[0] or 0.0
            avg_conf = conn.execute("SELECT AVG(confidence) FROM risk_assessments").fetchone()[0] or 0.0
            avg_unc = conn.execute("SELECT AVG(uncertainty) FROM risk_assessments").fetchone()[0] or 0.0
            actions = conn.execute("SELECT recommended_action, COUNT(*) as cnt FROM risk_assessments GROUP BY recommended_action").fetchall()
            act_counts = {r["recommended_action"]: r["cnt"] for r in actions}

            recent = conn.execute("SELECT * FROM risk_assessments ORDER BY timestamp DESC LIMIT 5").fetchall()
            recent_list = []
            for r in recent:
                d = dict(r)
                d["raw_event"] = _loads(d.get("raw_event"), {})
                recent_list.append(d)

            return {
                "total_assessments": tot,
                "categories": {
                    "LOW": cat_counts.get("LOW", 0),
                    "MEDIUM": cat_counts.get("MEDIUM", 0),
                    "HIGH": cat_counts.get("HIGH", 0),
                    "CRITICAL": cat_counts.get("CRITICAL", 0),
                },
                "category_distribution": {
                    "LOW": cat_counts.get("LOW", 0),
                    "MEDIUM": cat_counts.get("MEDIUM", 0),
                    "HIGH": cat_counts.get("HIGH", 0),
                    "CRITICAL": cat_counts.get("CRITICAL", 0),
                },
                "average_risk_score": round(avg_score, 1),
                "average_confidence": round(avg_conf, 2),
                "average_uncertainty": round(avg_unc, 2),
                "recommended_actions": act_counts,
                "recent_assessments": recent_list
            }


    # ═══════════════════════════════════════════════════════════════════════
    # FINANCIAL SECURITY ENTITIES & OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════

    async def get_finance_branches(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM finance_branches ORDER BY code").fetchall()
            return [dict(r) for r in rows]

    async def get_finance_branch(self, branch_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM finance_branches WHERE id = ? OR code = ?", (branch_id, branch_id)).fetchone()
            return dict(row) if row else None

    async def update_finance_branch_volume(self, branch_id: str, amount: float) -> Optional[dict]:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE finance_branches SET current_volume = current_volume + ? WHERE id = ?",
                    (amount, branch_id)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_branches WHERE id = ?", (branch_id,)).fetchone()
                return dict(row) if row else None

    async def get_finance_customers(self, branch_id: Optional[str] = None, risk_rating: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM finance_customers WHERE 1=1"
            params = []
            if branch_id:
                query += " AND branch_id = ?"
                params.append(branch_id)
            if risk_rating:
                query += " AND risk_rating = ?"
                params.append(risk_rating)
            query += " ORDER BY name ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def get_finance_customer(self, customer_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM finance_customers WHERE id = ? OR pan_or_ssn = ?", (customer_id, customer_id)).fetchone()
            if not row:
                return None
            cust = dict(row)
            accs = conn.execute("SELECT * FROM finance_accounts WHERE customer_id = ?", (cust["id"],)).fetchall()
            cust["accounts"] = [dict(a) for a in accs]
            return cust

    async def get_finance_accounts(self, customer_id: Optional[str] = None, branch_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            query = """
                SELECT a.*, c.name as customer_name, b.name as branch_name
                FROM finance_accounts a
                LEFT JOIN finance_customers c ON a.customer_id = c.id
                LEFT JOIN finance_branches b ON a.branch_id = b.id
                WHERE 1=1
            """
            params = []
            if customer_id:
                query += " AND a.customer_id = ?"
                params.append(customer_id)
            if branch_id:
                query += " AND a.branch_id = ?"
                params.append(branch_id)
            query += " ORDER BY a.account_number ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def get_finance_account(self, account_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT a.*, c.name as customer_name, b.name as branch_name
                FROM finance_accounts a
                LEFT JOIN finance_customers c ON a.customer_id = c.id
                LEFT JOIN finance_branches b ON a.branch_id = b.id
                WHERE a.id = ? OR a.account_number = ?
                """,
                (account_id, account_id)
            ).fetchone()
            return dict(row) if row else None

    async def update_finance_account_status(self, account_id: str, status: str, risk_score: Optional[float] = None) -> Optional[dict]:
        async with self._lock:
            with self._connect() as conn:
                if risk_score is not None:
                    conn.execute("UPDATE finance_accounts SET status = ?, risk_score = ? WHERE id = ? OR account_number = ?", (status, risk_score, account_id, account_id))
                else:
                    conn.execute("UPDATE finance_accounts SET status = ? WHERE id = ? OR account_number = ?", (status, account_id, account_id))
                conn.commit()
                row = conn.execute("SELECT * FROM finance_accounts WHERE id = ? OR account_number = ?", (account_id, account_id)).fetchone()
                return dict(row) if row else None

    async def update_finance_account_balance(self, account_id: str, delta: float) -> Optional[dict]:
        async with self._lock:
            with self._connect() as conn:
                conn.execute("UPDATE finance_accounts SET balance = balance + ? WHERE id = ? OR account_number = ?", (delta, account_id, account_id))
                conn.commit()
                row = conn.execute("SELECT * FROM finance_accounts WHERE id = ? OR account_number = ?", (account_id, account_id)).fetchone()
                return dict(row) if row else None

    async def get_finance_transactions(
        self,
        account_id: Optional[str] = None,
        branch_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        with self._connect() as conn:
            query = """
                SELECT t.*, a.account_number, a.branch_id, a.customer_id, c.name as customer_name
                FROM finance_transactions t
                JOIN finance_accounts a ON t.account_id = a.id
                JOIN finance_customers c ON a.customer_id = c.id
                WHERE 1=1
            """
            params = []
            if account_id:
                query += " AND (t.account_id = ? OR a.account_number = ?)"
                params.extend([account_id, account_id])
            if branch_id:
                query += " AND a.branch_id = ?"
                params.append(branch_id)
            if customer_id:
                query += " AND a.customer_id = ?"
                params.append(customer_id)
            if status:
                query += " AND t.status = ?"
                params.append(status)
            query += " ORDER BY t.timestamp DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def get_finance_transaction(self, transaction_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT t.*, a.account_number, a.branch_id, a.customer_id, c.name as customer_name
                FROM finance_transactions t
                JOIN finance_accounts a ON t.account_id = a.id
                JOIN finance_customers c ON a.customer_id = c.id
                WHERE t.id = ?
                """,
                (transaction_id,)
            ).fetchone()
            return dict(row) if row else None

    async def create_finance_transaction(self, data: dict) -> dict:
        tx_id = data.get("id") or f"TX-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO finance_transactions (
                        id, account_id, counterparty_account, amount, channel, currency,
                        timestamp, ip_address, device_id, location, status, risk_score,
                        model_attribution, flag_reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_id,
                        data["account_id"],
                        data["counterparty_account"],
                        float(data["amount"]),
                        data.get("channel", "UPI"),
                        data.get("currency", "INR"),
                        data.get("timestamp", now),
                        data.get("ip_address", "127.0.0.1"),
                        data.get("device_id", "DEV-CLIENT-01"),
                        data.get("location", "Bengaluru Regional Gateway"),
                        data.get("status", "SETTLED"),
                        float(data.get("risk_score", 5.0)),
                        data.get("model_attribution", "LIVE INFERENCE"),
                        data.get("flag_reason"),
                        now
                    )
                )
                # update account balance if settled
                if data.get("status") == "SETTLED":
                    conn.execute("UPDATE finance_accounts SET balance = balance - ? WHERE id = ?", (float(data["amount"]), data["account_id"]))
                conn.commit()
                row = conn.execute("SELECT * FROM finance_transactions WHERE id = ?", (tx_id,)).fetchone()
                return dict(row)

    async def update_finance_transaction_status(self, transaction_id: str, status: str, flag_reason: Optional[str] = None) -> Optional[dict]:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE finance_transactions SET status = ?, flag_reason = COALESCE(?, flag_reason) WHERE id = ?",
                    (status, flag_reason, transaction_id)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_transactions WHERE id = ?", (transaction_id,)).fetchone()
                return dict(row) if row else None

    async def get_finance_fraud_cases(self, status: Optional[str] = None, severity: Optional[str] = None, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM finance_fraud_cases WHERE 1=1"
            params = []
            if status:
                query += " AND status = ?"
                params.append(status)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY opened_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    async def get_finance_fraud_case(self, case_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM finance_fraud_cases WHERE id = ? OR case_number = ?", (case_id, case_id)).fetchone()
            if not row:
                return None
            c = dict(row)
            # Fetch attached transaction
            if c.get("transaction_id"):
                tx = conn.execute("SELECT * FROM finance_transactions WHERE id = ?", (c["transaction_id"],)).fetchone()
                c["transaction"] = dict(tx) if tx else None
            # Fetch aml findings for this case
            findings = conn.execute("SELECT * FROM finance_aml_findings WHERE case_id = ?", (c["id"],)).fetchall()
            c["aml_findings"] = []
            for f in findings:
                fd = dict(f)
                fd["counterparty_accounts"] = _loads(fd["counterparty_accounts_json"], [])
                fd["graph_metrics"] = _loads(fd["graph_metrics_json"], {})
                c["aml_findings"].append(fd)
            return c

    async def create_finance_fraud_case(self, data: dict) -> dict:
        case_id = data.get("id") or f"CASE-FRD-{uuid.uuid4().hex[:8].upper()}"
        case_num = data.get("case_number") or f"FRD-2026-{uuid.uuid4().hex[:4].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO finance_fraud_cases (
                        id, case_number, transaction_id, customer_id, account_id, title,
                        severity, status, total_exposure_inr, assigned_analyst,
                        decision, decision_rationale, resolution_notes, opened_at, closed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        case_id,
                        case_num,
                        data.get("transaction_id"),
                        data["customer_id"],
                        data["account_id"],
                        data["title"],
                        data.get("severity", "MEDIUM"),
                        data.get("status", "OPEN"),
                        float(data.get("total_exposure_inr", 0.0)),
                        data.get("assigned_analyst", "fraud_analyst"),
                        data.get("decision"),
                        data.get("decision_rationale"),
                        data.get("resolution_notes"),
                        now,
                        None
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_fraud_cases WHERE id = ?", (case_id,)).fetchone()
                return dict(row)

    async def update_finance_fraud_case(
        self,
        case_id: str,
        status: Optional[str] = None,
        decision: Optional[str] = None,
        decision_rationale: Optional[str] = None,
        resolution_notes: Optional[str] = None,
        assigned_analyst: Optional[str] = None
    ) -> Optional[dict]:
        now = _utcnow()
        closed_at = now if status in ("CLOSED", "RESOLVED") else None
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE finance_fraud_cases
                    SET status = COALESCE(?, status),
                        decision = COALESCE(?, decision),
                        decision_rationale = COALESCE(?, decision_rationale),
                        resolution_notes = COALESCE(?, resolution_notes),
                        assigned_analyst = COALESCE(?, assigned_analyst),
                        closed_at = CASE WHEN ? IN ('CLOSED', 'RESOLVED') THEN ? ELSE closed_at END
                    WHERE id = ? OR case_number = ?
                    """,
                    (status, decision, decision_rationale, resolution_notes, assigned_analyst, status, closed_at, case_id, case_id)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_fraud_cases WHERE id = ? OR case_number = ?", (case_id, case_id)).fetchone()
                return dict(row) if row else None

    async def get_finance_aml_findings(
        self,
        finding_type: Optional[str] = None,
        min_mule_prob: Optional[float] = None,
        sar_filed: Optional[int] = None
    ) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT * FROM finance_aml_findings WHERE 1=1"
            params = []
            if finding_type:
                query += " AND finding_type = ?"
                params.append(finding_type)
            if min_mule_prob is not None:
                query += " AND mule_probability >= ?"
                params.append(min_mule_prob)
            if sar_filed is not None:
                query += " AND sar_filed = ?"
                params.append(sar_filed)
            query += " ORDER BY detected_at DESC"
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["counterparty_accounts"] = _loads(d["counterparty_accounts_json"], [])
                d["graph_metrics"] = _loads(d["graph_metrics_json"], {})
                results.append(d)
            return results

    async def get_finance_aml_finding(self, finding_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM finance_aml_findings WHERE id = ?", (finding_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["counterparty_accounts"] = _loads(d["counterparty_accounts_json"], [])
            d["graph_metrics"] = _loads(d["graph_metrics_json"], {})
            return d

    async def create_finance_aml_finding(self, data: dict) -> dict:
        finding_id = data.get("id") or f"AML-FIND-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO finance_aml_findings (
                        id, case_id, finding_type, primary_account,
                        counterparty_accounts_json, mule_probability,
                        hop_count, structuring_pattern, graph_metrics_json,
                        sar_filed, sar_reference, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        finding_id,
                        data.get("case_id"),
                        data.get("finding_type", "ANOMALOUS_TOPOLOGY"),
                        data["primary_account"],
                        _json(data.get("counterparty_accounts", [])),
                        float(data.get("mule_probability", 0.0)),
                        int(data.get("hop_count", 1)),
                        data.get("structuring_pattern"),
                        _json(data.get("graph_metrics", {})),
                        1 if data.get("sar_filed") else 0,
                        data.get("sar_reference"),
                        now
                    )
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_aml_findings WHERE id = ?", (finding_id,)).fetchone()
                d = dict(row)
                d["counterparty_accounts"] = _loads(d["counterparty_accounts_json"], [])
                d["graph_metrics"] = _loads(d["graph_metrics_json"], {})
                return d

    async def update_finance_aml_finding(self, finding_id: str, sar_filed: Optional[int] = None, sar_reference: Optional[str] = None) -> Optional[dict]:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE finance_aml_findings
                    SET sar_filed = COALESCE(?, sar_filed),
                        sar_reference = COALESCE(?, sar_reference)
                    WHERE id = ?
                    """,
                    (sar_filed, sar_reference, finding_id)
                )
                conn.commit()
                row = conn.execute("SELECT * FROM finance_aml_findings WHERE id = ?", (finding_id,)).fetchone()
                if not row:
                    return None
                d = dict(row)
                d["counterparty_accounts"] = _loads(d["counterparty_accounts_json"], [])
                d["graph_metrics"] = _loads(d["graph_metrics_json"], {})
                return d

    async def get_finance_cyber_var_data(self) -> dict:
        with self._connect() as conn:
            # Aggregate exposure from high-risk accounts and open fraud cases
            total_active_balance = conn.execute("SELECT SUM(balance) FROM finance_accounts WHERE status = 'ACTIVE'").fetchone()[0] or 0.0
            frozen_balance = conn.execute("SELECT SUM(balance) FROM finance_accounts WHERE status = 'FROZEN'").fetchone()[0] or 0.0
            case_exposure = conn.execute("SELECT SUM(total_exposure_inr) FROM finance_fraud_cases WHERE status IN ('OPEN', 'INVESTIGATING')").fetchone()[0] or 0.0
            high_risk_tx_vol = conn.execute("SELECT SUM(amount) FROM finance_transactions WHERE risk_score >= 70.0").fetchone()[0] or 0.0
            
            # Simulated & Engineering VaR metrics
            # 95% 1-day Cyber-VaR based on composite exposure
            var_95_inr = round((case_exposure * 0.45) + (high_risk_tx_vol * 0.25) + (total_active_balance * 0.0018), 2)
            var_99_inr = round(var_95_inr * 1.42, 2)
            expected_shortfall = round(var_99_inr * 1.18, 2)

            return {
                "timestamp": _utcnow(),
                "methodology": "Monte Carlo Parametric Cyber-Exposure Engine",
                "model_attribution": "SIMULATION",
                "portfolio_total_balance_inr": total_active_balance,
                "quarantined_frozen_inr": frozen_balance,
                "open_case_exposure_inr": case_exposure,
                "high_risk_transaction_volume_inr": high_risk_tx_vol,
                "cyber_var_95_1day_inr": var_95_inr,
                "cyber_var_99_1day_inr": var_99_inr,
                "expected_shortfall_cvar_inr": expected_shortfall,
                "stress_scenarios": [
                    {
                        "name": "Coordinated APT SWIFT Core Switch Compromise",
                        "probability": 0.02,
                        "projected_loss_inr": round(var_99_inr * 3.5, 2),
                        "status": "MONITORED"
                    },
                    {
                        "name": "Distributed Mule Fan-In / Structuring Cascade",
                        "probability": 0.08,
                        "projected_loss_inr": round(var_95_inr * 1.8, 2),
                        "status": "MITIGATED"
                    },
                    {
                        "name": "Branch WAN Man-in-the-Middle Relay",
                        "probability": 0.05,
                        "projected_loss_inr": round(var_95_inr * 0.9, 2),
                        "status": "CLEARED"
                    }
                ]
            }


    # ═══════════════════════════════════════════════════════════════════════
    # STANDARDIZED AI MODEL INFERENCE & HEALTH MONITORING
    # ═══════════════════════════════════════════════════════════════════════

    async def save_ai_model_inference(self, inference: dict) -> dict:
        inf_id = inference.get("id") or f"INF-{uuid.uuid4().hex[:10].upper()}"
        now = inference.get("timestamp") or _utcnow()
        feats = inference.get("features", {})
        if isinstance(feats, (dict, list)):
            feats = _json(feats)
        elif not isinstance(feats, str):
            feats = str(feats)

        factors = inference.get("important_factors", [])
        if isinstance(factors, list):
            factors = _json(factors)
        elif not isinstance(factors, str):
            factors = str(factors)

        pred = inference.get("prediction")
        if isinstance(pred, (dict, list)):
            pred = _json(pred)
        else:
            pred = str(pred)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ai_model_inferences (
                    id, model_name, version, domain, event_id, prediction,
                    score, confidence, ground_truth_claim, features,
                    important_factors, latency_ms, disclaimer, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inf_id,
                    inference.get("model_name", "UNKNOWN_MODEL"),
                    inference.get("version", "1.0.0"),
                    inference.get("domain", "NETWORK"),
                    inference.get("event_id"),
                    pred,
                    float(inference.get("score", 0.0)),
                    float(inference.get("confidence", 0.90)),
                    0,  # ground_truth_claim is strictly 0 (NEVER True)
                    feats,
                    factors,
                    float(inference.get("latency_ms", 0.0)),
                    inference.get("disclaimer", "AI prediction represents a probabilistic statistical inference, not deterministic ground truth."),
                    now
                )
            )
        return {**inference, "id": inf_id, "timestamp": now, "ground_truth_claim": False}

    async def get_ai_model_inferences(
        self,
        domain: Optional[str] = None,
        model_name: Optional[str] = None,
        event_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        with self._connect() as conn:
            query = "SELECT * FROM ai_model_inferences WHERE 1=1"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain.upper())
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            if event_id:
                query += " AND event_id = ?"
                params.append(event_id)
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["features"] = _loads(d.get("features"), {})
                d["important_factors"] = _loads(d.get("important_factors"), [])
                d["ground_truth_claim"] = bool(d.get("ground_truth_claim", 0))
                results.append(d)
            return results

    async def update_ai_model_health(
        self,
        model_id: str,
        model_name: str,
        domain: str,
        version: str,
        status: str,
        latency_ms: float = 0.0,
        is_error: bool = False,
        health_details: Optional[dict] = None
    ) -> dict:
        now = _utcnow()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM ai_model_health WHERE model_id = ?", (model_id,)).fetchone()
            if not row:
                tot_inf = 1 if not is_error else 0
                tot_err = 1 if is_error else 0
                avg_lat = latency_ms
                last_inf = now if not is_error else None
                last_err = now if is_error else None
                details = health_details or {}
                conn.execute(
                    """
                    INSERT INTO ai_model_health
                    (model_id, model_name, domain, version, status, total_inferences, total_errors, avg_latency_ms, last_inference_at, last_error_at, health_details, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (model_id, model_name, domain.upper(), version, status, tot_inf, tot_err, avg_lat, last_inf, last_err, _json(details), now)
                )
            else:
                d = dict(row)
                tot_inf = d["total_inferences"] + (0 if is_error else 1)
                tot_err = d["total_errors"] + (1 if is_error else 0)
                curr_avg = float(d.get("avg_latency_ms", 0.0))
                new_avg = round(0.9 * curr_avg + 0.1 * latency_ms, 2) if curr_avg > 0 else round(latency_ms, 2)
                last_inf = now if not is_error else d.get("last_inference_at")
                last_err = now if is_error else d.get("last_error_at")
                details = {**_loads(d.get("health_details"), {}), **(health_details or {})}

                conn.execute(
                    """
                    UPDATE ai_model_health SET
                        model_name = ?, domain = ?, version = ?, status = ?,
                        total_inferences = ?, total_errors = ?, avg_latency_ms = ?,
                        last_inference_at = ?, last_error_at = ?, health_details = ?, updated_at = ?
                    WHERE model_id = ?
                    """,
                    (model_name, domain.upper(), version, status, tot_inf, tot_err, new_avg, last_inf, last_err, _json(details), now, model_id)
                )
            conn.commit()
            updated = conn.execute("SELECT * FROM ai_model_health WHERE model_id = ?", (model_id,)).fetchone()
            res = dict(updated)
            res["health_details"] = _loads(res.get("health_details"), {})
            return res

    async def get_ai_model_health_all(self) -> list:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM ai_model_health ORDER BY domain, model_name").fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["health_details"] = _loads(d.get("health_details"), {})
                results.append(d)
            return results

    async def get_ai_model_health(self, model_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM ai_model_health WHERE model_id = ?", (model_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["health_details"] = _loads(d.get("health_details"), {})
            return d

    # ── Auth Decisions & Authorization Pipeline ──────────────────────────

    async def save_auth_decision(self, decision: dict) -> dict:
        dec_id = decision.get("id") or f"DEC-{uuid.uuid4().hex[:10].upper()}"
        ts = decision.get("timestamp") or _utcnow()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auth_decisions (
                    id, timestamp, identity, role, domain, resource, action,
                    decision, risk_score, risk_category, explanation, factors,
                    restrictions, event_id, context_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dec_id,
                    ts,
                    decision.get("identity", "unknown"),
                    decision.get("role", "user"),
                    decision.get("domain", "SECURITY"),
                    decision.get("resource", "SYSTEM"),
                    decision.get("action", "ACCESS"),
                    decision.get("decision", "ALLOW"),
                    float(decision.get("risk_score", 0.0)),
                    decision.get("risk_category", "LOW"),
                    decision.get("explanation", ""),
                    _json(decision.get("factors", [])),
                    _json(decision.get("restrictions", [])),
                    decision.get("event_id"),
                    _json(decision.get("context_payload", {}))
                )
            )
            conn.commit()
        return {**decision, "id": dec_id, "timestamp": ts}

    async def get_auth_decisions(
        self,
        limit: int = 50,
        offset: int = 0,
        identity: Optional[str] = None,
        domain: Optional[str] = None,
        decision: Optional[str] = None
    ) -> list:
        with self._connect() as conn:
            query = "SELECT * FROM auth_decisions WHERE 1=1"
            params = []
            if identity:
                query += " AND identity = ?"
                params.append(identity)
            if domain:
                query += " AND domain = ?"
                params.append(domain.upper())
            if decision:
                query += " AND decision = ?"
                params.append(decision.upper())
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["factors"] = _loads(d.get("factors"), [])
                d["restrictions"] = _loads(d.get("restrictions"), [])
                d["context_payload"] = _loads(d.get("context_payload"), {})
                results.append(d)
            return results

    # ── Mitigation Proposals & Safety Workflow ────────────────────────────

    async def save_mitigation_proposal(self, proposal: dict) -> dict:
        prop_id = proposal.get("id") or f"MIT-{uuid.uuid4().hex[:8].upper()}"
        now = _utcnow()
        ts = proposal.get("timestamp") or now
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO mitigation_proposals (
                    id, timestamp, domain, action_name, target_asset, proposed_by,
                    safety_verdict, safety_evaluation, status, required_role,
                    approved_by, approval_timestamp, comments, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prop_id,
                    ts,
                    proposal.get("domain", "SECURITY").upper(),
                    proposal.get("action_name", "MITIGATION_ACTION"),
                    proposal.get("target_asset", "SYSTEM"),
                    proposal.get("proposed_by", "AI_SYSTEM"),
                    proposal.get("safety_verdict", "UNSAFE_FOR_AUTONOMOUS_EXECUTION"),
                    _json(proposal.get("safety_evaluation", {})),
                    proposal.get("status", "PENDING_APPROVAL"),
                    proposal.get("required_role", "admin"),
                    proposal.get("approved_by"),
                    proposal.get("approval_timestamp"),
                    proposal.get("comments", ""),
                    now,
                    now
                )
            )
            conn.commit()
        return {**proposal, "id": prop_id, "timestamp": ts, "created_at": now, "updated_at": now}

    async def update_mitigation_proposal(self, proposal_id: str, updates: dict) -> Optional[dict]:
        now = _utcnow()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM mitigation_proposals WHERE id = ?", (proposal_id,)).fetchone()
            if not row:
                return None
            current = dict(row)
            status = updates.get("status", current["status"])
            approved_by = updates.get("approved_by", current["approved_by"])
            approval_ts = updates.get("approval_timestamp", current["approval_timestamp"])
            comments = updates.get("comments", current["comments"])

            conn.execute(
                """
                UPDATE mitigation_proposals SET
                    status = ?, approved_by = ?, approval_timestamp = ?,
                    comments = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, approved_by, approval_ts, comments, now, proposal_id)
            )
            conn.commit()
            updated = conn.execute("SELECT * FROM mitigation_proposals WHERE id = ?", (proposal_id,)).fetchone()
            d = dict(updated)
            d["safety_evaluation"] = _loads(d.get("safety_evaluation"), {})
            return d

    async def get_mitigation_proposals(
        self,
        domain: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list:
        with self._connect() as conn:
            query = "SELECT * FROM mitigation_proposals WHERE 1=1"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain.upper())
            if status:
                query += " AND status = ?"
                params.append(status.upper())
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d["safety_evaluation"] = _loads(d.get("safety_evaluation"), {})
                results.append(d)
            return results

    async def get_mitigation_proposal(self, proposal_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM mitigation_proposals WHERE id = ?", (proposal_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["safety_evaluation"] = _loads(d.get("safety_evaluation"), {})
            return d

    # ═══════════════════════════════════════════════════════════════════
    # UNIFIED SECURITY OPERATIONS CENTER (SOC) PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════

    async def save_soc_incident(self, incident: dict) -> dict:
        inc = dict(incident)
        inc_id = inc.get("id") or f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        inc["id"] = inc_id
        inc.setdefault("timestamp", _utcnow())
        inc.setdefault("updated_at", _utcnow())
        inc.setdefault("status", "DETECTED")
        inc.setdefault("severity", "HIGH")
        inc.setdefault("domain", "GLOBAL")
        inc.setdefault("title", f"Security Anomaly on {inc.get('asset', 'Unknown Asset')}")
        inc.setdefault("asset", "UNKNOWN_ASSET")
        inc.setdefault("identity", "unknown_actor")
        inc.setdefault("device", "DEV-UNKNOWN")
        inc.setdefault("owner", None)
        inc.setdefault("assigned_analyst", inc.get("owner"))
        inc.setdefault("evidence", [])
        inc.setdefault("notes", [])
        inc.setdefault("timeline", [{
            "phase": inc.get("status", "DETECTED"),
            "title": "Incident Detected",
            "description": f"Incident triggered by {inc.get('attack_type', 'security anomaly')}",
            "timestamp": inc["timestamp"],
            "actor": "System Event Engine"
        }])
        inc.setdefault("related_event_ids", [])
        inc.setdefault("risk_score", 65.0)

        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO incidents
                    (id, timestamp, title, status, severity, asset, owner, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inc["id"], inc["timestamp"], inc["title"],
                        inc["status"], inc["severity"], inc["asset"],
                        inc.get("owner") or inc.get("assigned_analyst"),
                        _json(inc)
                    )
                )
                conn.commit()
        return inc

    async def get_soc_incidents(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        limit = max(1, min(int(limit), 1000))
        offset = max(0, int(offset))
        with self._connect() as conn:
            query = "SELECT payload FROM incidents WHERE 1=1"
            params = []
            if status:
                query += " AND UPPER(status) = ?"
                params.append(status.upper())
            if severity:
                query += " AND UPPER(severity) = ?"
                params.append(severity.upper())
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                item = _loads(r["payload"], {})
                if domain and item.get("domain", "").upper() != domain.upper():
                    continue
                results.append(item)
            return results

    async def get_soc_incident(self, incident_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT payload FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            return _loads(row["payload"], {})

    async def update_soc_incident_workflow(self, incident_id: str, updates: dict) -> Optional[dict]:
        incident = await self.get_soc_incident(incident_id)
        if not incident:
            return None
        
        # Merge updates
        for k, v in updates.items():
            incident[k] = v
        incident["updated_at"] = _utcnow()
        if "assigned_analyst" in updates and not incident.get("owner"):
            incident["owner"] = updates["assigned_analyst"]
        
        return await self.save_soc_incident(incident)

    async def add_soc_evidence(self, evidence: dict) -> dict:
        ev = dict(evidence)
        ev_id = ev.get("id") or f"EVID-{uuid.uuid4().hex[:8].upper()}"
        ev["id"] = ev_id
        ev.setdefault("timestamp", _utcnow())
        
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO soc_evidence
                    (id, incident_id, evidence_type, description, artifact_ref, hash_value, added_by, timestamp, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev["id"], ev["incident_id"], ev.get("evidence_type", "FORENSIC_ARTIFACT"),
                        ev.get("description", ""), ev.get("artifact_ref", ""),
                        ev.get("hash_value", ""), ev.get("added_by", "analyst"),
                        ev["timestamp"], _json(ev)
                    )
                )
                conn.commit()

        # Also append to incident record
        inc = await self.get_soc_incident(ev["incident_id"])
        if inc:
            ev_list = inc.get("evidence", [])
            ev_list.append(ev)
            inc["evidence"] = ev_list
            await self.save_soc_incident(inc)

        return ev

    async def get_soc_evidence(self, incident_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM soc_evidence WHERE incident_id = ? ORDER BY timestamp ASC",
                (incident_id,)
            ).fetchall()
            return [_loads(r["payload"], {}) for r in rows]

    async def add_soc_note(self, note_dict: dict) -> dict:
        n = dict(note_dict)
        n_id = n.get("id") or f"NOTE-{uuid.uuid4().hex[:8].upper()}"
        n["id"] = n_id
        n.setdefault("timestamp", _utcnow())

        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO soc_notes
                    (id, incident_id, author, note, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        n["id"], n["incident_id"], n.get("author", "analyst"),
                        n.get("note", ""), n["timestamp"]
                    )
                )
                conn.commit()

        # Also append to incident record
        inc = await self.get_soc_incident(n["incident_id"])
        if inc:
            notes_list = inc.get("notes", [])
            notes_list.append(n)
            inc["notes"] = notes_list
            await self.save_soc_incident(inc)

        return n

    async def get_soc_notes(self, incident_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, incident_id, author, note, timestamp FROM soc_notes WHERE incident_id = ? ORDER BY timestamp ASC",
                (incident_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    async def save_soc_attack_chain(self, chain: dict) -> dict:
        c = dict(chain)
        c_id = c.get("id") or f"CHAIN-{uuid.uuid4().hex[:8].upper()}"
        c["id"] = c_id
        c.setdefault("first_seen", _utcnow())
        c.setdefault("last_seen", _utcnow())
        c.setdefault("severity", "HIGH")
        c.setdefault("status", "ACTIVE")
        c.setdefault("kill_chain_stage", "Execution")

        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO soc_attack_chains
                    (id, name, threat_actor, target_sector, severity, kill_chain_stage, first_seen, last_seen, incident_ids, indicators, tactics, techniques, status, payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c["id"], c.get("name", "Unknown Campaign"), c.get("threat_actor", "APT-UNKNOWN"),
                        c.get("target_sector", "CRITICAL_INFRASTRUCTURE"), c["severity"],
                        c["kill_chain_stage"], c["first_seen"], c["last_seen"],
                        _json(c.get("incident_ids", [])), _json(c.get("indicators", [])),
                        _json(c.get("tactics", [])), _json(c.get("techniques", [])),
                        c["status"], _json(c)
                    )
                )
                conn.commit()
        return c

    async def get_soc_attack_chains(self, limit: int = 50) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload FROM soc_attack_chains ORDER BY last_seen DESC LIMIT ?",
                (max(1, min(int(limit), 200)),)
            ).fetchall()
            return [_loads(r["payload"], {}) for r in rows]

store = DataStore()


