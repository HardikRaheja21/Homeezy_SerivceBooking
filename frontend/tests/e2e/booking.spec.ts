import { test, expect } from '@playwright/test';

test.describe('Booking Lifecycle Journey', () => {
  test('Customer creates booking, Worker accepts, status updates', async ({ page, browser }) => {
    // Note: In real CI, these use isolated browser contexts and seeded DB states
    const customerContext = await browser.newContext();
    const workerContext = await browser.newContext();
    
    const customerPage = await customerContext.newPage();
    const workerPage = await workerContext.newPage();

    // 1. Customer creates booking
    await customerPage.goto('/services/plumbing');
    await customerPage.click('button:has-text("Book Now")');
    // fill booking details...
    await customerPage.fill('textarea[name="description"]', 'Leaky kitchen sink');
    await customerPage.click('button:has-text("Confirm Booking")');

    await expect(customerPage.locator('text=Booking Requested')).toBeVisible();

    // 2. Worker receives realtime update (WebSocket verification)
    await workerPage.goto('/dashboard/worker');
    await expect(workerPage.locator('text=New Booking Request')).toBeVisible({ timeout: 10000 });
    
    // 3. Worker accepts
    await workerPage.click('button:has-text("Accept Job")');
    await expect(workerPage.locator('text=Job Accepted')).toBeVisible();

    // 4. Customer sees live status update
    await expect(customerPage.locator('text=Worker Assigned')).toBeVisible({ timeout: 10000 });

    // 5. Worker completes
    await workerPage.click('button:has-text("Mark Completed")');

    // 6. Customer Review Prompt appears
    await expect(customerPage.locator('text=Leave a Review')).toBeVisible({ timeout: 10000 });
  });
});
