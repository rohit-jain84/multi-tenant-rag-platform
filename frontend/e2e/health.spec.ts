import { test, expect } from '@playwright/test';

test.describe('Health Page', () => {
  test('should display health page with service cards', async ({ page }) => {
    await page.goto('/health');

    await expect(page.locator('h1')).toHaveText('System Health');
    await expect(page.getByText('Service connectivity status')).toBeVisible();

    // Should show the three service cards
    await expect(page.getByText('PostgreSQL')).toBeVisible();
    await expect(page.getByText('Vector Database')).toBeVisible();
    await expect(page.getByText('Redis')).toBeVisible();
  });

  test('should display last checked timestamp', async ({ page }) => {
    await page.goto('/health');
    await expect(page.getByText(/Last checked:/)).toBeVisible();
  });

  test('should have a refresh button', async ({ page }) => {
    await page.goto('/health');
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should show overall status banner', async ({ page }) => {
    await page.goto('/health');

    // Should show one of the three possible statuses
    const statusTexts = [
      'All Systems Operational',
      'Service Degraded',
      'Unable to reach backend',
    ];
    const statusBanner = page.locator('text=/All Systems Operational|Service Degraded|Unable to reach backend/');
    await expect(statusBanner.first()).toBeVisible({ timeout: 10000 });
  });

  test('should show service descriptions', async ({ page }) => {
    await page.goto('/health');
    await expect(page.getByText('Relational store & metadata')).toBeVisible();
    await expect(page.getByText(/Qdrant/)).toBeVisible();
    await expect(page.getByText('Cache & rate limiting')).toBeVisible();
  });
});
