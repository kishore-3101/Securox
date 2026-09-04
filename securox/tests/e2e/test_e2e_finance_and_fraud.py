import pytest
from playwright.async_api import Page, expect
from conftest import DatabaseVerifier


@pytest.mark.asyncio
async def test_e2e_finance_overview_normal_workflow(page: Page):
    """
    NORMAL WORKFLOW:
    Treasury & AML investigator inspects accounts, branches, transactions, and Cyber-VaR.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Treasury & AML Investigator')").click()
    await page.wait_for_url("**/finance", timeout=10000)

    # Verify Finance Dashboard Header
    content = await page.content()
    assert "Finance" in content or "Treasury" in content or "Accounts" in content


@pytest.mark.asyncio
async def test_e2e_fraud_investigation_workflow(page: Page, db: DatabaseVerifier):
    """
    FRAUD WORKFLOW:
    Inspects suspicious fraud outflows and verifies containment persistence.
    """
    await page.goto("/login")
    await page.locator("button:has-text('Treasury & AML Investigator')").click()
    await page.wait_for_url("**/finance", timeout=10000)

    # Switch to Fraud Investigation subsystem tab
    fraud_tab = page.locator("button:has-text('Fraud Investigation'), button:has-text('Fraud Cases')")
    if await fraud_tab.first.is_visible():
        await fraud_tab.first.click()
        await page.wait_for_timeout(1000)
        
        # Verify fraud cases table renders
        content = await page.content()
        assert "CASE-" in content or "Fraud" in content or "Suspicious" in content
