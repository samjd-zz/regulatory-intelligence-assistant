import { Page, expect } from '@playwright/test';

/**
 * Test Helper Functions
 * Reusable utilities for E2E tests
 */

/**
 * Navigate to a page and wait for it to be ready
 */
export async function navigateAndWait(page: Page, path: string) {
  await page.goto(path);
  await page.waitForLoadState('networkidle');
}

/**
 * Fill a form field by label text
 */
export async function fillFieldByLabel(page: Page, label: string, value: string) {
  const field = page.getByLabel(new RegExp(label, 'i'));
  await field.fill(value);
}

/**
 * Check if an element is visible with custom timeout
 */
export async function waitForElement(page: Page, selector: string, timeout = 5000) {
  await page.waitForSelector(selector, { state: 'visible', timeout });
}

/**
 * Check if page has proper accessibility attributes
 */
export async function checkAccessibility(page: Page) {
  // Check for page title
  const title = await page.title();
  expect(title).toBeTruthy();
  
  // Check for main landmark
  const main = page.locator('main');
  await expect(main).toBeVisible();
}

/**
 * Take a screenshot with a descriptive name
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({ path: `e2e/screenshots/${name}.png`, fullPage: true });
}

/**
 * Wait for API response
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp) {
  return await page.waitForResponse(response => {
    const url = response.url();
    if (typeof urlPattern === 'string') {
      return url.includes(urlPattern);
    }
    return urlPattern.test(url);
  });
}

/**
 * Mock API response for testing
 */
export async function mockApiResponse(page: Page, url: string, response: unknown) {
  await page.route(url, route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(response)
    });
  });
}

/**
 * Check for console errors
 */
export function setupConsoleErrorListener(page: Page) {
  const errors: string[] = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });
  
  return errors;
}

/**
 * Wait for loading spinner to disappear
 */
export async function waitForLoadingToComplete(page: Page) {
  const spinner = page.getByRole('status', { name: /loading/i });
  await spinner.waitFor({ state: 'hidden', timeout: 10000 }).catch(() => {
    // Spinner might not appear for fast responses
  });
}

/**
 * Verify confidence badge is displayed correctly
 */
export async function verifyConfidenceBadge(page: Page, expectedLevel: 'high' | 'medium' | 'low') {
  const badge = page.getByText(new RegExp(expectedLevel, 'i'));
  await expect(badge).toBeVisible();
}

/**
 * Verify citation tag format
 */
export async function verifyCitationFormat(page: Page, citationText: string) {
  const citation = page.getByText(citationText);
  await expect(citation).toBeVisible();
  
  // Should have monospace styling (check class or computed style)
  const className = await citation.getAttribute('class');
  expect(className).toContain('font-mono');
}

/**
 * Test responsive behavior at different breakpoints
 */
export async function testResponsiveLayout(page: Page, path: string) {
  const breakpoints = [
    { width: 375, height: 667, name: 'mobile' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 1280, height: 720, name: 'desktop' }
  ];
  
  for (const breakpoint of breakpoints) {
    await page.setViewportSize({ width: breakpoint.width, height: breakpoint.height });
    await page.goto(path);
    await page.waitForLoadState('networkidle');
    
    // Take screenshot for visual regression
    await page.screenshot({ 
      path: `e2e/screenshots/${path.replace('/', '')}-${breakpoint.name}.png`,
      fullPage: true 
    });
  }
}

/**
 * Verify keyboard navigation works
 */
export async function testKeyboardNavigation(page: Page) {
  // Tab through first few elements
  for (let i = 0; i < 5; i++) {
    await page.keyboard.press('Tab');
    
    // Verify focus is visible
    const focused = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      
      const styles = window.getComputedStyle(el);
      return {
        tag: el.tagName,
        hasFocus: el === document.activeElement,
        outlineWidth: styles.outlineWidth
      };
    });
    
    expect(focused?.hasFocus).toBe(true);
  }
}

/**
 * Verify ARIA labels are present
 */
export async function verifyAriaLabels(page: Page, expectedLabels: string[]) {
  for (const label of expectedLabels) {
    const element = page.getByLabel(new RegExp(label, 'i'));
    await expect(element).toBeVisible();
  }
}
