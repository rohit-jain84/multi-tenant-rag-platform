import { test, expect } from '@playwright/test';

test.describe('Sidebar Navigation', () => {
  test('should load with Query page as default route', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL('/query');
    await expect(page.locator('h1')).toHaveText('Query Playground');
  });

  test('should navigate to all pages via sidebar links', async ({ page }) => {
    await page.goto('/');

    const routes = [
      { name: 'Documents', path: '/documents', heading: 'Documents' },
      { name: 'Query', path: '/query', heading: 'Query Playground' },
      { name: 'Evaluation', path: '/eval', heading: 'Evaluation Dashboard' },
      { name: 'Tenants', path: '/tenants', heading: 'Tenant Management' },
      { name: 'Health', path: '/health', heading: 'System Health' },
    ];

    for (const route of routes) {
      await page.getByRole('link', { name: route.name }).click();
      await expect(page).toHaveURL(route.path);
      await expect(page.locator('h1')).toHaveText(route.heading);
    }
  });

  test('should highlight active nav item', async ({ page }) => {
    await page.goto('/health');
    const healthLink = page.getByRole('link', { name: 'Health' });
    await expect(healthLink).toHaveClass(/bg-primary/);
  });

  test('should collapse and expand sidebar', async ({ page }) => {
    await page.goto('/query');

    // Sidebar should show full text initially
    await expect(page.getByText('RAG Platform')).toBeVisible();

    // Click collapse button
    const collapseButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    const sidebar = page.locator('aside, nav').first();

    // Find the sidebar collapse toggle (chevron button at the bottom)
    const toggleButton = sidebar.locator('button').last();
    await toggleButton.click();

    // After collapse, "RAG Platform" text should be hidden
    await expect(page.getByText('RAG Platform')).toBeHidden();
  });

  test('should redirect unknown routes to /query', async ({ page }) => {
    await page.goto('/nonexistent-page');
    await expect(page).toHaveURL('/query');
  });
});
