import { test, expect } from '@playwright/test'

test('user can log in and see History button', async ({ page }) => {
  await page.goto('http://localhost:5173/')
  await page.getByText('Log in').click()
  await page.waitForTimeout(500)
  await page.fill('input[type="email"]', 't@test.com')
  await page.fill('input[type="password"]', 'pass123')
  await page.click('button[type="submit"]')
  await expect(page.getByText('History')).toBeVisible()
})
