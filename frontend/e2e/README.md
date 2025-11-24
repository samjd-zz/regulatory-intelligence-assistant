# E2E Testing with Playwright

This directory contains end-to-end tests for the Regulatory Intelligence Assistant frontend.

## Quick Start

```bash
# Run all tests (headless)
npm test

# Run with UI (interactive mode)
npm run test:ui

# Run with browser visible
npm run test:headed

# Debug mode (step through tests)
npm run test:debug

# View test report
npm run test:report
```

## Test Files

- **dashboard.spec.ts** - Dashboard page tests (navigation, cards, responsive design)
- **search.spec.ts** - Search functionality tests (input, filters, results)
- **chat.spec.ts** - Q&A chat interface tests (messages, interactions)
- **helpers/test-helpers.ts** - Reusable test utilities

## Test Structure

Each test file follows this pattern:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/path');
  });

  test('should do something', async ({ page }) => {
    // Test code here
  });
});
```

## Test Helpers

Common utilities in `helpers/test-helpers.ts`:

```typescript
import {
  navigateAndWait,           // Navigate with wait for load
  fillFieldByLabel,          // Fill form by label text
  checkAccessibility,        // Verify a11y attributes
  waitForLoadingToComplete,  // Wait for spinners to disappear
  verifyConfidenceBadge,     // Check confidence badge display
  testKeyboardNavigation,    // Test tab navigation
  mockApiResponse,           // Mock API responses
} from './helpers/test-helpers';
```

## Browser Configuration

Tests run on multiple browsers/devices:
- Desktop: Chromium, Firefox, WebKit
- Mobile: Pixel 5, iPhone 12
- Tablet: iPad Pro

Run specific browser:
```bash
npx playwright test --project=chromium
npx playwright test --project="Mobile Chrome"
```

## Writing New Tests

1. Create a new `.spec.ts` file in the `e2e/` directory
2. Import Playwright test utilities
3. Group related tests with `test.describe()`
4. Use `test.beforeEach()` for common setup
5. Write descriptive test names with "should"
6. Use semantic selectors (getByRole, getByLabel, getByText)
7. Always wait for assertions to complete

Example:

```typescript
import { test, expect } from '@playwright/test';

test.describe('New Feature', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/new-feature');
  });

  test('should display heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /feature name/i }))
      .toBeVisible();
  });

  test('should handle user interaction', async ({ page }) => {
    const button = page.getByRole('button', { name: /submit/i });
    await button.click();
    await expect(page.getByText(/success/i)).toBeVisible();
  });
});
```

## Best Practices

### 1. Use Semantic Selectors

✅ **Good** - Accessible and resilient:
```typescript
page.getByRole('button', { name: /submit/i })
page.getByLabel(/email/i)
page.getByText(/welcome/i)
page.getByPlaceholder(/search/i)
```

❌ **Avoid** - Brittle and implementation-dependent:
```typescript
page.locator('.submit-btn')
page.locator('#email-input')
page.locator('div > span.text')
```

### 2. Always Wait for State

```typescript
// Wait for navigation
await page.waitForURL('/dashboard');

// Wait for element visibility
await expect(element).toBeVisible();

// Wait for network to be idle
await page.waitForLoadState('networkidle');
```

### 3. Test User Behavior, Not Implementation

✅ **Good** - Tests what users experience:
```typescript
test('user can search for regulations', async ({ page }) => {
  await page.goto('/search');
  await page.getByPlaceholder(/search/i).fill('employment');
  await page.getByRole('button', { name: /search/i }).click();
  await expect(page.getByText(/results/i)).toBeVisible();
});
```

❌ **Avoid** - Tests internal implementation:
```typescript
test('search store updates', async ({ page }) => {
  // Don't test internal state management
});
```

### 4. Keep Tests Independent

Each test should:
- Start from a clean state
- Not depend on other tests
- Clean up after itself (if needed)

```typescript
test.describe('Feature', () => {
  test.beforeEach(async ({ page }) => {
    // Reset state for each test
    await page.goto('/');
  });

  test('test 1', async ({ page }) => {
    // Independent test
  });

  test('test 2', async ({ page }) => {
    // Independent test
  });
});
```

### 5. Use Test Helpers for Common Operations

```typescript
import { navigateAndWait, checkAccessibility } from './helpers/test-helpers';

test('page is accessible', async ({ page }) => {
  await navigateAndWait(page, '/search');
  await checkAccessibility(page);
});
```

## Debugging

### Interactive UI Mode

Best for exploring tests visually:
```bash
npm run test:ui
```

Features:
- Watch mode with file watcher
- Time travel through test execution
- Pick and run individual tests
- See test results in real-time

### Debug Mode

Step through tests with DevTools:
```bash
npm run test:debug
```

Or debug a specific test:
```bash
npx playwright test dashboard.spec.ts --debug
```

### Screenshots and Videos

On test failure, Playwright automatically captures:
- Screenshot at failure point
- Video recording of the test
- Trace file for time-travel debugging

View in the HTML report:
```bash
npm run test:report
```

### Console Logging

Add debugging output:
```typescript
test('debug example', async ({ page }) => {
  console.log('Current URL:', page.url());
  
  const text = await page.getByRole('heading').textContent();
  console.log('Heading text:', text);
});
```

## CI/CD Integration

The configuration is optimized for CI:
- Automatic retries on failure (2x)
- Single worker in CI (parallel locally)
- HTML report artifacts
- Screenshot/video capture on failure

Example GitHub Actions:

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: cd frontend && npm ci
        
      - name: Install Playwright browsers
        run: cd frontend && npx playwright install --with-deps
        
      - name: Run E2E tests
        run: cd frontend && npm test
        
      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Accessibility Testing

All tests should verify basic accessibility:

```typescript
import { checkAccessibility } from './helpers/test-helpers';

test('page is accessible', async ({ page }) => {
  await page.goto('/');
  await checkAccessibility(page);
});
```

This checks for:
- Proper page title
- Main landmark element
- Semantic HTML structure

For comprehensive a11y testing, consider:
- [@axe-core/playwright](https://www.npmjs.com/package/@axe-core/playwright)
- Manual keyboard navigation testing
- Screen reader testing

## Performance Testing

Monitor page load times:

```typescript
test('page loads quickly', async ({ page }) => {
  const start = Date.now();
  await page.goto('/');
  const loadTime = Date.now() - start;
  
  expect(loadTime).toBeLessThan(3000); // 3 seconds
});
```

Use Lighthouse for detailed metrics:
```bash
npx playwright test --project=chromium --trace on
```

## Common Issues

### Test Timeout

If tests timeout, increase the timeout:

```typescript
test('slow operation', async ({ page }) => {
  test.setTimeout(60000); // 60 seconds
  await page.goto('/slow-page');
});
```

### Flaky Tests

Flaky tests often indicate:
- Missing waits
- Race conditions
- Non-deterministic behavior

Fix with explicit waits:

```typescript
// Wait for element
await expect(element).toBeVisible();

// Wait for network
await page.waitForLoadState('networkidle');

// Wait for specific response
await page.waitForResponse(response => 
  response.url().includes('/api/search')
);
```

### Element Not Found

Ensure element exists and is visible:

```typescript
// Check if element exists
await page.locator('button').count();

// Wait for element to be visible
await expect(page.getByRole('button')).toBeVisible();

// Use more specific selector
await page.getByRole('button', { name: /exact name/i });
```

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Selectors Guide](https://playwright.dev/docs/selectors)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [API Reference](https://playwright.dev/docs/api/class-playwright)

## Coverage

Current test coverage:

- ✅ Dashboard page
  - Navigation
  - Action cards
  - Responsive design
  - Keyboard navigation

- ✅ Search page
  - Search input
  - Filter controls
  - Result display
  - Mobile layout

- ✅ Chat page
  - Message input
  - Send functionality
  - Message display
  - Button states

- ⏳ Compliance page (pending)
- ⏳ API integration tests (pending)
- ⏳ Visual regression tests (pending)

## Contributing

When adding new tests:

1. Follow the existing file structure
2. Use descriptive test names
3. Add comments for complex logic
4. Keep tests independent
5. Use test helpers when appropriate
6. Verify accessibility
7. Test on multiple browsers (run full suite)
8. Update this README if adding new patterns

## Questions?

See the main [TESTING.md](../TESTING.md) for comprehensive testing documentation.
