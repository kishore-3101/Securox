import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, BrowserContext, Page

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5174")
API_URL = os.getenv("E2E_API_URL", "http://127.0.0.1:8000")
DB_PATH = Path(__file__).resolve().parent.parent.parent / "backend" / "app" / "core" / "securox.db"


class DatabaseVerifier:
    """Direct database verification against the SQLite persistent store."""

    def __init__(self, db_path: Path):
        self.db_path = str(db_path)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_incidents(self, domain: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if domain:
                cur.execute("SELECT * FROM incidents WHERE domain = ? ORDER BY id DESC LIMIT ?", (domain, limit))
            else:
                cur.execute("SELECT * FROM incidents ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def count_incidents(self) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM incidents")
            return cur.fetchone()[0]

    def get_auth_decisions(self, identity: Optional[str] = None, action: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            query = "SELECT * FROM auth_decisions WHERE 1=1"
            params = []
            if identity:
                query += " AND identity = ?"
                params.append(identity)
            if action:
                query += " AND action = ?"
                params.append(action)
            query += " ORDER BY id DESC LIMIT 50"
            cur.execute(query, tuple(params))
            return [dict(r) for r in cur.fetchall()]

    def get_risk_assessments(self, domain: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if domain:
                cur.execute("SELECT * FROM risk_assessments WHERE domain = ? ORDER BY id DESC LIMIT ?", (domain, limit))
            else:
                cur.execute("SELECT * FROM risk_assessments ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def count_risk_assessments(self) -> int:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM risk_assessments")
            return cur.fetchone()[0]

    def get_audit_logs(self, action: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            if action:
                cur.execute("SELECT * FROM audit_logs WHERE action = ? ORDER BY id DESC LIMIT ?", (action, limit))
            else:
                cur.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def get_finance_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM finance_accounts WHERE id = ?", (account_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def assert_blocked_integrity(frontend_says_blocked: bool, backend_allows_request: bool):
    """
    INVARIANT 1:
    A test MUST FAIL if:
      frontend says BLOCKED
      but backend allows the request.
    """
    if frontend_says_blocked and backend_allows_request:
        raise AssertionError(
            "STRICT INVARIANT VIOLATION: Frontend displayed BLOCKED, but backend allowed the request! "
            "Zero-Trust enforcement discrepancy detected between client presentation and server pipeline."
        )


def assert_incident_persisted(ui_incident_id: str, db: DatabaseVerifier) -> Dict[str, Any]:
    """
    INVARIANT 2:
    A test MUST FAIL if:
      incident appears in UI
      but does not exist in persistence.
    """
    if not ui_incident_id:
        raise AssertionError("STRICT INVARIANT VIOLATION: Received empty incident ID from UI.")
    
    incident = db.get_incident(ui_incident_id)
    if not incident:
        raise AssertionError(
            f"STRICT INVARIANT VIOLATION: Incident '{ui_incident_id}' appears in the UI, "
            f"but does NOT exist in persistence (SQLite incidents table)! Fake UI animation detected."
        )
    return incident


def assert_risk_audit_recorded(
    initial_score: float,
    current_score: float,
    db: DatabaseVerifier,
    initial_count: Optional[int] = None,
    domain: Optional[str] = None
):
    """
    INVARIANT 3:
    A test MUST FAIL if:
      risk score changes
      but no risk event is recorded.
    """
    if abs(current_score - initial_score) > 0.001:
        current_count = db.count_risk_assessments()
        if initial_count is not None and current_count <= initial_count:
            raise AssertionError(
                f"STRICT INVARIANT VIOLATION: Risk score changed from {initial_score} to {current_score}, "
                f"but no risk assessment / event was recorded in persistence! "
                f"(assessment count before: {initial_count}, count after: {current_count})"
            )
        
        assessments = db.get_risk_assessments(domain=domain, limit=5)
        if not assessments:
            raise AssertionError(
                f"STRICT INVARIANT VIOLATION: Risk score mutated to {current_score}, "
                f"but zero risk assessments exist in persistence table risk_assessments!"
            )


@pytest.fixture(scope="session")
def db() -> DatabaseVerifier:
    return DatabaseVerifier(DB_PATH)


@pytest_asyncio.fixture(scope="function")
async def browser_context():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            base_url=BASE_URL,
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )
        yield context
        await context.close()
        await browser.close()


@pytest_asyncio.fixture(scope="function")
async def page(browser_context: BrowserContext) -> Page:
    p = await browser_context.new_page()
    p.set_default_timeout(15000)
    return p
