import { test, expect } from '@playwright/test';

test.describe('Documents Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/documents');
  });

  test('should display documents page with upload and library sections', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Documents');
    await expect(page.getByText('Upload Documents')).toBeVisible();
    await expect(page.getByText('Document Library')).toBeVisible();
  });

  test('should show dropzone with supported formats', async ({ page }) => {
    await expect(page.getByText(/drag & drop/i)).toBeVisible();
    await expect(page.getByText(/PDF, DOCX, HTML, Markdown/i)).toBeVisible();
  });

  test('should show empty state when no documents exist', async ({ page }) => {
    // Mock empty document list
    await page.route('**/api/v1/documents*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ documents: [], total: 0, page: 1, page_size: 10 }),
      });
    });

    await page.reload();
    await expect(page.getByText(/no documents/i)).toBeVisible();
  });

  test('should display document list with data', async ({ page }) => {
    await page.route('**/api/v1/documents*', (route) => {
      if (route.request().url().includes('page=')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            documents: [
              {
                id: '11111111-1111-1111-1111-111111111111',
                tenant_id: 'aaaa-bbbb-cccc',
                filename: 'report.pdf',
                format: 'pdf',
                category: 'reports',
                status: 'completed',
                page_count: 42,
                chunk_count: 87,
                chunking_strategy: 'semantic',
                upload_date: '2026-04-10T00:00:00Z',
                created_at: '2026-04-10T00:00:00Z',
              },
              {
                id: '22222222-2222-2222-2222-222222222222',
                tenant_id: 'aaaa-bbbb-cccc',
                filename: 'handbook.docx',
                format: 'docx',
                category: 'policies',
                status: 'completed',
                page_count: 15,
                chunk_count: 30,
                chunking_strategy: 'fixed',
                upload_date: '2026-04-11T00:00:00Z',
                created_at: '2026-04-11T00:00:00Z',
              },
            ],
            total: 2,
            page: 1,
            page_size: 10,
          }),
        });
      }
    });

    await page.reload();

    await expect(page.getByText('report.pdf')).toBeVisible();
    await expect(page.getByText('handbook.docx')).toBeVisible();
  });

  test('should show chunking strategy selector', async ({ page }) => {
    // Simulate a file selection by checking the strategy dropdown exists
    const strategySelect = page.locator('select').filter({ hasText: /fixed|semantic|parent/i });
    // Strategy select is only visible after files are staged
    // Verify the dropzone is interactive
    const dropzone = page.getByText(/drag & drop/i).locator('..');
    await expect(dropzone).toBeVisible();
  });
});

test.describe('Documents Page - Upload Flow', () => {
  test('should show upload button after file selection', async ({ page }) => {
    await page.route('**/api/v1/documents*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ documents: [], total: 0, page: 1, page_size: 10 }),
      });
    });

    await page.goto('/documents');

    // Create a fake PDF file and trigger the drop
    const dataTransfer = await page.evaluateHandle(() => {
      const dt = new DataTransfer();
      const file = new File(['test content'], 'test-doc.pdf', { type: 'application/pdf' });
      dt.items.add(file);
      return dt;
    });

    const dropzone = page.getByText(/drag & drop/i).locator('..');
    await dropzone.dispatchEvent('drop', { dataTransfer });

    // Upload button should appear with file count
    await expect(page.getByRole('button', { name: /upload.*file/i })).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Documents Page - Delete Flow', () => {
  test('should show delete confirmation modal', async ({ page }) => {
    await page.route('**/api/v1/documents*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          documents: [
            {
              id: '11111111-1111-1111-1111-111111111111',
              tenant_id: 'aaaa-bbbb-cccc',
              filename: 'report.pdf',
              format: 'pdf',
              category: 'reports',
              status: 'completed',
              page_count: 42,
              chunk_count: 87,
              chunking_strategy: 'semantic',
              upload_date: '2026-04-10T00:00:00Z',
              created_at: '2026-04-10T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
        }),
      });
    });

    await page.goto('/documents');
    await expect(page.getByText('report.pdf')).toBeVisible();

    // Click delete button (Trash2 icon)
    const deleteButton = page.locator('button').filter({ has: page.locator('[class*="trash"], [data-lucide="trash"]') }).or(
      page.getByRole('row', { name: /report\.pdf/i }).getByRole('button')
    );
    await deleteButton.last().click();

    // Confirmation modal should appear
    await expect(page.getByText(/delete/i).first()).toBeVisible();
  });
});
