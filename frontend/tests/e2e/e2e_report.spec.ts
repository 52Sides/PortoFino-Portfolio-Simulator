import { test, expect } from '@playwright/test'
import fs from 'fs'

test('download XLSX report', async ({ page, context }) => {
  // Main page
  await page.goto('http://localhost:5173/')

  // Login
  await page.getByText('Log in').click()
  await page.fill('input[type="email"]', 't@test.com')
  await page.fill('input[type="password"]', 'pass123')
  await page.click('button[type="submit"]')

  // Move to history
  await page.getByText('History').click()
  await expect(page.getByText('View')).toBeVisible()
  await expect(page.getByText('Download')).toBeVisible()

  // Waiting for download report
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByText('Download').click()
  ])

  // Check that file exists
  const path = await download.path()
  expect(path).not.toBeNull()

  if (path) {
    const content = fs.readFileSync(path)
    expect(content.length).toBeGreaterThan(0)
  }
})
