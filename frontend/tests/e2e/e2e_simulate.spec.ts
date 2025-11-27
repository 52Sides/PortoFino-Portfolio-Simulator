import { test, expect } from '@playwright/test'

test("register → login → simulate portfolio", async ({ page }) => {
  await page.goto("http://localhost:5173/");
  await page.click("text=Sign up");
  await page.fill('input[name="email"]', "user@test.com");
  await page.fill('input[name="password"]', "pass123");
  await page.click("text=Register");
  await expect(page.getByText('Log in')).toBeVisible();

  await page.click("text=Log in");
  await page.fill('input[name="email"]', "user@test.com");
  await page.fill('input[name="password"]', "pass123");
  await page.click("text=Login");

  await page.fill("textarea", "AAPL-L-100% 2020-01-01 2020-12-31");
  await page.click("text=Simulate");
  await page.locator('text=Sharpe Ratio').waitFor({ timeout: 20000 })

  await page.getByText('History').click()
  await expect(page.getByText('Simulation History')).toBeVisible()
  await page.getByText('View').first().click()
  await expect(page.getByText('Back to History')).toBeVisible()
});
