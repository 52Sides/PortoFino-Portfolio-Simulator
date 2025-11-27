import { test, expect, Page } from '@playwright/test';

test('user can sign up, log in, see Logout, then log out', async ({ page }) => {
  await page.goto("http://localhost:5173/", { timeout: 30000 });

  // Sign up
  await page.click("text=Sign up");
  await expect(page.getByText('Cancel')).toBeVisible();

  await page.getByPlaceholder("Email").fill("user@test.com");
  await page.getByPlaceholder("Password").fill("pass123");
  await page.getByTestId('signup-submit').click()

  // Модалка должна исчезнуть сама (если новый пользователь)
  await expect(page.getByText('Logout')).toBeVisible({ timeout: 3000 });

  // Logout
  await page.click("text=Logout");
  await expect(page.getByText('Sign up')).toBeVisible();
});
