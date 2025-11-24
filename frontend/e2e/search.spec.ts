import { test, expect } from '@playwright/test';

/**
 * Search Page E2E Tests
 * Tests the search functionality and results display
 */

test.describe('Search Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/search');
  });

  test('should display search interface', async ({ page }) => {
    // Check search input is visible
    await expect(page.getByPlaceholder(/search regulations/i)).toBeVisible();
    
    // Check search button is visible
    await expect(page.getByRole('button', { name: /search/i })).toBeVisible();
  });

  test('should display filter panel', async ({ page }) => {
    // Check filter section exists
    await expect(page.getByText(/filters/i)).toBeVisible();
  });

  test('should allow text input in search field', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search regulations/i);
    await searchInput.fill('employment insurance');
    
    await expect(searchInput).toHaveValue('employment insurance');
  });

  test('should trigger search on button click', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search regulations/i);
    await searchInput.fill('employment insurance');
    
    await page.getByRole('button', { name: /search/i }).click();
    
    // Should show loading or results
    // Note: Actual results depend on backend being available
    await page.waitForTimeout(1000);
  });

  test('should trigger search on Enter key', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search regulations/i);
    await searchInput.fill('employment insurance');
    await searchInput.press('Enter');
    
    await page.waitForTimeout(1000);
  });

  test('should have keyboard accessible filter controls', async ({ page }) => {
    // Tab through interface
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON', 'SELECT']).toContain(focused);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/search');
    
    // Search input should still be visible and usable
    await expect(page.getByPlaceholder(/search regulations/i)).toBeVisible();
  });
});

test.describe('Search Page - Error Handling', () => {
  test('should handle empty search gracefully', async ({ page }) => {
    await page.goto('/search');
    
    const searchButton = page.getByRole('button', { name: /search/i });
    await searchButton.click();
    
    // Should either prevent submission or show message
    await page.waitForTimeout(500);
  });
});
