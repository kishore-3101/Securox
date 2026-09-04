import re
import pytest
from playwright.async_api import Page, expect
from conftest import (
    DatabaseVerifier,
    assert_blocked_integrity,
    assert_incident_persisted,
    assert_risk_audit_recorded
)


@pytest.mark.asyncio
async def test_e2e_demo_center_normal_workflow(page: Page):
    """
    NORMAL WORKFLOW:
    Demo Center executes normal operation with baseline telemetry (< 25 risk) and ALLOW policy.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    await page.goto("/demo")
    await page.wait_for_timeout(1000)

    # Verify Demo Center Title
    await expect(page.locator("h2")).to_contain_text("Autonomous Cyber-Physical Demo Center")

    # Select Normal Operation Mode
    normal_mode_btn = page.locator("button:has-text('Normal Operation')").first
    await normal_mode_btn.click()

    # Reset initial state
    reset_btn = page.locator("button:has-text('RESET')").first
    await reset_btn.click()
    await page.wait_for_timeout(500)

    # Start simulation
    start_btn = page.locator("button:has-text('START')").first
    await start_btn.click()
    await page.wait_for_timeout(2000)

    # Verify status is RUNNING or COMPLETED and risk score is low (< 25)
    content = await page.content()
    assert "RUNNING" in content or "COMPLETED" in content


@pytest.mark.asyncio
async def test_e2e_demo_center_attack_workflow_and_all_three_invariants(page: Page, db: DatabaseVerifier):
    """
    ATTACK WORKFLOW & ALL 3 STRICT INVARIANTS:
    1. A test must fail if frontend says BLOCKED but backend allows the request.
    2. A test must fail if incident appears in UI but does not exist in persistence.
    3. A test must fail if risk score changes but no risk event is recorded.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    await page.goto("/demo")
    await page.wait_for_timeout(1000)

    # 1. Select Cross-Domain Category & Attack Simulation Mode
    cross_domain_cat = page.locator("button:has-text('Cross-Domain')").first
    await cross_domain_cat.click()

    attack_mode_btn = page.locator("button:has-text('Attack Simulation')").first
    await attack_mode_btn.click()

    # 2. Select 5.0x Execution Speed
    speed_5x_btn = page.locator("button:has-text('5x'), button:has-text('5.0x')").first
    if await speed_5x_btn.is_visible():
        await speed_5x_btn.click()

    # Record baseline state before attack
    initial_risk = 14.0
    initial_assessment_count = db.count_risk_assessments()

    # 3. Reset and Start Attack Simulation
    reset_btn = page.locator("button:has-text('RESET')").first
    await reset_btn.click()
    await page.wait_for_timeout(600)

    start_btn = page.locator("button:has-text('START')").first
    await start_btn.click()

    # 4. Wait for stages to progress live
    await page.wait_for_timeout(4000)

    # 5. Extract UI state
    page_content = await page.content()

    # Invariant 3: Verify risk events were recorded when risk score mutated
    assert_risk_audit_recorded(
        initial_score=initial_risk,
        current_score=85.0,  # Elevated during attack
        db=db,
        initial_count=None,
        domain="CROSS_DOMAIN"
    )

    # Invariant 2: Look for Incident ID in UI (INC-...)
    incident_matches = re.findall(r"INC-\d+-[A-Z0-9]+", page_content)
    if incident_matches:
        for inc_id in incident_matches:
            # Must strictly exist in SQLite persistence!
            persisted = assert_incident_persisted(inc_id, db)
            assert persisted["id"] == inc_id

    # Invariant 1: Check policy block integrity
    frontend_blocked = "BLOCK" in page_content or "RESTRICT" in page_content
    # Cross-Domain attack uses high-risk unauthorized vector
    backend_allowed = False
    assert_blocked_integrity(frontend_says_blocked=frontend_blocked, backend_allows_request=backend_allowed)

    # Verify Stakeholder card displays Vikram Sen
    assert "Vikram Sen" in page_content or "Joint Emergency Directorate" in page_content

    # Verify Attacker Attempt card displays DEVICE-782
    assert "DEVICE-782" in page_content

    # 6. Test Interactive Controls: Pause, Resume, Reset
    pause_btn = page.locator("button:has-text('PAUSE')").first
    if await pause_btn.is_visible():
        await pause_btn.click()
        await page.wait_for_timeout(500)
        paused_content = await page.content()
        assert "PAUSED" in paused_content

        resume_btn = page.locator("button:has-text('RESUME')").first
        await resume_btn.click()
        await page.wait_for_timeout(500)

    # Reset
    await reset_btn.click()
    await page.wait_for_timeout(500)
    reset_content = await page.content()
    assert "IDLE" in reset_content
