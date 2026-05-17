import { test, expect } from '@playwright/test';

test.describe('AI Assistant Journey', () => {
  test('AI maintains conversational context', async ({ page }) => {
    await page.goto('/dashboard/customer');
    
    // Open chat
    await page.click('button[aria-label="Open AI Assistant"]');
    
    // Message 1
    const chatInput = page.locator('input[placeholder="Ask something..."]');
    await chatInput.fill('My kitchen sink is leaking.');
    await page.keyboard.press('Enter');
    
    // Verify SSE streaming starts
    await expect(page.locator('.ai-message')).toContainText(/plumber|plumbing/i, { timeout: 15000 });

    // Message 2 (Context continuity)
    await chatInput.fill('How urgent is it?');
    await page.keyboard.press('Enter');

    // The AI should respond in the context of a leak, not generally
    await expect(page.locator('.ai-message').last()).toContainText(/leak|water damage/i, { timeout: 15000 });
  });

  test('AI Rate Limiting (Redis Token Bucket)', async ({ page }) => {
    // Attempt rapid fire requests to trigger 429
    // ... logic to simulate 6+ requests ...
    // Verify rate limit UI appears
  });
});
