import { test, expect } from '@playwright/test'
import fs from 'fs'

test('download XLSX report', async ({ page, context }) => {
  await page.goto('http://localhost:5173/')

  await page.getByText('Log in').click()
  await page.fill('input[type="email"]', 't@test.com')
  await page.fill('input[type="password"]', 'pass123')
  await page.click('button[type="submit"]')

  await page.getByText('History').click()
  await expect(page.getByText('View')).toBeVisible()
  await expect(page.getByText('Download')).toBeVisible()

