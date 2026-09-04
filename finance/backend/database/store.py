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

                CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON event_stream(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_history(timestamp DESC);
                CREATE INDEX IF NOT EXISTS idx_fraud_timestamp ON fraud_alerts(timestamp DESC);
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
            for username, role, full_name in [
                ("admin", "admin", "Securox Administrator"),
                ("analyst", "analyst", "SOC Analyst"),
                ("traffic", "traffic_operator", "Traffic Operator"),
                ("finance", "finance_investigator", "Finance Investigator"),
                ("emergency", "emergency_commander", "Emergency Commander"),
            ]:
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
            }
            return {
                key: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for key, table in tables.items()
            }


store = DataStore()
