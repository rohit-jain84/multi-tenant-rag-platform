import { test, expect } from '@playwright/test';

test.describe('Query Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/query');
  });

  test('should display query playground', async ({ page }) => {
    await expect(page.locator('h1')).toHaveText('Query Playground');
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible();
  });

  test('should have a textarea for question input', async ({ page }) => {
    const textarea = page.getByPlaceholder(/ask a question/i);
    await expect(textarea).toBeVisible();
    await expect(textarea).toBeEditable();
  });

  test('should have a send button', async ({ page }) => {
    // Send button is inside the form, identifiable by Send icon
    const form = page.locator('form');
    await expect(form).toBeVisible();
    const submitButton = form.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });

  test('should toggle advanced options panel', async ({ page }) => {
    // Advanced options are hidden by default
    const topKLabel = page.getByText(/top k/i);
    await expect(topKLabel).toBeHidden();

    // Click the settings button to show advanced options
    const settingsButton = page.locator('form button').first();
    await settingsButton.click();

    // Advanced options should now be visible
    await expect(page.getByText(/top k/i).first()).toBeVisible();
    await expect(page.getByText(/top n/i).first()).toBeVisible();

    // Toggle off
    await settingsButton.click();
    await expect(topKLabel).toBeHidden();
  });

  test('should type a question in the textarea', async ({ page }) => {
    const textarea = page.getByPlaceholder(/ask a question/i);
    await textarea.fill('What are the main findings?');
    await expect(textarea).toHaveValue('What are the main findings?');
  });
});

test.describe('Query Page - Query Submission', () => {
  test('should submit query and display answer', async ({ page }) => {
    // Mock the query endpoint
    await page.route('**/api/v1/query/stream', (route) => {
      const body = [
        'data: {"type": "token", "content": "The main"}',
        'data: {"type": "token", "content": " findings include"}',
        'data: {"type": "token", "content": " improved performance."}',
        'data: {"type": "citations", "content": [{"source_number": 1, "document_name": "report.pdf", "document_id": "d5e6f7g8", "page_number": 3, "chunk_text": "Performance improved by 40%.", "relevance_score": 0.92}]}',
        'data: {"type": "metadata", "content": {"latency": {"embedding_ms": 45, "retrieval_ms": 120, "reranking_ms": 300, "generation_ms": 2000, "total_ms": 2465}, "tokens": {"prompt_tokens": 1200, "completion_tokens": 150, "total_tokens": 1350, "estimated_cost": 0.00025}}}',
        'data: {"type": "done"}',
      ].join('\n\n');

      route.fulfill({
        status: 200,
        contentType: 'text/event-stream',
        body,
      });
    });

    await page.goto('/query');

    // Set up tenant auth via localStorage so the query can authenticate
    await page.evaluate(() => {
      localStorage.setItem(
        'rag_auth',
        JSON.stringify({
          tenantId: 'test-id',
          tenantName: 'test-tenant',
          apiKey: 'rag_testkey123',
          adminApiKey: null,
        })
      );
    });
    await page.reload();

    const textarea = page.getByPlaceholder(/ask a question/i);
    await textarea.fill('What are the main findings?');

    // Submit the form
    const submitButton = page.locator('form button[type="submit"]');
    await submitButton.click();

    // Answer should appear (either streamed or as final text)
    await expect(page.getByText(/main findings/i)).toBeVisible({ timeout: 10000 });
  });

  test('should display error state on query failure', async ({ page }) => {
    await page.route('**/api/v1/query/stream', (route) => {
      route.fulfill({ status: 401, body: 'Unauthorized' });
    });

    await page.goto('/query');

    const textarea = page.getByPlaceholder(/ask a question/i);
    await textarea.fill('Test query');

    const submitButton = page.locator('form button[type="submit"]');
    await submitButton.click();

    // Should show some form of error indication
    // Either an error toast or an error display in the answer area
    const errorIndicator = page.getByText(/error|unauthorized|api key/i).first();
    await expect(errorIndicator).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Query Page - Advanced Options', () => {
  test('should allow configuring top_k and top_n', async ({ page }) => {
    await page.goto('/query');

    // Open advanced options
    const settingsButton = page.locator('form button').first();
    await settingsButton.click();

    // Find and modify top_k input
    const topKInput = page.locator('input[type="number"]').first();
    await topKInput.clear();
    await topKInput.fill('10');
    await expect(topKInput).toHaveValue('10');

    // Find and modify top_n input
    const topNInput = page.locator('input[type="number"]').nth(1);
    await topNInput.clear();
    await topNInput.fill('3');
    await expect(topNInput).toHaveValue('3');
  });

  test('should allow selecting chunking strategy', async ({ page }) => {
    await page.goto('/query');

    // Open advanced options
    const settingsButton = page.locator('form button').first();
    await settingsButton.click();

    const strategySelect = page.locator('select');
    await expect(strategySelect).toBeVisible();

    // Change strategy
    await strategySelect.selectOption('semantic');
    await expect(strategySelect).toHaveValue('semantic');
  });
});
