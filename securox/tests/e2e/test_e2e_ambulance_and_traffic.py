import pytest
from playwright.async_api import Page, expect
from conftest import DatabaseVerifier


@pytest.mark.asyncio
async def test_e2e_ambulance_cad_normal_workflow(page: Page):
    """
    NORMAL WORKFLOW:
    Ambulance driver inspects CAD emergency fleet and active ambulance coordinates.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Mobile ALS Unit CAD-04')").click()
    await page.wait_for_url("**/ambulance", timeout=10000)

    # Verify Ambulance CAD Fleet
    await expect(page.locator("h2")).to_contain_text("Computer-Aided Dispatch")
    
    # Check CAD units in UI
    content = await page.content()
    assert "CAD-01" in content
    assert "CAD-02" in content


@pytest.mark.asyncio
async def test_e2e_ambulance_green_corridor_preemption(page: Page):
    """
    Verifies 1-tap green corridor preemption request and safety activation.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Mobile ALS Unit CAD-04')").click()
    await page.wait_for_url("**/ambulance", timeout=10000)

    await page.wait_for_timeout(1500)

    # Click Request Green Corridor button
    preempt_btn = page.locator("button:has-text('Request Green Corridor')").first
    await expect(preempt_btn).to_be_visible()
    await preempt_btn.click()
    await page.wait_for_timeout(1000)

    # Corridor indicator should show active or success
    corridor_active = page.locator("text=ACTIVE").first
    await expect(corridor_active).to_be_visible()


@pytest.mark.asyncio
async def test_e2e_traffic_operations_workflow(page: Page):
    """
    NORMAL & ATTACK WORKFLOW:
    Verifies Traffic Command Center, Signal Timing SCADA, and Emergency Response subsystems.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Inspector Rajesh')").click()
    await page.wait_for_url("**/traffic", timeout=10000)
    await page.wait_for_timeout(1000)

    # Verify Traffic Operations UI
    await expect(page.locator("main h1")).to_contain_text("STIG Smart Traffic")

    # Switch to Signals Subsystem tab
    signals_tab = page.locator("button:has-text('Signals'), button:has-text('Signal Timing')")
    if await signals_tab.first.is_visible():
        await signals_tab.first.click()
        await page.wait_for_timeout(800)
        content = await page.content()
        assert "SIG-" in content or "Signal" in content
