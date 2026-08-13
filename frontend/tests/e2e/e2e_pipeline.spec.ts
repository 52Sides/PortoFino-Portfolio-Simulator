import { test, expect } from '@playwright/test';

test('login → simulate → history → report pipeline', async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  const email = `pipeline-${Date.now()}@test.com`;

  // Sign up
  await page.click("text=Sign up");
  await expect(page.getByText('Cancel')).toBeVisible();

  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill("pass123");
  await page.getByTestId('signup-submit').click()
  await expect(page.getByText('Logout')).toBeVisible({ timeout: 5000 });
  await expect(page.getByText('Cancel')).not.toBeVisible();

  await page.fill("textarea", "AAPL-L-100% 2020-01-01 2020-12-31");
  const simulateResponsePromise = page.waitForResponse(
    (response) => response.url().includes('/api/simulate/') && response.request().method() === 'POST',
    { timeout: 30000 }
  );
  await page.click("text=Simulate");
  const simulateResponse = await simulateResponsePromise;
  expect(simulateResponse.ok()).toBeTruthy();

  await expect(
    page
      .locator('text=Sharpe Ratio')
      .or(page.locator('text=Simulation failed'))
      .or(page.locator('text=Simulation error'))
  ).toBeVisible({ timeout: 90000 });
  await expect(page.locator('text=Sharpe Ratio')).toBeVisible();

  await page.getByText('History').click();
  await expect(page.getByText('Simulation History')).toBeVisible();
  await page.getByText('View').first().click();
  await expect(page.getByText('Close')).toBeVisible();
  await page.click("text=Close");

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download').click(),
  ]);

  expect(await download.path()).not.toBeNull();
});
