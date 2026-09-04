"""
Securox — Authoritative Database Seeder
Seeds default baseline records for fresh deployments on PostgreSQL or clean SQLite.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add backend/app to sys.path
backend_app = Path(__file__).resolve().parent.parent / "backend" / "app"
if str(backend_app) not in sys.path:
    sys.path.insert(0, str(backend_app))

from core.database import engine, Base, SessionLocal
from core import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("securox.seed")


def seed_database():
    logger.info("Verifying unified schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. ROLES
        roles = [
            ("ADMIN", "Full platform administrative privilege"),
            ("CISO", "Chief Information Security Officer executive cockpit"),
            ("SOC_ANALYST", "Security operations center alert investigation and mitigation"),
            ("ANALYST", "Forensic threat investigation"),
            ("OPERATOR", "Municipal infrastructure operations"),
            ("TRAFFIC_OPERATOR", "Traffic signal and smart corridor control"),
            ("DOCTOR", "Clinical patient record access"),
            ("NURSE", "Emergency and triage patient care"),
            ("FINANCE_OPERATOR", "Fintech risk and anti-fraud monitoring"),
            ("AUDITOR", "Independent compliance and security audit read-only"),
            ("VIEWER", "Read-only monitoring dashboard")
        ]
        for r_id, desc in roles:
            if not db.query(models.Role).filter_by(id=r_id).first():
                db.add(models.Role(id=r_id, name=r_id, description=desc, is_system=True))
        db.commit()

        # 2. DEFAULT USERS
        # Hash for 'admin123'
        from auth.jwt_auth import get_password_hash
        admin_hash = get_password_hash("admin123")

        users = [
            ("admin", "admin@securox.city", "Chief System Administrator", "ADMIN"),
            ("ciso", "ciso@securox.city", "Chief Info Security Officer", "CISO"),
            ("soc_analyst", "analyst@securox.city", "Senior SOC Analyst", "SOC_ANALYST"),
            ("traffic_op", "traffic_op@securox.city", "Traffic Control Lead", "TRAFFIC_OPERATOR"),
            ("doc_sarah", "doc.sarah@securox.city", "Dr. Sarah Chen, MD", "DOCTOR"),
            ("nurse_priya", "nurse.priya@securox.city", "Priya Sharma, RN", "NURSE"),
            ("fin_sec", "fin_sec@securox.city", "Fintech Fraud Investigator", "FINANCE_OPERATOR"),
            ("auditor", "auditor@securox.city", "External Compliance Auditor", "AUDITOR"),
        ]
        for u_name, u_email, u_full, u_role in users:
            existing = db.query(models.User).filter(
                (models.User.username == u_name) | (models.User.email == u_email)
            ).first()
            if not existing:
                db.add(models.User(
                    id=f"usr-{u_name}",
                    username=u_name,
                    email=u_email,
                    full_name=u_full,
                    hashed_password=admin_hash,
                    role=u_role,
                    is_active=True
                ))
        db.commit()

        # 3. INTERSECTIONS & SIGNALS
        intersections = [
            ("INT-01", "MG Road & Residency Rd", 12.9716, 77.5946, "CTRL-01", "GREEN"),
            ("INT-02", "Indiranagar 100ft Rd", 12.9784, 77.6408, "CTRL-02", "RED"),
            ("INT-03", "Koramangala 80ft Rd", 12.9352, 77.6245, "CTRL-03", "GREEN"),
            ("INT-04", "Electronic City Phase 1", 12.8452, 77.6602, "CTRL-04", "RED"),
            ("INT-05", "Whitefield Main Rd", 12.9698, 77.7500, "CTRL-05", "YELLOW"),
        ]
        for int_id, name, lat, lon, ctrl, phase in intersections:
            if not db.query(models.Intersection).filter_by(id=int_id).first():
                db.add(models.Intersection(
                    id=int_id, name=name, latitude=lat, longitude=lon,
                    controller_id=ctrl, signal_phase=phase
                ))
        db.commit()

        signals = [
            ("SIG-01", "INT-01", "MG Road & Residency Rd", "Central", "CTRL-01", "GREEN", 90),
            ("SIG-02", "INT-02", "Indiranagar 100ft Rd", "East", "CTRL-02", "RED", 80),
            ("SIG-03", "INT-03", "Koramangala 80ft Rd", "South", "CTRL-03", "GREEN", 85),
            ("SIG-04", "INT-04", "Electronic City Phase 1", "South", "CTRL-04", "RED", 120),
            ("SIG-05", "INT-05", "Whitefield Main Rd", "East", "CTRL-05", "YELLOW", 90),
            ("SIG-06", None, "Hebbal Flyover Junction", "North", "CTRL-06", "RED", 100),
        ]
        for sig_id, i_id, i_name, zone, ctrl, state, cycle in signals:
            if not db.query(models.TrafficSignal).filter_by(id=sig_id).first():
                db.add(models.TrafficSignal(
                    id=sig_id, intersection_id=i_id, intersection=i_name,
                    zone=zone, controller_id=ctrl, current_state=state, cycle_time_sec=cycle
                ))
        db.commit()

        # 4. CAMERAS
        cameras = [
            ("CAM-01", "MG Road Junction HD", "Central Transit Hub", 12.9716, 77.5946, 30.0, "1920x1080"),
            ("CAM-02", "Indiranagar Metro Feed", "Indiranagar", 12.9784, 77.6408, 30.0, "1920x1080"),
            ("CAM-03", "Koramangala Sony Signal", "Koramangala", 12.9352, 77.6245, 25.0, "1920x1080"),
            ("CAM-04", "Silk Board Flyover Cam", "South Highway", 12.9176, 77.6238, 30.0, "1920x1080"),
            ("CAM-05", "Electronic City Toll ANPR", "Electronic City Toll", 12.8452, 77.6602, 60.0, "3840x2160"),
        ]
        for c_id, c_name, c_loc, lat, lon, fps, res in cameras:
            if not db.query(models.Camera).filter_by(id=c_id).first():
                db.add(models.Camera(
                    id=c_id, name=c_name, location=c_loc, latitude=lat, longitude=lon,
                    fps=fps, resolution=res, status="ONLINE"
                ))
        db.commit()

        # 5. PATIENTS & AMBULANCES
        patients = [
            ("P-1001", "HOSP-CITY-01", "Aarav Sharma", 42, "MALE", "Cardiology", "doc_sarah", "nurse_priya", "ICU-Bed-04", "CRITICAL"),
            ("P-1002", "HOSP-CITY-01", "Ananya Rao", 29, "FEMALE", "Neurology", "doc_sarah", "nurse_priya", "Ward-B-12", "STABLE"),
            ("P-1003", "HOSP-CITY-01", "Rajesh Kumar", 58, "MALE", "Emergency Trauma", "doc_sarah", "nurse_priya", "Trauma-01", "CRITICAL"),
        ]
        for p_id, h_id, name, age, gender, dept, doc, nurse, bed, cond in patients:
            if not db.query(models.Patient).filter_by(id=p_id).first():
                db.add(models.Patient(
                    id=p_id, hospital_id=h_id, name=name, age=age, gender=gender,
                    department=dept, assigned_doctor_id=doc, assigned_nurse_id=nurse,
                    room_bed=bed, condition=cond
                ))
        db.commit()

        # 6. BANK ACCOUNTS
        bank_accounts = [
            ("ACC-9001", "CUST-492", "492001928374", "CHECKING", 345000.0, "INR", "CENTRAL_BLR", "ACTIVE"),
            ("ACC-9002", "CUST-883", "883002948172", "SAVINGS", 1250000.0, "INR", "KORAMANGALA", "ACTIVE"),
            ("ACC-9003", "CUST-121", "121004819204", "SAVINGS", 84000.0, "INR", "INDIRANAGAR", "ACTIVE"),
            ("ACC-9004", "CUST-MULE", "999000111222", "CURRENT", 18500.0, "INR", "GHOST_BRANCH", "FLAGGED"),
        ]
        for acc_id, cust_id, acc_num, acc_type, bal, curr, branch, stat in bank_accounts:
            if not db.query(models.BankAccount).filter_by(id=acc_id).first():
                db.add(models.BankAccount(
                    id=acc_id, customer_id=cust_id, account_number=acc_num,
                    account_type=acc_type, balance=bal, currency=curr, branch=branch, status=stat
                ))
        db.commit()

        # 7. SIMULATION & AML STATE
        if not db.query(models.SimulationState).filter_by(id="active_state").first():
            db.add(models.SimulationState(
                id="active_state", scenario_id="", status="IDLE", current_stage=0,
                stage_name="Idle", elapsed_seconds=0.0, events_emitted=0, state_blob="{}"
            ))
            db.commit()

        if not db.query(models.AMLGraphState).filter_by(id="primary").first():
            db.add(models.AMLGraphState(
                id="primary", graph_name="SmartCityFintechGraph", node_count=12, edge_count=24,
                mule_cluster_count=2,
                nodes_json=json.dumps([
                    {"id": "mule-wallet", "type": "mule", "risk_score": 92.5},
                    {"id": "user-492@okaxis", "type": "victim", "risk_score": 15.0},
                    {"id": "user-883@okaxis", "type": "victim", "risk_score": 12.0},
                    {"id": "ghost-merchant", "type": "mule", "risk_score": 95.0}
                ]),
                edges_json=json.dumps([
                    {"source": "user-492@okaxis", "target": "mule-wallet", "amount": 180000.0},
                    {"source": "mule-wallet", "target": "ghost-merchant", "amount": 175000.0}
                ]),
                clusters_json=json.dumps([
                    {"cluster_id": "CLUSTER-AML-01", "mule_nodes": ["mule-wallet", "ghost-merchant"], "risk_level": "CRITICAL"}
                ])
            ))
            db.commit()

        logger.info("Authoritative baseline seed data created successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
