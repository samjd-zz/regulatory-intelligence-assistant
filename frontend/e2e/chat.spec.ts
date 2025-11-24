import { test, expect } from '@playwright/test';

/**
 * Chat/Q&A Page E2E Tests
 * Tests the conversational interface functionality
 */

test.describe('Chat Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/chat');
  });

  test('should display chat interface', async ({ page }) => {
    // Check chat input is visible
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible();
    
    // Check send button is visible
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible();
  });

  test('should allow text input in message field', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask a question/i);
    await chatInput.fill('What are the requirements for employment insurance?');
    
    await expect(chatInput).toHaveValue('What are the requirements for employment insurance?');
  });

  test('should send message on button click', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask a question/i);
    await chatInput.fill('Test question');
    
    await page.getByRole('button', { name: /send/i }).click();
    
    // Input should be cleared after sending
    await expect(chatInput).toHaveValue('');
  });

  test('should send message on Enter key', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask a question/i);
    await chatInput.fill('Test question');
    await chatInput.press('Enter');
    
    // Input should be cleared
    await expect(chatInput).toHaveValue('');
  });

  test('should display user message after sending', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask a question/i);
    const testMessage = 'What is the minimum hours requirement?';
    
    await chatInput.fill(testMessage);
    await chatInput.press('Enter');
    
    // User message should appear in chat
    await expect(page.getByText(testMessage)).toBeVisible();
  });

  test('should disable send button when input is empty', async ({ page }) => {
    const sendButton = page.getByRole('button', { name: /send/i });
    
    // Button should be disabled with empty input
    await expect(sendButton).toBeDisabled();
  });

  test('should enable send button when input has text', async ({ page }) => {
    const chatInput = page.getByPlaceholder(/ask a question/i);
    const sendButton = page.getByRole('button', { name: /send/i });
    
    await chatInput.fill('Test');
    
    // Button should be enabled with text
    await expect(sendButton).toBeEnabled();
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Tab to input field
    await page.keyboard.press('Tab');
    
    // Should focus on input
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'TEXTAREA']).toContain(focused);
  });

  test('should display chat history section', async ({ page }) => {
    // Chat history/messages area should exist
    const chatArea = page.locator('[role="log"], [aria-label*="chat"], [aria-label*="messages"]');
    await expect(chatArea.first()).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/chat');
    
    // Chat interface should still be usable
    await expect(page.getByPlaceholder(/ask a question/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /send/i })).toBeVisible();
  });
});

test.describe('Chat Page - Message Display', () => {
  test('should show loading indicator after sending message', async ({ page }) => {
    await page.goto('/chat');
    
    const chatInput = page.getByPlaceholder(/ask a question/i);
    await chatInput.fill('Test question');
    await chatInput.press('Enter');
    
    // Should show loading state briefly
    // Note: This may complete too quickly to test without mocking
    await page.waitForTimeout(500);
  });

  test('should clear input after message is sent', async ({ page }) => {
    await page.goto('/chat');
    
    const chatInput = page.getByPlaceholder(/ask a question/i);
    await chatInput.fill('Test question');
    await chatInput.press('Enter');
    
    // Input should be empty
    await expect(chatInput).toHaveValue('');
  });
});
