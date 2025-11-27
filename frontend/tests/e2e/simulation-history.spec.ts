import { test, expect } from '@playwright/test'

test.describe('Full flow: login → simulate → history → detail', () => {
  test('should login, simulate, and view history detail', async ({ page }) => {
    await page.goto('http://localhost:5173')

    await page.click('text=Log in')
    await page.fill('input[type="email"]', 'demo@test.com')
    await page.fill('input[type="password"]', 'pass123')
    await page.click('text=Log in')
    await page.waitForTimeout(1000)
    await page.fill('textarea', 'AAPL-L-100% 2020-01-01 2021-01-01')
    await page.click('text=Simulate')
    await expect(page.locator('text=Running Simulation...')).toBeVisible()
    await page.waitForSelector('text=Sharpe', { timeout: 10000 })
    await page.click('text=History')
    await expect(page.locator('table')).toBeVisible()
    await page.click('text=View')
    await expect(page.locator('text=Back to History')).toBeVisible()
    await expect(page.locator('text=CAGR')).toBeVisible()
    await expect(page.locator('canvas')).toBeVisible()
  })
})
