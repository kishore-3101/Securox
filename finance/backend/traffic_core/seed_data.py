import json
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from traffic_core.traffic_db import SessionLocal, engine, Base
from traffic_core import traffic_models as models
from traffic_core.services.auth_service import hash_password

def seed_all_data(db: Session):
    # 1. Users
    if not db.query(models.User).first():
        users = [
            ("admin", "admin@securox.ai", "Chief Security Officer", "admin123", "ADMIN"),
            ("analyst", "analyst@securox.ai", "Senior Cyber Analyst", "analyst123", "ANALYST"),
            ("operator", "operator@securox.ai", "Traffic Operations Lead", "operator123", "OPERATOR"),
            ("executive", "exec@securox.ai", "Executive Director", "exec123", "EXECUTIVE"),
            ("viewer", "viewer@securox.ai", "External Auditor", "viewer123", "VIEWER")
        ]
        for uname, email, fname, pwd, role in users:
            h, s = hash_password(pwd)
            u = models.User(
                username=uname,
                email=email,
                full_name=fname,
                password_hash=h,
                salt=s,
                role=role,
                is_active=True,
                risk_score=10.0 if role != "ADMIN" else 5.0
            )
            db.add(u)
        db.commit()
        print("[Seeder] Created default user accounts.")

    # 2. Road Segments (NH44 corridor & Urban grid with geographic coordinates)
    if not db.query(models.RoadSegment).first():
        # Geographic coordinates centered around Bangalore-Hyderabad NH44 corridor
        roads_data = [
            {
                "id": "ROAD-NH44-01",
                "name": "NH44 Express Corridor (Sector 1 - North Tollgate)",
                "route_id": "NH44",
                "start_node": "TG-01",
                "end_node": "TG-02",
                "length_km": 14.2,
                "lanes": 6,
                "speed_limit_kmh": 100.0,
                "current_speed_kmh": 86.0,
                "current_volume": 260,
                "capacity": 450,
                "density_score": 42.0,
                "congestion_level": "FREE_FLOW",
                "coordinates": [[13.120, 77.580], [13.150, 77.590], [13.180, 77.605]]
            },
            {
                "id": "ROAD-NH44-02",
                "name": "NH44 Central Arterial (Sector 2 - Electronic City Flyover)",
                "route_id": "NH44",
                "start_node": "TG-02",
                "end_node": "TG-03",
                "length_km": 18.5,
                "lanes": 6,
                "speed_limit_kmh": 90.0,
                "current_speed_kmh": 54.0,
                "current_volume": 360,
                "capacity": 420,
                "density_score": 68.0,
                "congestion_level": "HEAVY",
                "coordinates": [[13.180, 77.605], [13.210, 77.618], [13.245, 77.632]]
            },
            {
                "id": "ROAD-NH44-03",
                "name": "NH44 Logistics Bypass (Sector 3 - Industrial Gate)",
                "route_id": "NH44",
                "start_node": "TG-03",
                "end_node": "TG-04",
                "length_km": 22.0,
                "lanes": 4,
                "speed_limit_kmh": 100.0,
                "current_speed_kmh": 88.0,
                "current_volume": 210,
                "capacity": 380,
                "density_score": 35.0,
                "congestion_level": "FREE_FLOW",
                "coordinates": [[13.245, 77.632], [13.280, 77.645], [13.315, 77.660]]
            },
            {
                "id": "ROAD-URBAN-01",
                "name": "Arterial Ring Road (Intersection 04 Junction)",
                "route_id": "URBAN-R1",
                "start_node": "INT-01",
                "end_node": "INT-02",
                "length_km": 8.0,
                "lanes": 4,
                "speed_limit_kmh": 60.0,
                "current_speed_kmh": 42.0,
                "current_volume": 310,
                "capacity": 400,
                "density_score": 58.0,
                "congestion_level": "MODERATE",
                "coordinates": [[13.140, 77.560], [13.160, 77.575], [13.175, 77.595]]
            },
            {
                "id": "ROAD-URBAN-02",
                "name": "Metro Transit Gateway (Central Hub)",
                "route_id": "URBAN-R2",
                "start_node": "INT-03",
                "end_node": "INT-04",
                "length_km": 6.5,
                "lanes": 4,
                "speed_limit_kmh": 50.0,
                "current_speed_kmh": 36.0,
                "current_volume": 290,
                "capacity": 350,
                "density_score": 52.0,
                "congestion_level": "MODERATE",
                "coordinates": [[13.175, 77.595], [13.190, 77.610], [13.205, 77.625]]
            }
        ]

        for r in roads_data:
            road_obj = models.RoadSegment(
                id=r["id"],
                name=r["name"],
                route_id=r["route_id"],
                start_node=r["start_node"],
                end_node=r["end_node"],
                length_km=r["length_km"],
                lanes=r["lanes"],
                speed_limit_kmh=r["speed_limit_kmh"],
                current_speed_kmh=r["current_speed_kmh"],
                current_volume=r["current_volume"],
                capacity=r["capacity"],
                density_score=r["density_score"],
                congestion_level=r["congestion_level"],
                coordinates_json=json.dumps(r["coordinates"])
            )
            db.add(road_obj)
        db.commit()
        print("[Seeder] Created Road Segments.")

    # 3. Intersections & Traffic Signals
    if not db.query(models.Intersection).first():
        intersections = [
            ("INT-01", "NH44 & Airport Expressway Interchange", 13.150, 77.590, "CTRL-INT01"),
            ("INT-02", "Tech Zone Arterial Junction", 13.180, 77.605, "CTRL-INT02"),
            ("INT-03", "Ring Road North Confluence", 13.210, 77.618, "CTRL-INT03"),
            ("INT-04", "Industrial Logistics Junction", 13.245, 77.632, "CTRL-INT04"),
            ("INT-12", "Central Metro Multi-Modal Interchange", 13.205, 77.610, "CTRL-INT12")
        ]
        for i_id, iname, lat, lng, cid in intersections:
            db.add(models.Intersection(
                id=i_id,
                name=iname,
                latitude=lat,
                longitude=lng,
                controller_id=cid,
                status="NORMAL",
                signal_phase="NORTH_SOUTH_GREEN",
                queue_length=random.randint(4, 12),
                risk_score=15.0
            ))
            db.add(models.TrafficSignal(
                id=f"SIG-{i_id}",
                intersection_id=i_id,
                controller_id=cid,
                current_state="GREEN",
                cycle_time=90,
                timing_plan="ADAPTIVE_PEAK_01",
                status="NORMAL"
            ))
        db.commit()
        print("[Seeder] Created Intersections and Signals.")

    # 4. Optical Cameras
    if not db.query(models.Camera).first():
        cameras = [
            ("CAM-01", "NH44 Toll Plaza Inbound Cam 1", "TG-01 Approach", 13.125, 77.582, "ONLINE", 30.0, 32.0),
            ("CAM-02", "NH44 Airport Overpass PTZ", "Sector 1 Flyover", 13.152, 77.591, "ONLINE", 30.0, 38.0),
            ("CAM-03", "Electronic City Gantry Camera", "Sector 2 KM 18", 13.182, 77.607, "ONLINE", 30.0, 42.0),
            ("CAM-04", "Tech Park Junction 360", "Intersection 02", 13.212, 77.620, "ONLINE", 30.0, 45.0),
            ("CAM-05", "Bypass Heavy Freight Cam", "TG-03 North Gate", 13.248, 77.634, "ONLINE", 28.0, 50.0),
            ("CAM-06", "NH44 KM 32 Speed Enforcement", "Sector 3 Corridor", 13.282, 77.647, "ONLINE", 30.0, 35.0),
            ("CAM-07", "Ring Road West Interchange", "Intersection 01", 13.142, 77.562, "ONLINE", 30.0, 40.0),
            ("CAM-08", "Central Plaza ANPR Gate", "Intersection 12", 13.207, 77.612, "ONLINE", 30.0, 36.0),
        ]
        for cid, cname, loc, lat, lng, st, fps, lat_ms in cameras:
            db.add(models.Camera(
                id=cid,
                name=cname,
                location=loc,
                latitude=lat,
                longitude=lng,
                status=st,
                fps=fps,
                latency_ms=lat_ms,
                resolution="1920x1080",
                vehicle_count=random.randint(25, 60),
                detection_confidence=0.94,
                network_health=98.0,
                security_health=96.0,
                risk_score=12.0,
                is_simulated=True
            ))
        db.commit()
        print("[Seeder] Created Cameras.")

    # 5. Sensors
    if not db.query(models.Sensor).first():
        sensors = [
            ("SEN-LOOP-01", "INDUCTIVE_LOOP", "NH44 KM 12 Inbound", 13.128, 77.583, 240.0, 98.5),
            ("SEN-RADAR-01", "RADAR", "Sector 1 High-Speed Zone", 13.155, 77.593, 85.0, 99.0),
            ("SEN-LOOP-02", "INDUCTIVE_LOOP", "Electronic City Exit", 13.185, 77.609, 320.0, 97.0),
            ("SEN-RADAR-02", "RADAR", "Intersection 12 Approach", 13.208, 77.613, 45.0, 98.0),
            ("SEN-BLUETOOTH-01", "BLUETOOTH", "Corridor Travel-Time Probe", 13.249, 77.635, 180.0, 95.0)
        ]
        for sid, stype, loc, lat, lng, val, qual in sensors:
            db.add(models.Sensor(
                id=sid,
                type=stype,
                location=loc,
                latitude=lat,
                longitude=lng,
                status="ONLINE",
                last_reading=val,
                expected_range_min=20.0,
                expected_range_max=400.0,
                confidence=0.96,
                data_quality_score=qual
            ))
        db.commit()
        print("[Seeder] Created Sensors.")

    # 6. Infrastructure Assets Catalog
    if not db.query(models.Asset).first():
        assets = [
            ("ASSET-CAM-01", "CAMERA", "Toll Plaza Inbound Camera 01", "192.168.10.21", "Sector 1 Toll", "HEALTHY", 10.0, "HIGH"),
            ("ASSET-CAM-04", "CAMERA", "Tech Park Junction Camera 04", "192.168.10.24", "Intersection 02", "HEALTHY", 12.0, "HIGH"),
            ("ASSET-CTRL-12", "TRAFFIC_CONTROLLER", "NTCIP Master Signal Controller 12", "192.168.10.84", "Intersection 12", "HEALTHY", 15.0, "CRITICAL"),
            ("ASSET-GATEWAY-01", "GATEWAY", "OT Field Edge Gateway 01", "192.168.10.1", "Sector 2 Substation", "HEALTHY", 8.0, "CRITICAL"),
            ("ASSET-SEN-LOOP-01", "SENSOR", "Inductive Loop Detector 01", "192.168.10.101", "NH44 KM 12", "HEALTHY", 5.0, "MEDIUM"),
            ("ASSET-SRV-CORE", "SERVER", "SECUROX Primary Telemetry Host", "10.0.4.15", "SOC Datacenter", "HEALTHY", 4.0, "CRITICAL")
        ]
        for aid, atype, aname, ip, loc, st, rsk, crit in assets:
            db.add(models.Asset(
                id=aid,
                asset_type=atype,
                name=aname,
                ip_address=ip,
                location=loc,
                status=st,
                risk_score=rsk,
                criticality=crit,
                firmware_version="v3.4.1-securox",
                last_seen=datetime.utcnow()
            ))
        db.commit()
        print("[Seeder] Created Infrastructure Assets.")

    # 7. Initial Baseline Incidents & Cyber Threats
    if not db.query(models.Incident).first():
        inc = models.Incident(
            incident_id="INC-2026-BASELINE-01",
            title="Periodic Morning Congestion & Ramp Metering Alert",
            severity="MEDIUM",
            type="TRAFFIC_CONGESTION",
            status="RESOLVED",
            asset_id="ROAD-NH44-02",
            location="Sector 2 - Electronic City Flyover",
            risk_score=48.0,
            detected_at=datetime.utcnow() - timedelta(hours=3),
            acknowledged_at=datetime.utcnow() - timedelta(hours=2, minutes=45),
            resolved_at=datetime.utcnow() - timedelta(hours=1, minutes=30),
            assigned_to="Operator Lead",
            evidence_json=json.dumps({"max_density": 72.0, "queue_length_m": 180}),
            root_cause="Scheduled morning commuter surge combined with minor delivery van stall.",
            resolution_notes="Van cleared by patrol. Flow restored to free-flow baseline."
        )
        db.add(inc)
        db.commit()

        # Add initial timeline
        db.add(models.IncidentTimeline(
            incident_id="INC-2026-BASELINE-01",
            timestamp=datetime.utcnow() - timedelta(hours=3),
            title="Congestion Density Flagged",
            description="Vehicle throughput reduced by 35% on NH44 Sector 2 approach.",
            event_type="TRAFFIC_ANOMALY",
            severity="MEDIUM",
            source="TRAFFIC_DENSITY_ENGINE"
        ))
        db.commit()

    # 8. Initial Audit Log
    if not db.query(models.AuditLog).first():
        db.add(models.AuditLog(
            timestamp=datetime.utcnow() - timedelta(minutes=15),
            user_id="1",
            username="admin",
            action="SYSTEM_INITIALIZATION",
            target_type="COMMAND_CENTER",
            target_id="SOC-CORE",
            details_json=json.dumps({"status": "SUCCESS", "version": "v2.4.0"}),
            ip_address="127.0.0.1",
            success=True
        ))
        db.commit()

    # 9. Toll Plazas
    if not db.query(models.Tollgate).first():
        plazas = [
            ("TG-01", "NH44 North Toll Plaza", "NH44"),
            ("TG-02", "Electronic City Flyover Plaza", "NH44"),
            ("TG-03", "Industrial Gate West", "NH44"),
            ("TG-04", "Ring Road Confluence Toll", "URBAN-R1")
        ]
        for gate_id, name, route in plazas:
            db.add(models.Tollgate(
                gate_id=gate_id,
                route=route
            ))
        db.commit()
        print("[Seeder] Created 4 Toll Plazas.")

if __name__ == "__main__":
    db = SessionLocal()
    seed_all_data(db)
    db.close()
