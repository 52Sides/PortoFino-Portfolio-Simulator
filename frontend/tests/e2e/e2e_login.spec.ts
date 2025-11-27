import { test, expect } from '@playwright/test';
import { closeModalIfExists } from './utils';

test('user can sign up, log in, see Logout, then log out', async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  await page.click("text=Sign up");

  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Sign up");

  await closeModalIfExists(page);

  await page.click("text=Log in");
  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.click("text=Login");

  await closeModalIfExists(page);

  await expect(page.getByText('Logout')).toBeVisible();
  await page.click("text=Logout");
  await expect(page.getByText('Sign up')).toBeVisible();
});
