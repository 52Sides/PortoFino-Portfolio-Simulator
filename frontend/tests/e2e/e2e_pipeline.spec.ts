import { test, expect } from '@playwright/test';
import { closeModalIfExists } from '../utils/closeModal';

test('login → simulate → history → report pipeline', async ({ page }) => {
  await page.goto("http://localhost:5173", { timeout: 30000 });

  // Login
  await page.click("text=Log in");
  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Login");

  // Должно закрыться автоматически
  await expect(page.getByText('Logout')).toBeVisible();

  // Simulate
  await page.fill("textarea", "AAPL-L-100% 2020-01-01 2020-12-31");
  await page.click("text=Simulate");

  await page.locator('text=Sharpe Ratio').waitFor({ timeout: 20000 });

  // History
  await page.getByText('History').click();
  await expect(page.getByText('Simulation History')).toBeVisible();

  // View → Close
  await page.getByText('View').first().click();
  await expect(page.getByText('Close')).toBeVisible();
  await closeModalIfExists(page); // закрытие вручную

  // Download
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download').click(),
  ]);

  expect(await download.path()).not.toBeNull();
});
