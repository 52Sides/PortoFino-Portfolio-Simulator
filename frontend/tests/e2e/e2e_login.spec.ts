import { test, expect } from '@playwright/test'

test('user can log in and see History button', async ({ page }) => {
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

  await page.waitForTimeout(500)
  await expect(page.getByText('Logout')).toBeVisible();
  await page.click("text=Logout");
  await expect(page.getByText('Sign up')).toBeVisible()
})
