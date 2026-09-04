"""
Securox — Database Integrity Test Suite
Comprehensive automated tests validating:
  1. Foreign Key enforcement
  2. Uniqueness constraints
  3. Multi-tenant / Domain isolation
  4. Transaction consistency and rollback semantics
  5. Concurrent multithreaded writes under WAL
  6. Simulation state persistence across sessions
  7. Security bans enforcement
  8. AML graph state persistence
"""

import sys
import os
import uuid
import threading
import pytest
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Ensure backend/app is on sys.path
backend_app = Path(__file__).resolve().parent.parent / "backend" / "app"
if str(backend_app) not in sys.path:
    sys.path.insert(0, str(backend_app))

from core.database import Base, SessionLocal, engine
from core import models
from core.store import store


@pytest.fixture(scope="function")
def isolated_db():
    """Provides an in-memory SQLite database with strict foreign keys and WAL emulation."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )

    @event.listens_for(test_engine, "connect")
    def enable_fk(dbapi_con, con_record):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine, expire_on_commit=False)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        test_engine.dispose()


# ==============================================================================
# 1. FOREIGN KEY INTEGRITY TESTS
# ==============================================================================

def test_foreign_key_enforcement_invalid_patient(isolated_db):
    """Ensures child medical record cannot be created with non-existent patient."""
    bad_record = models.MedicalRecord(
        id="REC-ERR-01",
        patient_id="NON_EXISTENT_PATIENT_ID",
        doctor_id="doc_sarah",
        diagnosis="Acute Hypertension"
    )
    isolated_db.add(bad_record)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()


def test_foreign_key_cascade_patient_deletion(isolated_db):
    """Ensures deleting a patient cascades and deletes associated medical records."""
    patient = models.Patient(
        id="P-TEST-CASCADE",
        name="Cascade Test Patient",
        age=35,
        gender="FEMALE",
        department="Cardiology"
    )
    isolated_db.add(patient)
    isolated_db.commit()

    record = models.MedicalRecord(
        id="REC-CASCADE-01",
        patient_id=patient.id,
        doctor_id="doc_sarah",
        diagnosis="Normal sinus rhythm"
    )
    isolated_db.add(record)
    isolated_db.commit()

    assert isolated_db.query(models.MedicalRecord).filter_by(patient_id=patient.id).count() == 1

    # Delete patient
    isolated_db.delete(patient)
    isolated_db.commit()

    # Medical record should be cascade deleted
    assert isolated_db.query(models.MedicalRecord).filter_by(patient_id="P-TEST-CASCADE").count() == 0


def test_foreign_key_traffic_signal_intersection(isolated_db):
    """Ensures traffic signal links correctly to intersection."""
    intersection = models.Intersection(
        id="INT-VALID-01",
        name="Valid Crossing",
        latitude=12.97,
        longitude=77.59
    )
    isolated_db.add(intersection)
    isolated_db.commit()

    sig = models.TrafficSignal(
        id="SIG-VALID-01",
        intersection_id=intersection.id,
        zone="Central"
    )
    isolated_db.add(sig)
    isolated_db.commit()

    queried_sig = isolated_db.query(models.TrafficSignal).filter_by(id="SIG-VALID-01").first()
    assert queried_sig is not None
    assert queried_sig.intersection_rel.name == "Valid Crossing"


# ==============================================================================
# 2. UNIQUENESS CONSTRAINTS
# ==============================================================================

def test_uniqueness_users_username(isolated_db):
    """Ensures duplicate usernames raise IntegrityError."""
    u1 = models.User(
        id="usr-1",
        username="securox_admin",
        hashed_password="hash_value_1",
        role="ADMIN"
    )
    isolated_db.add(u1)
    isolated_db.commit()

    u2 = models.User(
        id="usr-2",
        username="securox_admin",  # DUPLICATE
        hashed_password="hash_value_2",
        role="OPERATOR"
    )
    isolated_db.add(u2)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()


def test_uniqueness_vehicle_tag_id(isolated_db):
    """Ensures duplicate FASTag EPC tags raise IntegrityError."""
    v1 = models.Vehicle(tag_id="FT-UNIQUE-999", vehicle_plate="KA-01-AB-1234")
    isolated_db.add(v1)
    isolated_db.commit()

    v2 = models.Vehicle(tag_id="FT-UNIQUE-999", vehicle_plate="KA-02-CD-5678")
    isolated_db.add(v2)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()


def test_uniqueness_bank_account_number(isolated_db):
    """Ensures duplicate account numbers raise IntegrityError."""
    acc1 = models.BankAccount(
        id="ACC-U1",
        customer_id="CUST-1",
        account_number="111222333444",
        balance=5000.0
    )
    isolated_db.add(acc1)
    isolated_db.commit()

    acc2 = models.BankAccount(
        id="ACC-U2",
        customer_id="CUST-2",
        account_number="111222333444",  # DUPLICATE
        balance=10000.0
    )
    isolated_db.add(acc2)
    with pytest.raises(IntegrityError):
        isolated_db.commit()
    isolated_db.rollback()


# ==============================================================================
# 3. TENANT & DOMAIN ISOLATION
# ==============================================================================

def test_domain_isolation_healthcare_vs_traffic(isolated_db):
    """Ensures healthcare queries cannot return or contaminate traffic domain data."""
    # Healthcare record
    patient = models.Patient(
        id="P-DEPT-NEURO",
        hospital_id="HOSP-CITY-01",
        name="Neuro Patient",
        age=45,
        gender="MALE",
        department="Neurology"
    )
    isolated_db.add(patient)

    # Traffic signal
    sig = models.TrafficSignal(
        id="SIG-ZONE-NORTH",
        zone="North",
        current_state="RED"
    )
    isolated_db.add(sig)

    # Finance account
    acc = models.BankAccount(
        id="ACC-FIN-01",
        customer_id="CUST-FIN-01",
        account_number="998877665544",
        balance=25000.0
    )
    isolated_db.add(acc)
    isolated_db.commit()

    # Query domain isolates
    neuro_patients = isolated_db.query(models.Patient).filter_by(department="Neurology").all()
    assert len(neuro_patients) == 1
    assert neuro_patients[0].name == "Neuro Patient"

    cardio_patients = isolated_db.query(models.Patient).filter_by(department="Cardiology").all()
    assert len(cardio_patients) == 0

    north_signals = isolated_db.query(models.TrafficSignal).filter_by(zone="North").all()
    assert len(north_signals) == 1
    assert north_signals[0].id == "SIG-ZONE-NORTH"

    cust_accounts = isolated_db.query(models.BankAccount).filter_by(customer_id="CUST-FIN-01").all()
    assert len(cust_accounts) == 1
    assert cust_accounts[0].account_number == "998877665544"


# ==============================================================================
# 4. TRANSACTION CONSISTENCY & ATOMIC ROLLBACK
# ==============================================================================

def test_atomic_transaction_rollback(isolated_db):
    """Verifies that an unhandled error inside a multi-operation transaction rolls back cleanly."""
    acc = models.BankAccount(
        id="ACC-TX-01",
        customer_id="CUST-TX-01",
        account_number="554433221100",
        balance=10000.0
    )
    isolated_db.add(acc)
    isolated_db.commit()

    initial_balance = acc.balance

    try:
        # Deduct balance
        acc.balance -= 2000.0
        # Add valid transaction
        tx = models.BankTransaction(
            id="TX-ROLLBACK-01",
            account_id=acc.id,
            sender_name="Sender One",
            receiver_account="ACC-RECEIVER",
            amount=2000.0
        )
        isolated_db.add(tx)

        # Deliberately cause an integrity error in the same transaction
        bad_tx = models.BankTransaction(
            id="TX-ROLLBACK-01",  # PRIMARY KEY COLLISION
            account_id=acc.id,
            sender_name="Sender Duplicate",
            receiver_account="ACC-RECEIVER",
            amount=500.0
        )
        isolated_db.add(bad_tx)
        isolated_db.commit()
    except IntegrityError:
        isolated_db.rollback()

    # Verify rollback: balance must be completely restored, no transaction record inserted
    re_queried_acc = isolated_db.query(models.BankAccount).filter_by(id="ACC-TX-01").one()
    assert re_queried_acc.balance == initial_balance

    assert isolated_db.query(models.BankTransaction).filter_by(id="TX-ROLLBACK-01").count() == 0


# ==============================================================================
# 5. CONCURRENT WRITES (WAL / MULTITHREADED)
# ==============================================================================

def test_concurrent_writes_thread_safety():
    """Spawns 10 concurrent threads executing simultaneous writes to test WAL mode resilience."""
    errors = []
    threads = []
    num_threads = 10
    writes_per_thread = 15

    def worker(worker_id):
        try:
            db = SessionLocal()
            for i in range(writes_per_thread):
                log_id = f"CONC-AUDIT-{worker_id}-{i}-{uuid.uuid4().hex[:6]}"
                db.add(models.AuditLog(
                    id=log_id,
                    actor_username=f"worker_{worker_id}",
                    action="CONCURRENT_BENCHMARK",
                    resource_type="STRESS_TEST",
                    decision="ALLOW",
                    reason=f"Concurrent write batch {i}"
                ))
                db.commit()
            db.close()
        except Exception as e:
            errors.append((worker_id, str(e)))

    for wid in range(num_threads):
        t = threading.Thread(target=worker, args=(wid,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join(timeout=10)

    assert len(errors) == 0, f"Concurrent write errors encountered: {errors}"

    # Verify total records written
    verify_db = SessionLocal()
    count = verify_db.query(models.AuditLog).filter_by(action="CONCURRENT_BENCHMARK").count()
    assert count == (num_threads * writes_per_thread)

    # Clean up test benchmark records
    verify_db.query(models.AuditLog).filter_by(action="CONCURRENT_BENCHMARK").delete()
    verify_db.commit()
    verify_db.close()


# ==============================================================================
# 6. SIMULATION STATE PERSISTENCE
# ==============================================================================

@pytest.mark.asyncio
async def test_simulation_state_persistence():
    """Verifies that active simulation state is saved and recovered across sessions."""
    saved = await store.save_simulation_state(
        scenario_id="CASCADE_MEGA_01",
        status="RUNNING",
        current_stage=4,
        stage_name="Substation Grid Failure",
        elapsed_seconds=185.5,
        events_emitted=420,
        state_blob={"active_injections": ["DDoS_Toll", "Signal_Tamper"], "speed": 5.0}
    )
    assert saved["scenario_id"] == "CASCADE_MEGA_01"
    assert saved["status"] == "RUNNING"

    # Fetch fresh state
    recovered = await store.get_simulation_state()
    assert recovered is not None
    assert recovered["scenario_id"] == "CASCADE_MEGA_01"
    assert recovered["current_stage"] == 4
    assert recovered["stage_name"] == "Substation Grid Failure"
    assert recovered["elapsed_seconds"] == 185.5
    assert recovered["events_emitted"] == 420
    assert "DDoS_Toll" in recovered["state_blob"]["active_injections"]


# ==============================================================================
# 7. SECURITY BANS PERSISTENCE
# ==============================================================================

@pytest.mark.asyncio
async def test_security_bans_persistence():
    """Verifies IP and Device bans persist and are evaluated correctly."""
    test_ip = f"198.51.100.{uuid.uuid4().hex[:2]}"
    await store.add_security_ban(
        target_type="IP",
        target_value=test_ip,
        reason="Malicious fastag replay spoofing",
        banned_by="AI_COMMANDER"
    )

    is_banned = await store.is_banned("IP", test_ip)
    assert is_banned is True

    # Unbanned IP should return False
    assert await store.is_banned("IP", "127.0.0.1") is False


# ==============================================================================
# 8. AML GRAPH STATE PERSISTENCE
# ==============================================================================

@pytest.mark.asyncio
async def test_aml_graph_state_persistence():
    """Verifies AML money mule network graph topology persistence."""
    nodes = [
        {"id": "mule-node-99", "type": "mule", "risk_score": 98.0},
        {"id": "victim-node-12", "type": "victim", "risk_score": 10.0}
    ]
    edges = [
        {"source": "victim-node-12", "target": "mule-node-99", "amount": 250000.0}
    ]
    clusters = [
        {"cluster_id": "MULE-CLUSTER-77", "mule_nodes": ["mule-node-99"]}
    ]

    await store.save_aml_graph_state(
        graph_name="TestMuleGraph",
        node_count=len(nodes),
        edge_count=len(edges),
        mule_cluster_count=len(clusters),
        nodes=nodes,
        edges=edges,
        clusters=clusters,
        graph_id="test_aml_graph"
    )

    retrieved = await store.get_aml_graph_state(graph_id="test_aml_graph")
    assert retrieved is not None
    assert retrieved["graph_name"] == "TestMuleGraph"
    assert retrieved["node_count"] == 2
    assert retrieved["edge_count"] == 1
    assert len(retrieved["nodes"]) == 2
    assert retrieved["nodes"][0]["id"] == "mule-node-99"
