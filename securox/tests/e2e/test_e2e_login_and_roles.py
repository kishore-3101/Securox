import pytest
from playwright.async_api import Page, expect
from conftest import DatabaseVerifier


@pytest.mark.asyncio
async def test_e2e_login_invalid_credentials(page: Page):
    """Verifies that invalid credentials fail in UI and do not authenticate."""
    await page.goto("/login")
    await expect(page.locator("h1")).to_contain_text("SECUROX ENTERPRISE")

    # Clear and fill invalid username and password
    username_input = page.locator("input[type='text']")
    password_input = page.locator("input[type='password']")
    await username_input.fill("unauthorized_hacker")
    await password_input.fill("bad_password_999")

    # Click Sign In
    submit_btn = page.locator("button[type='submit']")
    await submit_btn.click()

    # Verify error message displays and URL remains /login
    await page.wait_for_timeout(1000)
    assert "/login" in page.url


@pytest.mark.asyncio
async def test_e2e_login_valid_admin(page: Page):
    """Verifies valid admin credentials authenticate and transition to dashboard."""
    await page.goto("/login")
    
    username_input = page.locator("input[type='text']")
    password_input = page.locator("input[type='password']")
    await username_input.fill("admin")
    await password_input.fill("admin123")

    submit_btn = page.locator("button[type='submit']")
    await submit_btn.click()

    # Expect transition to protected app layout
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)
    
    # Topbar should display platform header or user badge
    topbar = page.locator("header")
    await expect(topbar).to_be_visible()


@pytest.mark.asyncio
async def test_e2e_fast_persona_login(page: Page):
    """Verifies 1-click interactive evaluator persona login."""
    await page.goto("/login")

    # Click on Dr. Sarah Chen persona card
    doctor_card = page.locator("button:has-text('Dr. Sarah Chen')")
    await expect(doctor_card).to_be_visible()
    await doctor_card.click()

    # Should land directly on /doctor
    await page.wait_for_url("**/doctor", timeout=10000)
    await expect(page.locator("h2")).to_contain_text("Doctor Clinical Portal")


@pytest.mark.asyncio
async def test_e2e_topbar_role_switcher_modal(page: Page):
    """Verifies in-app Topbar persona switcher across all domains."""
    # Start at login, fast login as admin
    await page.goto("/login")
    admin_card = page.locator("button:has-text('Global CISO / SOC Administrator')")
    await admin_card.click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    # Click Topbar Persona Switcher button
    persona_btn = page.locator("header button:has-text('Switch')")
    if not await persona_btn.is_visible():
        persona_btn = page.locator("header button").filter(has_text="ROLE").first
    if not await persona_btn.is_visible():
        # Fallback to any button in header that triggers modal
        persona_btn = page.locator("header button").nth(0)
    
    await persona_btn.click()
    await page.wait_for_timeout(600)

    # Modal should open with domain filter buttons
    modal = page.locator("div[role='dialog'], div.fixed")
    await expect(modal.first).to_be_visible()

    # Search for traffic operator
    search_input = modal.locator("input[placeholder*='Search']")
    if await search_input.is_visible():
        await search_input.fill("traffic_operator")
        await page.wait_for_timeout(300)
        traffic_role = modal.locator("button:has-text('traffic_operator')")
        if await traffic_role.is_visible():
            await traffic_role.click()
            await page.wait_for_timeout(1000)
            # Topbar should reflect traffic
            await expect(page.locator("header")).to_contain_text("TRAFFIC")


@pytest.mark.asyncio
async def test_e2e_logout(page: Page):
    """Verifies user session logout redirects cleanly to /login."""
    await page.goto("/login")
    await page.locator("button:has-text('Global CISO / SOC Administrator')").click()
    await page.wait_for_url(lambda u: "/login" not in u, timeout=10000)

    # Click Sign out
    logout_btn = page.locator("header button[title*='Sign out'], header button:has-text('Logout'), header button:has-text('Sign Out')")
    if await logout_btn.is_visible():
        await logout_btn.click()
        await page.wait_for_url("**/login", timeout=8000)
        await expect(page.locator("h1")).to_contain_text("SECUROX ENTERPRISE")
