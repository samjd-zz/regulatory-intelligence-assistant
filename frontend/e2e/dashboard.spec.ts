import { test, expect } from '@playwright/test';

/**
 * Dashboard Page E2E Tests
 * Tests the main landing page functionality
 */

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display page title and subtitle', async ({ page }) => {
    // Check main heading
    await expect(page.getByRole('heading', { name: /regulatory intelligence assistant/i }))
      .toBeVisible();
    
    // Check subtitle
    await expect(page.getByText(/navigate complex regulations/i))
      .toBeVisible();
  });

  test('should display three action cards', async ({ page }) => {
    // Check all three main action cards
    await expect(page.getByRole('link', { name: /search regulations/i }))
      .toBeVisible();
    
    await expect(page.getByRole('link', { name: /ask questions/i }))
      .toBeVisible();
    
    await expect(page.getByRole('link', { name: /check compliance/i }))
      .toBeVisible();
  });

  test('should navigate to search page when clicking search card', async ({ page }) => {
    await page.getByRole('link', { name: /search regulations/i }).click();
    await expect(page).toHaveURL('/search');
  });

  test('should navigate to chat page when clicking chat card', async ({ page }) => {
    await page.getByRole('link', { name: /ask questions/i }).click();
    await expect(page).toHaveURL('/chat');
  });

  test('should navigate to compliance page when clicking compliance card', async ({ page }) => {
    await page.getByRole('link', { name: /check compliance/i }).click();
    await expect(page).toHaveURL('/compliance');
  });

  test('should display statistics section', async ({ page }) => {
    // Statistics section should be visible
    await expect(page.getByText(/quick stats/i)).toBeVisible();
  });

  test('should have proper page title', async ({ page }) => {
    await expect(page).toHaveTitle(/regulatory intelligence assistant/i);
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Focus on first interactive element
    await page.keyboard.press('Tab');
    
    // Should be able to navigate through action cards
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check that focus is visible (basic check)
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['A', 'BUTTON']).toContain(focused);
  });
});

test.describe('Dashboard Page - Responsive', () => {
  test('should display properly on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone size
    await page.goto('/');
    
    // Page should still be usable
    await expect(page.getByRole('heading', { name: /regulatory intelligence assistant/i }))
      .toBeVisible();
    
    // Cards should be visible
    await expect(page.getByRole('link', { name: /search regulations/i }))
      .toBeVisible();
  });

  test('should display properly on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad size
    await page.goto('/');
    
    await expect(page.getByRole('heading', { name: /regulatory intelligence assistant/i }))
      .toBeVisible();
  });
});
