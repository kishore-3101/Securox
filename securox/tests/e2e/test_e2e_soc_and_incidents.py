import pytest
from playwright.async_api import Page, expect
from conftest import DatabaseVerifier, assert_incident_persisted


@pytest.mark.asyncio
async def test_e2e_soc_command_center_normal_workflow(page: Page):
    """
    NORMAL WORKFLOW:
    SOC Command Center renders KPI posture cards, live alerts, and triage table.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    await page.goto("/soc")
    await page.wait_for_timeout(1000)

    # Check SOC header
    await expect(page.locator("h2")).to_contain_text("SOC Command Center")

    # Verify KPI stat cards are present
    content = await page.content()
    assert "Alerts" in content
    assert "Incidents" in content


@pytest.mark.asyncio
async def test_e2e_soc_incident_persistence_invariant(page: Page, db: DatabaseVerifier):
    """
    INVARIANT 2:
    A test MUST FAIL if:
      incident appears in UI
      but does not exist in persistence.
    
    Extracts every rendered incident ID from UI and asserts presence in SQLite store.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    await page.goto("/soc")
    await page.wait_for_timeout(1500)

    # Find all incident ID badges rendered in the page (INC-...)
    import re
    page_text = await page.content()
    incident_matches = list(set(re.findall(r"INC-\d+-[A-Z0-9]+", page_text)))

    # If any incident appears in UI, assert it strictly exists in persistence!
    for inc_id in incident_matches:
        persisted_inc = assert_incident_persisted(inc_id, db)
        assert persisted_inc["id"] == inc_id
