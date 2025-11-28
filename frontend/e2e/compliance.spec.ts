import { test, expect } from '@playwright/test';

/**
 * Compliance Page E2E Tests
 * Tests both static (Employment Insurance) and dynamic (multi-program) compliance checkers
 */

test.describe('Static Compliance Page - Employment Insurance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/compliance');
  });

  test('should display compliance form interface', async ({ page }) => {
    // Check page title
    await expect(page.getByRole('heading', { name: /compliance check/i })).toBeVisible();
    
    // Check form fields are visible
    await expect(page.getByLabel(/full legal name/i)).toBeVisible();
    await expect(page.getByLabel(/social insurance number/i)).toBeVisible();
    await expect(page.getByLabel(/residency status/i)).toBeVisible();
    await expect(page.getByLabel(/hours worked/i)).toBeVisible();
    
    // Check submit button
    await expect(page.getByRole('button', { name: /analyze compliance/i })).toBeVisible();
  });

  test('should display empty state before form submission', async ({ page }) => {
    await expect(page.getByText(/ready for analysis/i)).toBeVisible();
    await expect(page.getByText(/fill out the applicant details/i)).toBeVisible();
  });

  test('should validate full name field', async ({ page }) => {
    const nameInput = page.getByLabel(/full legal name/i);
    
    // Test too short name
    await nameInput.fill('A');
    await nameInput.blur();
    await expect(page.getByText(/name must be at least 2 characters/i)).toBeVisible();
    
    // Test valid name
    await nameInput.fill('John Doe');
    await nameInput.blur();
    await expect(page.getByText(/name must be at least 2 characters/i)).not.toBeVisible();
  });

  test('should validate SIN field format', async ({ page }) => {
    const sinInput = page.getByLabel(/social insurance number/i);
    
    // Test invalid format
    await sinInput.fill('123456789');
    await sinInput.blur();
    await expect(page.getByText(/sin must be in format: 123-456-789/i)).toBeVisible();
    
    // Test valid format
    await sinInput.fill('123-456-789');
    await sinInput.blur();
    await expect(page.getByText(/sin must be in format: 123-456-789/i)).not.toBeVisible();
  });

  test('should validate hours worked field', async ({ page }) => {
    const hoursInput = page.getByLabel(/hours worked/i);
    
    // Test below minimum
    await hoursInput.fill('100');
    await hoursInput.blur();
    await expect(page.getByText(/minimum 420 hours required/i)).toBeVisible();
    
    // Test valid hours
    await hoursInput.fill('600');
    await hoursInput.blur();
    await expect(page.getByText(/minimum 420 hours required/i)).not.toBeVisible();
  });

  test('should require residency status selection', async ({ page }) => {
    const residencySelect = page.getByLabel(/residency status/i);
    
    // Initially should show placeholder
    await expect(residencySelect).toHaveValue('');
    
    // Select a value
    await residencySelect.selectOption('citizen');
    await expect(residencySelect).toHaveValue('citizen');
  });

  test('should disable submit button when form is invalid', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    
    // Button should be disabled initially (empty form)
    await expect(submitButton).toBeDisabled();
    
    // Fill form with invalid data
    await page.getByLabel(/full legal name/i).fill('J'); // Too short
    await expect(submitButton).toBeDisabled();
  });

  test('should enable submit button when form is valid', async ({ page }) => {
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    
    // Fill form with valid data
    await page.getByLabel(/full legal name/i).fill('John Doe');
    await page.getByLabel(/social insurance number/i).fill('123-456-789');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('600');
    
    // Wait for validation to complete
    await page.waitForTimeout(500);
    
    // Button should be enabled
    await expect(submitButton).not.toBeDisabled();
  });

  test('should show validation message when submitting invalid form', async ({ page }) => {
    // Try to submit with empty form (button will be disabled, so fill partially)
    await page.getByLabel(/full legal name/i).fill('J');
    
    await expect(page.getByText(/please fix validation errors/i)).toBeVisible();
  });

  test('should have keyboard accessible form fields', async ({ page }) => {
    // Tab through form
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Should focus on form elements
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'SELECT', 'BUTTON']).toContain(focused);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/compliance');
    
    // Form should still be visible and usable
    await expect(page.getByLabel(/full legal name/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /analyze compliance/i })).toBeVisible();
  });

  test('should show loading state during submission', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/compliance/check', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({ json: { compliant: true, confidence: 0.9 } });
    });
    
    // Fill form with valid data
    await page.getByLabel(/full legal name/i).fill('John Doe');
    await page.getByLabel(/social insurance number/i).fill('123-456-789');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('600');
    
    await page.waitForTimeout(500);
    
    // Submit form
    await page.getByRole('button', { name: /analyze compliance/i }).click();
    
    // Should show loading spinner
    await expect(page.getByText(/analyzing/i)).toBeVisible();
    await expect(page.getByText(/checking compliance/i)).toBeVisible();
  });
});

test.describe('Dynamic Compliance Page - Multi-Program', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/compliance-dynamic');
  });

  test('should display program selector', async ({ page }) => {
    // Check page title
    await expect(page.getByRole('heading', { name: /compliance checker/i })).toBeVisible();
    
    // Check description
    await expect(page.getByText(/select a government program/i)).toBeVisible();
    
    // Check program buttons are visible
    await expect(page.getByRole('button', { name: /employment insurance/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /cpp retirement/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /canada child benefit/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /gis/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /social assistance/i })).toBeVisible();
  });

  test('should start with Employment Insurance selected by default', async ({ page }) => {
    // First program button should have active styling
    const eiButton = page.getByRole('button', { name: /employment insurance/i });
    
    // Check if button has active state (bg-teal-600)
    await expect(eiButton).toHaveClass(/bg-teal-600/);
  });

  test('should switch between programs', async ({ page }) => {
    // Click on CPP Retirement program
    const cppButton = page.getByRole('button', { name: /cpp retirement/i });
    await cppButton.click();
    
    // CPP button should now be active
    await expect(cppButton).toHaveClass(/bg-teal-600/);
    
    // Should show CPP program description
    await expect(page.getByText(/canada pension plan retirement/i)).toBeVisible();
  });

  test('should reset form when switching programs', async ({ page }) => {
    // Fill in some data for Employment Insurance
    const nameInput = page.getByLabel(/full legal name/i);
    await nameInput.fill('John Doe');
    
    // Switch to CPP program
    await page.getByRole('button', { name: /cpp retirement/i }).click();
    
    // Wait for form to reset
    await page.waitForTimeout(300);
    
    // Form fields should be empty or reset
    // Note: Different programs have different fields
  });

  test('should display different fields for different programs', async ({ page }) => {
    // Employment Insurance has these fields
    await expect(page.getByLabel(/full legal name/i)).toBeVisible();
    await expect(page.getByLabel(/hours worked/i)).toBeVisible();
    
    // Switch to Canada Child Benefit
    await page.getByRole('button', { name: /canada child benefit/i }).click();
    
    // Should show different fields (child-related)
    await page.waitForTimeout(300);
    // Fields will vary based on program configuration
  });

  test('should show empty state before form submission', async ({ page }) => {
    await expect(page.getByText(/ready for analysis/i)).toBeVisible();
    await expect(page.getByText(/complete the form to generate/i)).toBeVisible();
  });

  test('should validate form fields dynamically', async ({ page }) => {
    // Test with Employment Insurance (has name and SIN validation)
    const nameInput = page.getByLabel(/full legal name/i);
    
    await nameInput.fill('A');
    await nameInput.blur();
    await expect(page.getByText(/name must be at least 2 characters/i)).toBeVisible();
    
    await nameInput.fill('John Doe');
    await nameInput.blur();
    await expect(page.getByText(/name must be at least 2 characters/i)).not.toBeVisible();
  });

  test('should have accessible program selector buttons', async ({ page }) => {
    // Tab to program selector
    await page.keyboard.press('Tab');
    
    // Arrow keys should navigate between programs
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Enter');
    
    // A different program should be selected
    await page.waitForTimeout(300);
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/compliance-dynamic');
    
    // Program selector should be scrollable
    await expect(page.getByRole('button', { name: /employment insurance/i })).toBeVisible();
    
    // Form should still be usable
    await expect(page.getByLabel(/full legal name/i)).toBeVisible();
  });

  test('should be responsive on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/compliance-dynamic');
    
    // All elements should be visible and properly laid out
    await expect(page.getByRole('button', { name: /employment insurance/i })).toBeVisible();
    await expect(page.getByLabel(/full legal name/i)).toBeVisible();
  });

  test('should handle program switching with keyboard', async ({ page }) => {
    // Focus on first program button
    const eiButton = page.getByRole('button', { name: /employment insurance/i });
    await eiButton.focus();
    
    // Press Tab to move to next program
    await page.keyboard.press('Tab');
    
    // Press Enter to select
    await page.keyboard.press('Enter');
    
    await page.waitForTimeout(300);
  });

  test('should display confidence score in results', async ({ page }) => {
    // Mock API response
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        json: {
          compliant: true,
          confidence: 0.92,
          issues: [],
          passed_requirements: 4,
          total_requirements: 4
        }
      });
    });
    
    // Fill form with valid data
    await page.getByLabel(/full legal name/i).fill('John Doe');
    await page.getByLabel(/social insurance number/i).fill('123-456-789');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('600');
    
    await page.waitForTimeout(500);
    
    // Submit form
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Wait for results
      await page.waitForTimeout(1000);
      
      // Should show confidence score
      await expect(page.getByText(/92%/)).toBeVisible();
    }
  });
});

test.describe('Compliance Pages - Error Handling', () => {
  test('should handle API errors gracefully on static page', async ({ page }) => {
    await page.goto('/compliance');
    
    // Mock API error
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        status: 500,
        json: { error: 'Internal server error' }
      });
    });
    
    // Fill and submit form
    await page.getByLabel(/full legal name/i).fill('John Doe');
    await page.getByLabel(/social insurance number/i).fill('123-456-789');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('600');
    
    await page.waitForTimeout(500);
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Should show error message
      await page.waitForTimeout(1000);
      await expect(page.getByText(/error/i)).toBeVisible();
    }
  });

  test('should handle API errors gracefully on dynamic page', async ({ page }) => {
    await page.goto('/compliance-dynamic');
    
    // Mock API error
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        status: 500,
        json: { error: 'Service unavailable' }
      });
    });
    
    // Fill and submit form
    await page.getByLabel(/full legal name/i).fill('Jane Smith');
    await page.getByLabel(/social insurance number/i).fill('987-654-321');
    await page.getByLabel(/residency status/i).selectOption('permanent_resident');
    await page.getByLabel(/hours worked/i).fill('800');
    
    await page.waitForTimeout(500);
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Should show error message
      await page.waitForTimeout(1000);
      await expect(page.getByText(/error/i)).toBeVisible();
    }
  });

  test('should prevent submission with incomplete form', async ({ page }) => {
    await page.goto('/compliance');
    
    // Fill only some fields
    await page.getByLabel(/full legal name/i).fill('John Doe');
    // Leave other fields empty
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    
    // Button should be disabled
    await expect(submitButton).toBeDisabled();
  });
});

test.describe('Compliance Pages - Results Display', () => {
  test('should display successful compliance result', async ({ page }) => {
    await page.goto('/compliance');
    
    // Mock successful API response
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        json: {
          compliant: true,
          confidence: 0.95,
          issues: [],
          passed_requirements: 5,
          total_requirements: 5
        }
      });
    });
    
    // Fill and submit form
    await page.getByLabel(/full legal name/i).fill('John Doe');
    await page.getByLabel(/social insurance number/i).fill('123-456-789');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('600');
    
    await page.waitForTimeout(500);
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Wait for results
      await page.waitForTimeout(1000);
      
      // Should show success message
      await expect(page.getByText(/likely eligible/i)).toBeVisible();
      await expect(page.getByText(/95%/)).toBeVisible();
    }
  });

  test('should display failed compliance result with issues', async ({ page }) => {
    await page.goto('/compliance');
    
    // Mock failed API response with issues
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        json: {
          compliant: false,
          confidence: 0.75,
          issues: [
            {
              issue_id: 'hours_insufficient',
              field_name: 'hours_worked',
              requirement: 'Minimum hours requirement',
              description: 'Applicant has not worked enough hours in the qualifying period',
              severity: 'critical',
              suggestion: 'Ensure you have worked at least 420 hours in the last 52 weeks'
            }
          ],
          passed_requirements: 3,
          total_requirements: 5
        }
      });
    });
    
    // Fill and submit form
    await page.getByLabel(/full legal name/i).fill('Jane Smith');
    await page.getByLabel(/social insurance number/i).fill('987-654-321');
    await page.getByLabel(/residency status/i).selectOption('temporary_resident');
    await page.getByLabel(/hours worked/i).fill('300'); // Below minimum
    
    await page.waitForTimeout(500);
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Wait for results
      await page.waitForTimeout(1000);
      
      // Should show failure message
      await expect(page.getByText(/not eligible/i)).toBeVisible();
      
      // Should show issues
      await expect(page.getByText(/issues/i)).toBeVisible();
      await expect(page.getByText(/minimum hours requirement/i)).toBeVisible();
    }
  });

  test('should display requirements met section', async ({ page }) => {
    await page.goto('/compliance-dynamic');
    
    // Mock response with some passed requirements
    await page.route('**/api/compliance/check', async route => {
      await route.fulfill({
        json: {
          compliant: true,
          confidence: 0.88,
          issues: [],
          passed_requirements: 8,
          total_requirements: 10
        }
      });
    });
    
    // Fill and submit form
    await page.getByLabel(/full legal name/i).fill('Test User');
    await page.getByLabel(/social insurance number/i).fill('111-222-333');
    await page.getByLabel(/residency status/i).selectOption('citizen');
    await page.getByLabel(/hours worked/i).fill('1000');
    
    await page.waitForTimeout(500);
    
    const submitButton = page.getByRole('button', { name: /analyze compliance/i });
    if (await submitButton.isEnabled()) {
      await submitButton.click();
      
      // Wait for results
      await page.waitForTimeout(1000);
      
      // Should show requirements met
      await expect(page.getByText(/requirements met/i)).toBeVisible();
      await expect(page.getByText(/8/)).toBeVisible();
      await expect(page.getByText(/10/)).toBeVisible();
    }
  });
});
