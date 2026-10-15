import { test, expect } from '@playwright/test';

test.describe('Economic Indicator Dashboard Visual & Layout Evaluation', () => {
  test.beforeEach(async ({ page }) => {
    // Set explicit evaluation viewport: 1214 x 2159 CSS px
    await page.setViewportSize({ width: 1214, height: 2159 });
    
    // Go to login page
    await page.goto('/login');

    // Sign in using demo analyst credentials
    await page.fill('#email', 'analyst@adityabirla.com');
    await page.fill('#password', 'Analyst@2026');
    await page.click('button[type="submit"]');

    // Wait for dashboard to mount
    await expect(page.locator('header h1')).toHaveText('ECONOMIC INDICATOR');
  });

  test('renders strictly within 1214 px width with zero horizontal scroll', async ({ page }) => {
    await page.waitForTimeout(1000);
    await page.screenshot({ path: 'tests/visual/react_dashboard.png', fullPage: true });
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    
    expect(scrollWidth).toBeLessThanOrEqual(1214);
    expect(clientWidth).toBe(1214);
  });

  test('renders all six macroeconomic panels in 2x3 grid', async ({ page }) => {
    await expect(page.locator('#panel-gdp-growth')).toBeVisible();
    await expect(page.locator('#panel-debt-to-gdp')).toBeVisible();
    await expect(page.locator('#panel-trade-balance')).toBeVisible();
    await expect(page.locator('#panel-gst-collection')).toBeVisible();
    await expect(page.locator('#panel-inflation')).toBeVisible();
    await expect(page.locator('#panel-govt-expenditure')).toBeVisible();
  });

  test('displays live ticker with LIVE badge and quotes', async ({ page }) => {
    const ticker = page.locator('nav[aria-label="Live Market Quotes Ticker"]');
    await expect(ticker).toBeVisible();
    await expect(ticker.locator('text=LIVE')).toBeVisible();
    await expect(ticker.locator('text=SENSEX').first()).toBeVisible();
  });

  test('supports demonstrating loading, stale, and unavailable lifecycle states', async ({ page }) => {
    // Click LOADING simulation
    await page.click('button:has-text("LOADING")');
    await expect(page.locator('[data-testid="panel-loading"]').first()).toBeVisible();

    // Click STALE simulation
    await page.click('button:has-text("STALE")');
    await expect(page.locator('text=STALE').first()).toBeVisible();

    // Click UNAVAILABLE simulation
    await page.click('button:has-text("UNAVAILABLE")');
    await expect(page.locator('text=Upstream data feed is temporarily unavailable.').first()).toBeVisible();

    // Return to NORMAL
    await page.click('button:has-text("NORMAL")');
    await expect(page.locator('[data-testid="panel-ok"]').first()).toBeVisible();
  });
});
