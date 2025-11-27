import { test, expect } from '@playwright/test'
import fs from 'fs'

test("login → simulate → history → report", async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  // Login
  await page.click("text=Log in");
  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Log in");

  await expect(page.getByText('Logout')).toBeVisible();

  // Run simulation
  await page.fill("textarea", "AAPL-L-100% 2020-01-01 2020-12-31");
  await page.click("text=Simulate");
  await page.locator('text=Sharpe Ratio').waitFor({ timeout: 20000 });

  // History
  await page.getByText('History').click();
  await expect(page.getByText('Simulation History')).toBeVisible();
  await expect(page.getByText('View')).toBeVisible();
  await expect(page.getByText('Download')).toBeVisible();

  // View details
  await page.getByText('View').first().click();
  await expect(page.getByText('Close')).toBeVisible();
  await page.click("text=Close");
  await expect(page.getByText('View')).toBeVisible();

  // Download report
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download').first().click()
  ]);

  // Wait backend to finish WS processing
  await page.waitForTimeout(10000);

  const path = await download.path();
  expect(path).not.toBeNull();

  if (path) {
    const content = fs.readFileSync(path);
    expect(content.length).toBeGreaterThan(0);
  }
});
