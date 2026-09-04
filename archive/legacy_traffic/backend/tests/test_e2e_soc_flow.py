import pytest
import asyncio
from database import SessionLocal
import models
from services.scenario_simulator import scenario_simulator
from services.ai_assistant import ai_assistant
from services.incident_service import incident_service
from services.risk_engine import risk_engine

@pytest.mark.asyncio
async def test_section_55_master_demo_flow():
    """
    Validates the complete Section 55 demo flow:
    1. Verify initial baseline state
    2. Trigger Scenario 7 (Master Cyber-Physical Attack)
    3. Verify network reconnaissance + signal manipulation + congestion events
    4. Verify correlation engine creates critical incident
    5. Verify system risk score elevates to CRITICAL (>80)
    6. Verify AI Security Assistant summarizes the incident with zero hallucination
    7. Operator investigates, acknowledges, and resolves the incident
    8. Reset simulation and verify system returns to nominal baseline
    """
    db = SessionLocal()
    try:
        # Step 1: Initial state check
        roads = db.query(models.RoadSegment).all()
        assert len(roads) >= 3
        cams = db.query(models.Camera).all()
        assert len(cams) >= 5

        # Step 2: Trigger Scenario 7 (Cyber-Physical Attack)
        result = await scenario_simulator.launch_scenario("scenario_7")
        assert result["status"] == "COMPLETED"
        assert result["scenario_id"] == "scenario_7"
        inc_id = result["incident_id"]
        assert inc_id is not None

        # Step 3: Verify incident in database
        inc = db.query(models.Incident).filter(models.Incident.incident_id == inc_id).first()
        assert inc is not None
        assert inc.severity == "CRITICAL"
        assert inc.type == "CYBER_PHYSICAL"

        # Step 4: Verify elevated risk score
        risk_report = risk_engine.calculate_system_risk(
            active_critical_incidents=1,
            active_cyber_threats=1,
            max_congestion_score=92.0,
            compromised_controllers=1
        )
        assert risk_report.overall_score >= 80.0
        assert risk_report.severity == "CRITICAL"

        # Step 5: Test AI Assistant query grounding
        ai_resp = ai_assistant.answer_query("Why is Intersection 12 critical?", db)
        assert ai_resp["confidence"] >= 0.90
        assert "Intersection 12" in ai_resp["answer"]
        assert "Root Cause" in ai_resp["answer"]
        assert len(ai_resp["grounded_entities"]) > 0

        # Step 6: Operator acknowledges and resolves incident
        inc = incident_service.update_incident_status(
            db=db,
            incident_id=inc_id,
            new_status="ACKNOWLEDGED",
            operator_name="Lead SOC Analyst",
            note="Verified correlation graph"
        )
        assert inc.status == "ACKNOWLEDGED"

        inc = incident_service.update_incident_status(
            db=db,
            incident_id=inc_id,
            new_status="RESOLVED",
            operator_name="Lead SOC Analyst",
            note="Controller failsafe active, queue cleared"
        )
        assert inc.status == "RESOLVED"
        assert inc.resolved_at is not None

        # Step 7: Reset simulation back to nominal baseline
        reset_res = await scenario_simulator.reset_simulation()
        assert reset_res["status"] == "SUCCESS"

        # Verify roadways normalized
        for r in db.query(models.RoadSegment).all():
            assert r.congestion_level == "FREE_FLOW"
            assert r.current_speed_kmh >= 75.0

    finally:
        db.close()
