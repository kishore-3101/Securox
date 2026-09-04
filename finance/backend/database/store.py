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
                    stream_url TEXT,
                    status TEXT NOT NULL DEFAULT 'ONLINE',
                    fps REAL DEFAULT 30.0,
                    incident_count INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
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
                    (id, username, hashed_password, role, full_name, is_active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
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
            return dict(row) if row else None

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

    async def get_bank_accounts(self, customer_id: Optional[str] = None) -> list[dict]:
        with self._connect() as conn:
            if customer_id:
                rows = conn.execute("SELECT * FROM bank_accounts WHERE customer_id = ?", (customer_id,)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM bank_accounts ORDER BY id ASC").fetchall()
            return [dict(r) for r in rows]

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
            conn.execute(
                """
                INSERT INTO devices
                (id, user_id, fingerprint, os, browser, ip, location, trust_score, status, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (dev_id, user_id, fingerprint, os_name, browser, ip, location, trust_score, status, now, now)
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


store = DataStore()

