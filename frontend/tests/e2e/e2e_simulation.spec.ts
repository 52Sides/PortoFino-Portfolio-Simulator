import { test, expect } from '@playwright/test'

test('simulate → history → details flow', async ({ page }) => {
  await page.goto('http://localhost:5173/')
  await page.getByText('Log in').click()
  await page.fill('input[type="email"]', 't@test.com')
  await page.fill('input[type="password"]', 'pass123')
  await page.click('button[type="submit"]')
  await page.fill('textarea', 'AAPL-L-100% 2020-01-01 2020-12-31')
  await page.getByRole('button', { name: 'Simulate' }).click()
  await page.locator('text=Sharpe Ratio').waitFor({ timeout: 20000 })
  await page.getByText('History').click()
  await expect(page.getByText('Simulation History')).toBeVisible()
  await page.getByText('View').first().click()
  await expect(page.getByText('Back to History')).toBeVisible()
})
