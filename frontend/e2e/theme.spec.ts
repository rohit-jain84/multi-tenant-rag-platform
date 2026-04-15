import { test, expect } from '@playwright/test';

test.describe('Theme Toggle', () => {
  test('should default to light mode', async ({ page }) => {
    await page.goto('/query');
    const html = page.locator('html');
    // Light mode: no 'dark' class on html element
    await expect(html).not.toHaveClass(/dark/);
  });

  test('should toggle to dark mode and back', async ({ page }) => {
    await page.goto('/query');
    const html = page.locator('html');

    // Find theme toggle button in header (Moon/Sun icon)
    const themeButton = page.locator('header button').last();
    await themeButton.click();

    // Should now be dark mode
    await expect(html).toHaveClass(/dark/);

    // Toggle back to light
    await themeButton.click();
    await expect(html).not.toHaveClass(/dark/);
  });

  test('should persist theme preference across navigation', async ({ page }) => {
    await page.goto('/query');
    const html = page.locator('html');

    // Switch to dark mode
    const themeButton = page.locator('header button').last();
    await themeButton.click();
    await expect(html).toHaveClass(/dark/);

    // Navigate to another page
    await page.getByRole('link', { name: 'Health' }).click();
    await expect(page).toHaveURL('/health');

    // Dark mode should persist
    await expect(html).toHaveClass(/dark/);
  });

  test('should persist theme in localStorage', async ({ page }) => {
    await page.goto('/query');

    // Toggle to dark
    const themeButton = page.locator('header button').last();
    await themeButton.click();

    const stored = await page.evaluate(() => localStorage.getItem('rag_theme'));
    expect(stored).toBe('dark');

    // Toggle back to light
    await themeButton.click();
    const storedLight = await page.evaluate(() => localStorage.getItem('rag_theme'));
    expect(storedLight).toBe('light');
  });
});
