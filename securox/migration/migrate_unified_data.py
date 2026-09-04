"""
Securox — Unified Database Data Migration & Reconciliation Script
Reconciles all data from securox_pre_migration.db and traffic_pre_migration.db
into the authoritative unified database schema (SQLAlchemy 2.0).
"""

import sys
import os
import sqlite3
import json
import logging
from pathlib import Path

# Add backend/app to sys.path
backend_app = Path(__file__).resolve().parent.parent / "backend" / "app"
if str(backend_app) not in sys.path:
    sys.path.insert(0, str(backend_app))

from core.database import engine, Base, SessionLocal, DEFAULT_DB_FILE
from core import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("securox.migrate")

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backup"
SECUROX_PRE_DB = BACKUP_DIR / "securox_pre_migration.db"
TRAFFIC_PRE_DB = BACKUP_DIR / "traffic_pre_migration.db"


def _row_to_dict(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def run_migration():
    if not SECUROX_PRE_DB.exists():
        raise FileNotFoundError(f"Missing backup: {SECUROX_PRE_DB}")
    if not TRAFFIC_PRE_DB.exists():
        raise FileNotFoundError(f"Missing backup: {TRAFFIC_PRE_DB}")

    # Remove stale un-migrated DB file if SQLite to create clean schema with all new columns
    if str(engine.url).startswith("sqlite") and DEFAULT_DB_FILE.exists():
        logger.info(f"Recreating clean unified database at {DEFAULT_DB_FILE}...")
        engine.dispose()
        DEFAULT_DB_FILE.unlink()

    logger.info("Initializing unified schema on authoritative database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    conn_sec = sqlite3.connect(SECUROX_PRE_DB)
    conn_tra = sqlite3.connect(TRAFFIC_PRE_DB)

    try:
        cur_sec = conn_sec.cursor()
        cur_tra = conn_tra.cursor()

        # ----------------------------------------------------------------------
        # 1. INTERSECTIONS & ROAD SEGMENTS
        # ----------------------------------------------------------------------
        logger.info("Migrating intersections & road segments...")
        cur_tra.execute("SELECT * FROM intersections")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Intersection(
                id=d["id"],
                name=d["name"],
                latitude=d["latitude"],
                longitude=d["longitude"],
                controller_id=d.get("controller_id"),
                status=d.get("status", "ONLINE"),
                signal_phase=d.get("signal_phase", "RED"),
                queue_length=d.get("queue_length", 0),
                risk_score=d.get("risk_score", 0.0)
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM road_segments")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.RoadSegment(
                id=d["id"],
                name=d["name"],
                route_id=d["route_id"],
                start_node=d["start_node"],
                end_node=d["end_node"],
                length_km=d.get("length_km", 1.0),
                lanes=d.get("lanes", 2),
                speed_limit_kmh=d.get("speed_limit_kmh", 50.0),
                current_speed_kmh=d.get("current_speed_kmh", 45.0),
                current_volume=d.get("current_volume", 100),
                congestion_level=d.get("congestion_level", "LOW"),
                incident_count=d.get("incident_count", 0),
                last_updated=d.get("last_updated", models._utcnow_iso())
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 2. TOLLGATES, SENSORS, VEHICLES & SCANS
        # ----------------------------------------------------------------------
        logger.info("Migrating tollgates, sensors, distances, vehicles...")
        cur_tra.execute("SELECT * FROM tollgates")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Tollgate(gate_id=d["gate_id"], route=d["route"]))
        db.commit()

        cur_tra.execute("SELECT * FROM tollgate_distances")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.TollgateDistance(
                from_gate=d["from_gate"],
                to_gate=d["to_gate"],
                distance_km=d["distance_km"],
                min_travel_time_min=d["min_travel_time_min"]
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM sensors")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Sensor(
                id=d["id"],
                type=d["type"],
                location=d["location"],
                latitude=d["latitude"],
                longitude=d["longitude"],
                status=d.get("status", "ONLINE"),
                last_reading=d.get("last_reading", 0.0),
                expected_range_min=d.get("expected_range_min", 0.0),
                expected_range_max=d.get("expected_range_max", 100.0),
                confidence=d.get("confidence", 1.0),
                anomaly_detected=bool(d.get("anomaly_detected", 0)),
                last_heartbeat=str(d.get("last_heartbeat", models._utcnow_iso()))
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM vehicles")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Vehicle(tag_id=d["tag_id"], vehicle_plate=d["vehicle_plate"]))
        db.commit()

        cur_tra.execute("SELECT * FROM scans")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Scan(
                transaction_id=d.get("transaction_id"),
                tag_id=d["tag_id"],
                vehicle_plate=d["vehicle_plate"],
                tollgate_id=d["tollgate_id"],
                lane_id=d.get("lane_id"),
                direction=d.get("direction", "INBOUND"),
                status=d.get("status", "success"),
                reason=d.get("reason"),
                timestamp=str(d.get("timestamp", models._utcnow_iso())),
                route_id=d.get("route_id")
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM anomalies")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Anomaly(
                transaction_id=d.get("transaction_id"),
                tag_id=d["tag_id"],
                vehicle_plate=d["vehicle_plate"],
                from_gate=d["from_gate"],
                to_gate=d["to_gate"],
                lane_id=d.get("lane_id"),
                actual_time_min=d["actual_time_min"],
                min_travel_time_min=d["min_travel_time_min"],
                reason=d["reason"],
                severity=d.get("severity", "MEDIUM"),
                status=d.get("status", "pending"),
                override_by=d.get("override_by"),
                override_reason=d.get("override_reason"),
                override_at=str(d.get("override_at")) if d.get("override_at") else None,
                detected_at=str(d.get("detected_at", models._utcnow_iso())),
                is_resolved=bool(d.get("is_resolved", 0))
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 3. CAMERAS & ASSETS RECONCILIATION
        # ----------------------------------------------------------------------
        logger.info("Reconciling cameras and assets...")
        cur_tra.execute("SELECT * FROM cameras")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Camera(
                id=d["id"],
                name=d["name"],
                location=d["location"],
                latitude=d.get("latitude"),
                longitude=d.get("longitude"),
                status=d.get("status", "ONLINE"),
                fps=d.get("fps", 30.0),
                latency_ms=d.get("latency_ms", 42.0),
                resolution=d.get("resolution", "1920x1080"),
                last_heartbeat=str(d.get("last_heartbeat", models._utcnow_iso())),
                updated_at=models._utcnow_iso()
            ))
        db.commit()

        # Merge securox traffic_cameras
        cur_sec.execute("SELECT * FROM traffic_cameras")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            cam = db.query(models.Camera).filter_by(id=d["id"]).first()
            if not cam:
                db.add(models.Camera(
                    id=d["id"],
                    name=d["name"],
                    location=d["location"],
                    stream_url=d.get("stream_url"),
                    status=d.get("status", "ONLINE"),
                    fps=d.get("fps", 30.0),
                    incident_count=d.get("incident_count", 0),
                    updated_at=d.get("updated_at", models._utcnow_iso())
                ))
            else:
                if d.get("stream_url"):
                    cam.stream_url = d["stream_url"]
                if d.get("incident_count"):
                    cam.incident_count = d["incident_count"]
        db.commit()

        cur_tra.execute("SELECT * FROM assets")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.Asset(
                id=d["id"],
                asset_type=d.get("asset_type", "INFRASTRUCTURE"),
                name=d["name"],
                domain="TRAFFIC",
                ip_address=d.get("ip_address"),
                mac_address=d.get("mac_address"),
                location=d.get("location"),
                status=d.get("status", "ONLINE"),
                risk_score=d.get("risk_score", 0.0),
                criticality=d.get("criticality", "MEDIUM"),
                firmware_version=d.get("firmware_version"),
                last_seen=models._utcnow_iso()
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 4. TRAFFIC SIGNALS RECONCILIATION
        # ----------------------------------------------------------------------
        logger.info("Reconciling traffic signals...")
        traffic_sig_map = {}
        cur_tra.execute("SELECT * FROM traffic_signals")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            traffic_sig_map[d["id"]] = d

        cur_sec.execute("SELECT * FROM traffic_signals")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            sig_id = d["id"]
            tra_extra = traffic_sig_map.get(sig_id, {})
            
            db.add(models.TrafficSignal(
                id=sig_id,
                intersection_id=tra_extra.get("intersection_id"),
                intersection=d.get("intersection", tra_extra.get("intersection_id")),
                zone=d.get("zone", "Central"),
                controller_id=tra_extra.get("controller_id", f"CTRL-{sig_id}"),
                current_state=d.get("current_state", "RED"),
                cycle_time_sec=d.get("cycle_time_sec", 90),
                cycle_time=tra_extra.get("cycle_time", 90),
                timing_plan=tra_extra.get("timing_plan", "FIXED"),
                mode=d.get("mode", "AUTO"),
                status=tra_extra.get("status", "ONLINE"),
                is_tampered=bool(d.get("is_tampered", 0)),
                is_compromised=bool(tra_extra.get("is_compromised", 0)),
                last_override_by=d.get("last_override_by"),
                last_command_time=str(tra_extra.get("last_command_time")) if tra_extra.get("last_command_time") else None,
                updated_at=d.get("updated_at", models._utcnow_iso())
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 5. USERS & RBAC RECONCILIATION
        # ----------------------------------------------------------------------
        logger.info("Reconciling users and credentials...")
        cur_sec.execute("SELECT * FROM users")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.User(
                id=d["id"],
                username=d["username"],
                email=f"{d['username']}@securox.city",
                full_name=d.get("full_name") or d["username"].replace("_", " ").title(),
                hashed_password=d["hashed_password"],
                role=d["role"].upper(),
                is_active=bool(d.get("is_active", 1)),
                created_at=d.get("created_at", models._utcnow_iso()),
                last_login_at=d.get("last_login_at")
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM users")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            usr = db.query(models.User).filter_by(username=d["username"]).first()
            if not usr:
                db.add(models.User(
                    id=f"usr-{d['username']}",
                    username=d["username"],
                    email=d.get("email"),
                    full_name=d.get("full_name", d["username"]),
                    hashed_password=d["password_hash"],
                    salt=d.get("salt"),
                    role=d.get("role", "OPERATOR").upper(),
                    is_active=bool(d.get("is_active", 1)),
                    failed_logins=d.get("failed_logins", 0),
                    risk_score=d.get("risk_score", 0.0),
                    created_at=str(d.get("created_at", models._utcnow_iso()))
                ))
            else:
                if d.get("email"):
                    usr.email = d["email"]
                if d.get("failed_logins"):
                    usr.failed_logins = d["failed_logins"]
                if d.get("risk_score"):
                    usr.risk_score = d["risk_score"]
        db.commit()

        roles_data = [
            ("ADMIN", "Full platform administrative privilege"),
            ("CISO", "Chief Information Security Officer executive overview"),
            ("SOC_ANALYST", "Security operations investigation and alert handling"),
            ("ANALYST", "Security data and forensic analysis"),
            ("OPERATOR", "Municipal and traffic systems operations"),
            ("TRAFFIC_OPERATOR", "Traffic signal and corridor operations"),
            ("DOCTOR", "Clinical patient record access"),
            ("NURSE", "Emergency and patient vital signs updates"),
            ("FINANCE_OPERATOR", "Fintech and transaction security management"),
            ("AUDITOR", "Read-only independent security and compliance audit"),
            ("VIEWER", "Read-only monitoring dashboard access")
        ]
        for role_id, desc in roles_data:
            db.add(models.Role(id=role_id, name=role_id, description=desc, is_system=True))
        db.commit()

        # ----------------------------------------------------------------------
        # 6. INCIDENTS & TIMELINES RECONCILIATION
        # ----------------------------------------------------------------------
        logger.info("Reconciling incidents and timelines...")
        cur_sec.execute("SELECT * FROM incidents")
        inc_batch = []
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            inc_batch.append(models.Incident(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                title=d["title"],
                severity=d.get("severity", "MEDIUM"),
                type="SECURITY",
                status=d.get("status", "OPEN"),
                asset=d.get("asset"),
                domain="SOC",
                owner=d.get("owner"),
                detected_at=d.get("timestamp", models._utcnow_iso()),
                payload=d.get("payload")
            ))
            if len(inc_batch) >= 1000:
                db.add_all(inc_batch)
                db.commit()
                inc_batch = []
        if inc_batch:
            db.add_all(inc_batch)
            db.commit()

        cur_tra.execute("SELECT * FROM incidents")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            inc_id = d["incident_id"]
            if not db.query(models.Incident).filter_by(id=inc_id).first():
                db.add(models.Incident(
                    id=inc_id,
                    timestamp=str(d.get("detected_at", models._utcnow_iso())),
                    title=d["title"],
                    severity=d.get("severity", "HIGH"),
                    type=d.get("type", "TRAFFIC_CYBER"),
                    status=d.get("status", "OPEN"),
                    asset_id=d.get("asset_id"),
                    location=d.get("location"),
                    domain="TRAFFIC",
                    risk_score=d.get("risk_score", 0.0),
                    detected_at=str(d.get("detected_at", models._utcnow_iso())),
                    acknowledged_at=str(d.get("acknowledged_at")) if d.get("acknowledged_at") else None,
                    resolved_at=str(d.get("resolved_at")) if d.get("resolved_at") else None,
                    description=d.get("description"),
                    is_escalated=bool(d.get("is_escalated", 0))
                ))
        db.commit()

        cur_tra.execute("SELECT * FROM incident_timelines")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.IncidentTimeline(
                incident_id=d["incident_id"],
                timestamp=str(d.get("timestamp", models._utcnow_iso())),
                title=d["title"],
                description=d.get("description"),
                event_type=d.get("event_type", "NOTE"),
                severity=d.get("severity", "INFO"),
                source=d.get("source", "SYSTEM")
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 7. AUDIT LOGS RECONCILIATION
        # ----------------------------------------------------------------------
        logger.info("Reconciling audit logs...")
        cur_sec.execute("SELECT * FROM audit_logs")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.AuditLog(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                actor=d.get("actor") or d.get("actor_username"),
                actor_id=d.get("actor_id"),
                actor_username=d.get("actor_username") or d.get("actor"),
                actor_role=d.get("actor_role"),
                action=d.get("action", "UNKNOWN"),
                target=d.get("target") or d.get("resource_type"),
                resource_type=d.get("resource_type") or d.get("target") or "GLOBAL",
                resource_id=d.get("resource_id"),
                decision=d.get("decision", "ALLOW"),
                reason=d.get("reason"),
                ip_address=d.get("ip_address"),
                user_agent=d.get("user_agent"),
                details=d.get("details") or d.get("payload"),
                payload=d.get("payload") or d.get("details") or "{}",
                details_json=d.get("details_json") or d.get("payload"),
                created_at=d.get("created_at") or d.get("timestamp") or models._utcnow_iso()
            ))
        db.commit()

        cur_tra.execute("SELECT * FROM audit_logs")
        for r in cur_tra.fetchall():
            d = _row_to_dict(cur_tra, r)
            db.add(models.AuditLog(
                id=f"tra-audit-{d['id']}",
                timestamp=str(d.get("timestamp", models._utcnow_iso())),
                actor=d.get("username"),
                actor_id=d.get("user_id"),
                actor_username=d.get("username"),
                user_id=d.get("user_id"),
                username=d.get("username"),
                action=d.get("action", "UNKNOWN"),
                target=d.get("target_id") or d.get("target_type"),
                target_type=d.get("target_type"),
                target_id=d.get("target_id"),
                resource_type=d.get("target_type", "TRAFFIC"),
                resource_id=d.get("target_id"),
                decision="ALLOW" if d.get("success", 1) else "DENY",
                ip_address=d.get("ip_address"),
                details=d.get("details_json"),
                details_json=d.get("details_json"),
                payload=d.get("details_json") or "{}",
                success=int(d.get("success", 1)),
                created_at=str(d.get("timestamp", models._utcnow_iso()))
            ))
        db.commit()

        # ----------------------------------------------------------------------
        # 8. HEALTHCARE, FINANCE, ALERTS, RISK HISTORY (BATCH INSERTS)
        # ----------------------------------------------------------------------
        logger.info("Migrating patients, medical records, ambulances...")
        cur_sec.execute("SELECT * FROM patients")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.Patient(
                id=d["id"],
                hospital_id=d.get("hospital_id", "HOSP-CITY-01"),
                name=d["name"],
                age=d["age"],
                gender=d["gender"],
                department=d["department"],
                assigned_doctor_id=d.get("assigned_doctor_id"),
                assigned_nurse_id=d.get("assigned_nurse_id"),
                room_bed=d.get("room_bed", ""),
                condition=d.get("condition", "STABLE"),
                admission_date=d.get("admission_date", models._utcnow_iso()),
                vital_signs_json=d.get("vital_signs_json"),
                updated_at=d.get("updated_at", models._utcnow_iso())
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM medical_records")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.MedicalRecord(
                id=d["id"],
                patient_id=d["patient_id"],
                doctor_id=d["doctor_id"],
                diagnosis=d["diagnosis"],
                prescriptions=d.get("prescriptions", "[]"),
                lab_results=d.get("lab_results", "[]"),
                treatment_notes=d.get("treatment_notes", ""),
                sensitivity=d.get("sensitivity", "RESTRICTED"),
                created_at=d.get("created_at", models._utcnow_iso())
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM ambulances")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.Ambulance(
                id=d["id"],
                driver_id=d.get("driver_id"),
                vehicle_number=d.get("vehicle_number", ""),
                call_sign=d.get("call_sign") or d.get("vehicle_number"),
                current_location=d.get("current_location", ""),
                destination_hospital=d.get("destination_hospital"),
                patient_priority=d.get("patient_priority", "NORMAL"),
                status=d.get("status", "AVAILABLE"),
                assigned_patient_id=d.get("assigned_patient_id"),
                eta_minutes=d.get("eta_minutes", 0),
                latitude=d.get("latitude"),
                longitude=d.get("longitude"),
                updated_at=d.get("updated_at", models._utcnow_iso())
            ))
        db.commit()

        logger.info("Migrating bank accounts and transactions...")
        cur_sec.execute("SELECT * FROM bank_accounts")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.BankAccount(
                id=d["id"],
                customer_id=d["customer_id"],
                account_number=d["account_number"],
                account_type=d.get("account_type", "SAVINGS"),
                balance=d.get("balance", 0.0),
                currency=d.get("currency", "INR"),
                branch=d.get("branch", "HEADQUARTERS"),
                status=d.get("status", "ACTIVE"),
                risk_rating=d.get("risk_rating", "LOW"),
                created_at=d.get("created_at", models._utcnow_iso())
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM bank_transactions")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.BankTransaction(
                id=d["id"],
                account_id=d["account_id"],
                sender_name=d["sender_name"],
                receiver_account=d["receiver_account"],
                amount=d["amount"],
                channel=d.get("channel", "UPI"),
                transaction_type=d.get("transaction_type", "TRANSFER"),
                risk_score=d.get("risk_score", 0.0),
                decision=d.get("decision", "APPROVE"),
                is_fraud=int(d.get("is_fraud", 0)),
                is_sar=int(d.get("is_sar", 0)),
                beneficiary_age_hours=float(d.get("beneficiary_age_hours", 720.0)),
                device_id=d.get("device_id"),
                ip_address=d.get("ip_address"),
                timestamp=d.get("timestamp") or d.get("created_at") or models._utcnow_iso(),
                created_at=d.get("created_at") or d.get("timestamp") or models._utcnow_iso(),
            ))
        db.commit()
        cur_sec.execute("SELECT * FROM security_policies")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.SecurityPolicy(
                id=d["id"],
                name=d["name"],
                domain=d.get("domain", "GLOBAL"),
                rule_definition=d["rule_definition"],
                risk_modifier=d.get("risk_modifier", 0.0),
                action=d.get("action", "ALLOW"),
                description=d.get("description", ""),
                is_active=bool(d.get("is_active", 1))
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM simulations")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.Simulation(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                scenario_id=d["scenario_id"],
                target_asset=d["target_asset"],
                attack_type=d["attack_type"],
                intensity=d.get("intensity", 1.0),
                duration=d.get("duration", 60.0),
                events_generated=d.get("events_generated", 0),
                status=d.get("status", "COMPLETED"),
                payload=d["payload"]
            ))
        db.commit()

        db.add(models.SimulationState(
            id="active_state",
            scenario_id="",
            status="IDLE",
            current_stage=0,
            stage_name="Idle",
            elapsed_seconds=0.0,
            events_emitted=0,
            state_blob="{}",
            updated_at=models._utcnow_iso()
        ))
        db.commit()

        db.add(models.AMLGraphState(
            id="primary",
            graph_name="SmartCityFintechGraph",
            node_count=12,
            edge_count=24,
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
            ]),
            updated_at=models._utcnow_iso()
        ))
        db.commit()

        cur_sec.execute("SELECT * FROM campaigns")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.Campaign(
                id=d["id"],
                title=d["title"],
                stages=d.get("stages", "[]"),
                affected_assets=d.get("affected_assets", "[]"),
                risk_score=d.get("risk_score", 0.0),
                confidence=d.get("confidence", 0.0),
                status=d.get("status", "ACTIVE"),
                first_seen=d.get("first_seen", models._utcnow_iso()),
                last_seen=d.get("last_seen", models._utcnow_iso()),
                payload=d["payload"]
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM cross_domain_threats")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.CrossDomainThreat(
                id=d["id"],
                threat_actor_ip=d["threat_actor_ip"],
                device_id=d["device_id"],
                domains_involved=d.get("domains_involved", "[]"),
                first_seen=d.get("first_seen", models._utcnow_iso()),
                last_seen=d.get("last_seen", models._utcnow_iso()),
                risk_score=d.get("risk_score", 0.0),
                campaign_summary=d.get("campaign_summary", ""),
                status=d.get("status", "DETECTED")
            ))
        db.commit()

        # Mitigations & Response Actions
        cur_sec.execute("SELECT * FROM mitigations")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.Mitigation(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                asset=d.get("asset", ""),
                playbook=d.get("playbook", ""),
                status=d.get("status", "PENDING"),
                payload=d["payload"]
            ))
        db.commit()

        cur_sec.execute("SELECT * FROM response_actions")
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            db.add(models.ResponseAction(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                action=d["action"],
                target_asset=d["target_asset"],
                before_risk=d.get("before_risk", 0.0),
                after_risk=d.get("after_risk", 0.0),
                verification_metrics=d.get("verification_metrics"),
                actor=d.get("actor", "SYSTEM"),
                status=d.get("status", "EXECUTED"),
                payload=d["payload"]
            ))
        db.commit()

        # Migrate alerts and fraud alerts in batches
        logger.info("Migrating alerts and fraud alerts (batching for high throughput)...")
        cur_sec.execute("SELECT * FROM alerts")
        alert_batch = []
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            alert_batch.append(models.Alert(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                asset=d.get("asset", "unknown"),
                severity=d.get("severity", "LOW"),
                risk_score=d.get("risk_score", 0.0),
                risk_category=d.get("risk_category", "LOW"),
                anomaly_score=d.get("anomaly_score", 0.0),
                scenario=d.get("scenario"),
                payload=d["payload"]
            ))
            if len(alert_batch) >= 2000:
                db.add_all(alert_batch)
                db.commit()
                alert_batch = []
        if alert_batch:
            db.add_all(alert_batch)
            db.commit()

        cur_sec.execute("SELECT * FROM fraud_alerts")
        fraud_batch = []
        for r in cur_sec.fetchall():
            d = _row_to_dict(cur_sec, r)
            fraud_batch.append(models.FraudAlert(
                id=d["id"],
                timestamp=d.get("timestamp", models._utcnow_iso()),
                transaction_id=d["transaction_id"],
                channel=d.get("channel", "UPI"),
                severity=d.get("severity", "MEDIUM"),
                risk_score=d.get("risk_score", 0.0),
                decision=d.get("decision", "REVIEW"),
                payload=d["payload"]
            ))
            if len(fraud_batch) >= 2000:
                db.add_all(fraud_batch)
                db.commit()
                fraud_batch = []
        if fraud_batch:
            db.add_all(fraud_batch)
            db.commit()

        logger.info("All tables migrated and reconciled successfully into single authoritative database!")

    finally:
        db.close()
        conn_sec.close()
        conn_tra.close()


if __name__ == "__main__":
    run_migration()
