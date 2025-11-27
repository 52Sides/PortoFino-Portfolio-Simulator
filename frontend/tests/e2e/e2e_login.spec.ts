import { test, expect } from '@playwright/test'

test('user can sign up, log in, see Logout, then log out', async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  // Sign up
  await page.click("text=Sign up");
  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Sign up");

  // Log in
  await page.click("text=Log in");
  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Log in");

  await expect(page.getByText('Logout')).toBeVisible();

  // Logout
  await page.click("text=Logout");
  await expect(page.getByText('Sign up')).toBeVisible();
});
