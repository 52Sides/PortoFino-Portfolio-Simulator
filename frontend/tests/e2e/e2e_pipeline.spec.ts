import { test, expect } from '@playwright/test';

async function closeModalIfExists(page) {
  const modalOverlay = page.locator('div.fixed.inset-0');
  if (await modalOverlay.isVisible().catch(() => false)) {
    const cancel = page.getByText('Cancel', { exact: true });
    if (await cancel.isVisible().catch(() => false)) {
      await cancel.click();
      await page.waitForTimeout(200);
    }
  }
}

test('login → simulate → history → report pipeline', async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  await closeModalIfExists(page);
  await closeModalIfExists(page);

  await page.click("text=Log in");

  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");

  await closeModalIfExists(page);
  await page.click("text=Login");

  await closeModalIfExists(page);

  await expect(page.getByText('Logout')).toBeVisible();

  await page.fill("textarea", "AAPL-L-100% 2020-01-01 2020-12-31");
  await page.click("text=Simulate");

  await page.locator('text=Sharpe Ratio').waitFor({ timeout: 20000 });

  await page.getByText('History').click();
  await expect(page.getByText('Simulation History')).toBeVisible();

  await page.getByText('View').first().click();
  await expect(page.getByText('Close')).toBeVisible();
  await page.getByText('Close').first().click();

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download').click()
  ]);

  expect(await download.path()).not.toBeNull();
});
