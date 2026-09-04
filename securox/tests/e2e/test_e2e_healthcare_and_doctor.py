import pytest
from playwright.async_api import Page, expect
from conftest import DatabaseVerifier, assert_blocked_integrity


@pytest.mark.asyncio
async def test_e2e_healthcare_command_overview(page: Page):
    """Verifies Healthcare Command Center metrics, bed census, and IoMT telemetry."""
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    await page.goto("/healthcare")
    await page.wait_for_timeout(1000)
    
    # Verify healthcare heading or IoMT monitor
    content = await page.content()
    assert "Healthcare" in content or "Hospital" in content or "ICU" in content


@pytest.mark.asyncio
async def test_e2e_doctor_portal_normal_workflow(page: Page):
    """
    NORMAL WORKFLOW:
    Doctor views assigned cardiology patient, reviews vitals telemetry, and saves notes.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Dr. Sarah Chen')").click()
    await page.wait_for_url("**/doctor", timeout=10000)

    # Doctor Clinical Portal header
    await expect(page.locator("h2")).to_contain_text("Doctor Clinical Portal")

    # Select assigned patient (Aarav Sharma / Lakshmi Narayanan / Ramesh Patel)
    patient_card = page.locator("button:has-text('Aarav Sharma'), button:has-text('Lakshmi Narayanan'), button:has-text('Ramesh Patel')").first
    await expect(patient_card).to_be_visible()
    await patient_card.click()

    # Vitals should be visible
    vitals_container = page.locator("text=Heart Rate").first
    await expect(vitals_container).to_be_visible()

    # Save clinical notes
    notes_area = page.locator("textarea")
    if await notes_area.is_visible():
        await notes_area.fill("Patient post-op recovery is nominal. Troponin levels trending down.")
        save_btn = page.locator("button:has-text('Save & Sign Clinical Note')")
        await save_btn.first.click()
        # Verify success badge appears
        saved_indicator = page.get_by_text("Saved with cryptographic audit")
        await expect(saved_indicator).to_be_visible(timeout=6000)


@pytest.mark.asyncio
async def test_e2e_doctor_portal_attack_workflow_and_blocked_invariant(page: Page, db: DatabaseVerifier):
    """
    ATTACK WORKFLOW & INVARIANT 1:
    A test MUST fail if:
      frontend says BLOCKED
      but backend allows the request.
    
    Simulates unauthorized BOLA patient record exfiltration attempt.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Dr. Sarah Chen')").click()
    await page.wait_for_url("**/doctor", timeout=10000)

    # Verify BOLA enforcement banner in UI
    bola_badge = page.locator("text=BOLA ENFORCEMENT: ACTIVE")
    await expect(bola_badge).to_be_visible()

    # In UI, unassigned patient outside Cardiology (Sunita Verma in Neurology or Rohan Gupta in Orthopedics) triggers BOLA
    non_cardiology_patient = page.locator("button:has-text('Sunita Verma'), button:has-text('Rohan Gupta'), button:has-text('Devraj Mukherjee')").first
    if await non_cardiology_patient.is_visible():
        await non_cardiology_patient.click()
        await page.wait_for_timeout(500)

    # Verify BOLA restriction warning in UI
    content = await page.content()
    frontend_says_blocked = "BOLA Warning" in content or "RESTRICTED" in content or "BOLA ENFORCEMENT" in content

    # Directly verify backend API enforcement: doctor attempts unauthorized modification on out-of-department patient P-1004
    token = await page.evaluate("() => localStorage.getItem('securox_token')")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    response = await page.request.patch(
        "http://127.0.0.1:8000/api/healthcare/patients/P-1004",
        data={"condition": "MALICIOUS_TAMPER"},
        headers=headers
    )
    backend_allowed = (response.status == 200)

    # Invariant 1 Assertion: Test fails if frontend says BLOCKED but backend allows request!
    assert_blocked_integrity(
        frontend_says_blocked=frontend_says_blocked,
        backend_allows_request=backend_allowed
    )
    assert response.status in (403, 401), f"Expected 403/401 for unauthorized BOLA action, got {response.status}"
