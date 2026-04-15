import { test, expect } from '@playwright/test';

test.describe('Evaluation Page', () => {
  test('should display evaluation dashboard', async ({ page }) => {
    await page.goto('/eval');
    await expect(page.locator('h1')).toHaveText('Evaluation Dashboard');
    await expect(page.getByText(/RAGAS evaluation metrics/i)).toBeVisible();
  });

  test('should have a refresh button', async ({ page }) => {
    await page.goto('/eval');
    const refreshButton = page.getByRole('button', { name: /refresh/i });
    await expect(refreshButton).toBeVisible();
  });

  test('should display score cards with mock data', async ({ page }) => {
    await page.route('**/api/v1/admin/eval/results*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: '11111111-1111-1111-1111-111111111111',
              run_id: 'eval-20260415-001',
              strategy: 'hybrid',
              reranking_enabled: true,
              faithfulness: 0.84,
              answer_relevancy: 0.79,
              context_precision: 0.81,
              context_recall: 0.88,
              per_question_results: null,
              created_at: '2026-04-15T10:00:00Z',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.goto('/eval');

    // Should display RAGAS metric values
    await expect(page.getByText('0.84').or(page.getByText('84'))).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('0.88').or(page.getByText('88'))).toBeVisible({ timeout: 5000 });
  });

  test('should show empty state when no eval results', async ({ page }) => {
    await page.route('**/api/v1/admin/eval/results*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [], total: 0 }),
      });
    });

    await page.goto('/eval');

    // Should show some indication that no evaluations have been run
    const emptyIndicator = page.getByText(/no eval|no results|run.*evaluation|no data/i).first();
    await expect(emptyIndicator).toBeVisible({ timeout: 5000 });
  });
});
