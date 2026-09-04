import asyncio
import pytest
from fastapi.testclient import TestClient

from main import app
from services.demo_center_engine import (
    demo_center_engine,
    DemoCategory,
    DemoMode,
    DemoStage,
    DemoStatus,
    STAGE_ORDER,
    STAKEHOLDERS
)

client = TestClient(app)


@pytest.mark.asyncio
async def test_demo_center_initial_state():
    status = demo_center_engine.get_status()
    assert "session_id" in status
    assert "status" in status
    assert "risk" in status
    assert "stakeholder" in status
    assert "attacker_attempt" in status
    assert "system_prevented" in status
    assert len(status["stages"]) == 9


@pytest.mark.asyncio
async def test_demo_center_start_pause_resume_reset():
    # Start
    res_start = await demo_center_engine.start(DemoCategory.HEALTHCARE, DemoMode.ATTACK, speed=5.0)
    assert res_start["status"] == "RUNNING"
    assert res_start["category"] == "HEALTHCARE"
    assert res_start["mode"] == "ATTACK"

    # Pause
    res_pause = await demo_center_engine.pause()
    assert res_pause["status"] == "PAUSED"

    # Resume
    res_resume = await demo_center_engine.resume()
    assert res_resume["status"] == "RUNNING"

    # Speed change
    res_speed = await demo_center_engine.set_speed(2.0)
    assert res_speed["speed"] == 2.0

    # Reset
    res_reset = await demo_center_engine.reset()
    assert res_reset["status"] == "IDLE"
    assert res_reset["risk"]["current_score"] == 14.0


@pytest.mark.asyncio
async def test_demo_center_all_four_categories():
    categories = [
        DemoCategory.HEALTHCARE,
        DemoCategory.TRAFFIC,
        DemoCategory.FINANCE,
        DemoCategory.CROSS_DOMAIN
    ]
    for cat in categories:
        res = await demo_center_engine.start(cat, DemoMode.ATTACK, speed=5.0)
        assert res["category"] == cat.value
        assert res["stakeholder"]["name"] == STAKEHOLDERS[cat]["name"]
        assert res["stakeholder"]["role"] == STAKEHOLDERS[cat]["role"]
        await demo_center_engine.reset()


@pytest.mark.asyncio
async def test_demo_center_nine_stage_progression():
    # Step through all 9 stages manually on engine
    await demo_center_engine.start(DemoCategory.HEALTHCARE, DemoMode.ATTACK, speed=5.0)
    
    for stage in STAGE_ORDER:
        await demo_center_engine._execute_stage(stage)
        status = demo_center_engine.get_status()
        assert status["risk"]["current_score"] > 0
    
    final_status = demo_center_engine.get_status()
    assert len(final_status["events_timeline"]) > 0
    assert "stage_data" in final_status
    await demo_center_engine.reset()


@pytest.mark.asyncio
async def test_demo_center_risk_score_dynamics():
    # Attack mode: risk increases to CRITICAL
    await demo_center_engine.start(DemoCategory.FINANCE, DemoMode.ATTACK, speed=5.0)
    await demo_center_engine._execute_stage(DemoStage.EVENT)
    await demo_center_engine._execute_stage(DemoStage.DETECTION)
    await demo_center_engine._execute_stage(DemoStage.AI_ANALYSIS)
    await demo_center_engine._execute_stage(DemoStage.RISK)
    status_attack = demo_center_engine.get_status()
    assert status_attack["risk"]["current_score"] >= 80.0
    assert status_attack["risk"]["tier"] == "CRITICAL"
    await demo_center_engine.reset()

    # Recovery mode: risk drops back to baseline
    await demo_center_engine.start(DemoCategory.FINANCE, DemoMode.RECOVERY, speed=5.0)
    await demo_center_engine._execute_stage(DemoStage.RECOVERY)
    status_recovery = demo_center_engine.get_status()
    assert status_recovery["risk"]["current_score"] < 20.0
    assert status_recovery["risk"]["tier"] == "LOW"
    await demo_center_engine.reset()


@pytest.mark.asyncio
async def test_demo_center_decision_reason_attribution():
    await demo_center_engine.start(DemoCategory.TRAFFIC, DemoMode.ATTACK, speed=5.0)
    await demo_center_engine._execute_stage(DemoStage.RISK)
    status = demo_center_engine.get_status()
    reason = status["decision_reason"]
    assert "composite_score" in reason
    assert "factors" in reason
    assert len(reason["factors"]) >= 2
    # Verify presence of specific expected factor points
    factor_names = [f["name"] for f in reason["factors"]]
    assert any("device" in fn or "location" in fn or "volume" in fn for fn in factor_names)
    await demo_center_engine.reset()


@pytest.mark.asyncio
async def test_demo_center_attacker_attempt_vs_system_prevented():
    await demo_center_engine.start(DemoCategory.CROSS_DOMAIN, DemoMode.ATTACK, speed=5.0)
    status = demo_center_engine.get_status()
    assert "DEVICE-782" in status["attacker_attempt"]["vector"]
    assert "COORDINATED ATTACK INDICATOR" in status["system_prevented"]["action"]
    await demo_center_engine.reset()


def test_api_demo_center_scenarios():
    resp = client.get("/api/demo-center/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["categories"]) == 4
    assert len(data["modes"]) == 3
    assert len(data["stages"]) == 9


def test_api_demo_center_lifecycle_endpoints():
    # 1. Start via API
    resp_start = client.post("/api/demo-center/start", json={
        "category": "HEALTHCARE",
        "mode": "ATTACK",
        "speed": 2.0
    })
    assert resp_start.status_code == 200
    assert resp_start.json()["status"] == "RUNNING"

    # 2. Get status
    resp_status = client.get("/api/demo-center/status")
    assert resp_status.status_code == 200
    assert resp_status.json()["category"] == "HEALTHCARE"

    # 3. Pause
    resp_pause = client.post("/api/demo-center/pause")
    assert resp_pause.status_code == 200
    assert resp_pause.json()["status"] == "PAUSED"

    # 4. Resume
    resp_resume = client.post("/api/demo-center/resume")
    assert resp_resume.status_code == 200
    assert resp_resume.json()["status"] == "RUNNING"

    # 5. Speed
    resp_speed = client.post("/api/demo-center/speed", json={"speed": 5.0})
    assert resp_speed.status_code == 200
    assert resp_speed.json()["speed"] == 5.0

    # 6. Reset
    resp_reset = client.post("/api/demo-center/reset")
    assert resp_reset.status_code == 200
    assert resp_reset.json()["status"] == "IDLE"
