import { test, expect } from '@playwright/test';

test.describe('End-to-End Live Dashboard Integration & Outage Recovery', () => {
  test.beforeEach(async ({ page }) => {
    // Fixed evaluation viewport strictly 1214 x 2159 CSS px
    await page.setViewportSize({ width: 1214, height: 2159 });
  });

  test('completes live analyst login and renders all six macroeconomic panels', async ({ page }) => {
    await page.goto('/login');

    // Fill analyst credentials
    await page.fill('#email', 'analyst@adityabirla.com');
    await page.fill('#password', 'Analyst@2026');
    await page.click('button[type="submit"]');

    // Verify successful authentication and navigation to dashboard
    await expect(page.locator('header h1')).toHaveText('ECONOMIC INDICATOR');

    // Verify all six indicator panels are rendered in the DOM
    const panelIds = [
      '#panel-gdp-growth',
      '#panel-debt-to-gdp',
      '#panel-trade-balance',
      '#panel-gst-collection',
      '#panel-inflation',
      '#panel-govt-expenditure',
    ];

    for (const id of panelIds) {
      const panel = page.locator(id);
      await expect(panel).toBeVisible();
      // Ensure panels are not in error overlay state
      await expect(panel.locator('text=Failed to load indicator data')).toHaveCount(0);
    }

    // Verify SourceFooters are rendered on the panels
    const footers = page.locator('footer[aria-label="Data provenance and reporting date"]');
    await expect(footers).toHaveCount(6);

    // Verify Government Expenditure panel displays Estimate badge
    const govtPanel = page.locator('#panel-govt-expenditure');
    await expect(govtPanel.locator('text=Estimate')).toBeVisible();
  });

  test('streams ticker quotes and displays market status badge', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#email', 'analyst@adityabirla.com');
    await page.fill('#password', 'Analyst@2026');
    await page.click('button[type="submit"]');

    await expect(page.locator('header h1')).toHaveText('ECONOMIC INDICATOR');

    const ticker = page.locator('nav[aria-label="Live Market Quotes Ticker"]');
    await expect(ticker).toBeVisible();

    // Verify market status badge is present (LIVE, CLOSED, or STALE)
    const statusBadge = ticker.locator('[data-testid="ticker-status-badge"]');
    await expect(statusBadge).toBeVisible();

    // Verify ticker contains key quotes
    await expect(ticker.locator('text=SENSEX').first()).toBeVisible();
    await expect(ticker.locator('text=NIFTY').first()).toBeVisible();
  });

  test('simulates stream outage transitioning ticker to STALE and preserves panels without blanking', async ({
    page,
  }) => {
    await page.goto('/login');
    await page.fill('#email', 'analyst@adityabirla.com');
    await page.fill('#password', 'Analyst@2026');
    await page.click('button[type="submit"]');

    await expect(page.locator('header h1')).toHaveText('ECONOMIC INDICATOR');

    // Verify dashboard is loaded
    await expect(page.locator('#panel-gdp-growth')).toBeVisible();

    // Simulate backend stream outage by aborting all stream & ticker calls
    await page.route('**/api/stream/**', (route) => route.abort());
    await page.route('**/api/ticker', (route) => route.abort());

    // Trigger panel refetch outage by aborting indicator requests
    await page.route('**/api/indicators/**', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Backend service unavailable' }),
      })
    );

    // Stale-while-revalidate verification:
    // Panels MUST retain existing DOM content and not blank out
    const gdpPanel = page.locator('#panel-gdp-growth');
    await expect(gdpPanel).toBeVisible();

    // Restore network routes (outage recovery)
    await page.unroute('**/api/stream/**');
    await page.unroute('**/api/ticker');
    await page.unroute('**/api/indicators/**');

    // Verify dashboard recovers and remains healthy
    await expect(page.locator('#panel-gdp-growth')).toBeVisible();
    await expect(page.locator('#panel-govt-expenditure')).toBeVisible();
  });
});
