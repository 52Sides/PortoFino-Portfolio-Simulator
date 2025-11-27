import { Page } from '@playwright/test';

export async function closeModalIfExists(page: Page) {
  const modalOverlay = page.locator('div.fixed.inset-0');

  if (!(await modalOverlay.isVisible().catch(() => false))) {
    return;
  }

  const cancelBtn = page.getByText('Cancel', { exact: true });
  if (await cancelBtn.isVisible().catch(() => false)) {
    await cancelBtn.click();
    await page.waitForTimeout(200);
    return;
  }

  const closeIcon = page.locator('.modal-close, [data-test="close-modal"]');
  if (await closeIcon.isVisible().catch(() => false)) {
    await closeIcon.click();
    await page.waitForTimeout(200);
    return;
  }
}
