import { Page } from '@playwright/test';

export async function closeModalIfExists(page: Page) {
  // Любая модалка
  const overlay = page.locator('div.fixed.inset-0');
  if (!(await overlay.isVisible().catch(() => false))) return;

  // Кнопка Cancel (обычно ошибка при Sign up)
  const cancel = page.getByText('Cancel', { exact: true });
  if (await cancel.isVisible().catch(() => false)) {
    await cancel.click();
    await page.waitForTimeout(150);
    return;
  }

  // Кнопка Close (History → View)
  const close = page.getByText('Close', { exact: true });
  if (await close.isVisible().catch(() => false)) {
    await close.click();
    await page.waitForTimeout(150);
    return;
  }
}
