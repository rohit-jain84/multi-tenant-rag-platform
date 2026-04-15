import { test, expect } from '@playwright/test';

test.describe('Tenants Page', () => {
  test.beforeEach(async ({ page }) => {
    // Clear auth state before each test
    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();
  });

  test('should display tenant management page', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Tenant Management');
    await expect(page.getByText('Manage tenants, API keys, and view usage statistics')).toBeVisible();
  });

  test('should show admin API key required banner when not connected', async ({ page }) => {
    await expect(page.getByText('Admin API key required')).toBeVisible();
    await expect(page.getByRole('button', { name: /set key/i })).toBeVisible();
  });

  test('should show admin key input when Set Key is clicked', async ({ page }) => {
    await page.getByRole('button', { name: /set key/i }).click();
    const input = page.locator('input[type="password"]');
    await expect(input).toBeVisible();
    await expect(page.getByRole('button', { name: /connect/i })).toBeVisible();
  });

  test('should disable New Tenant button when admin key is not set', async ({ page }) => {
    const newTenantButton = page.getByRole('button', { name: /new tenant/i });
    await expect(newTenantButton).toBeDisabled();
  });

  test('should show empty state when no tenants exist', async ({ page }) => {
    await expect(page.getByText(/no tenants/i)).toBeVisible();
  });
});

test.describe('Tenants Page - Admin Connected', () => {
  test('should accept admin key and show connected state', async ({ page }) => {
    // Mock the admin tenants endpoint to validate the key
    await page.route('**/api/v1/admin/tenants', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();

    await expect(page.getByText(/admin connected/i)).toBeVisible();
  });

  test('should enable New Tenant button after admin key is set', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();

    await expect(page.getByText(/admin connected/i)).toBeVisible();
    const newTenantButton = page.getByRole('button', { name: /new tenant/i });
    await expect(newTenantButton).toBeEnabled();
  });

  test('should open create tenant modal', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    // Connect admin
    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();
    await expect(page.getByText(/admin connected/i)).toBeVisible();

    // Open create tenant modal
    await page.getByRole('button', { name: /new tenant/i }).click();
    await expect(page.getByText('Tenant Name')).toBeVisible();
    await expect(page.getByRole('button', { name: /create/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
  });

  test('should create tenant and show API key', async ({ page }) => {
    const mockApiKey = 'rag_testkey123456789abcdef';

    await page.route('**/api/v1/admin/tenants', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenant: {
              id: '11111111-1111-1111-1111-111111111111',
              name: 'test-tenant',
              is_active: true,
              rate_limit_qpm: 60,
              created_at: new Date().toISOString(),
            },
            api_key: mockApiKey,
          }),
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      }
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    // Connect admin
    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();
    await expect(page.getByText(/admin connected/i)).toBeVisible();

    // Create tenant
    await page.getByRole('button', { name: /new tenant/i }).click();
    await page.getByPlaceholder(/acme/i).fill('test-tenant');
    await page.getByRole('button', { name: /create/i }).click();

    // Should show the generated API key
    await expect(page.getByText("Save this API key now")).toBeVisible();
    await expect(page.getByText(mockApiKey)).toBeVisible();
    await expect(page.getByRole('button', { name: /done/i })).toBeVisible();
  });

  test('should display tenant list with data', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '11111111-1111-1111-1111-111111111111',
            name: 'demo-tenant',
            is_active: true,
            rate_limit_qpm: 60,
            created_at: '2026-04-08T00:00:00Z',
          },
          {
            id: '22222222-2222-2222-2222-222222222222',
            name: 'test-tenant',
            is_active: true,
            rate_limit_qpm: 120,
            created_at: '2026-04-10T00:00:00Z',
          },
        ]),
      });
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    // Connect admin
    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();
    await expect(page.getByText(/admin connected/i)).toBeVisible();

    // Should display tenants in table
    await expect(page.getByText('demo-tenant')).toBeVisible();
    await expect(page.getByText('test-tenant')).toBeVisible();
  });

  test('should disconnect admin key', async ({ page }) => {
    await page.route('**/api/v1/admin/tenants', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/tenants');
    await page.evaluate(() => localStorage.removeItem('rag_auth'));
    await page.reload();

    // Connect admin
    await page.getByRole('button', { name: /set key/i }).click();
    await page.locator('input[type="password"]').fill('test-admin-key');
    await page.getByRole('button', { name: /connect/i }).click();
    await expect(page.getByText(/admin connected/i)).toBeVisible();

    // Disconnect
    const disconnectButton = page.locator('[title="Disconnect"]').or(
      page.getByText(/admin connected/i).locator('..').locator('button')
    );
    await disconnectButton.last().click();

    // Should revert to "Admin API key required"
    await expect(page.getByText('Admin API key required')).toBeVisible();
  });
});
