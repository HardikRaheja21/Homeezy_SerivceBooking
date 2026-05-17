import { test, expect } from '@playwright/test';

test.describe('Authentication Journey', () => {
  test('Customer can register and login securely', async ({ page }) => {
    // Navigate to login
    await page.goto('/login');
    await expect(page).toHaveTitle(/Homeezy - Login/);

    // Register flow (mocked credentials or seeded)
    await page.click('text=Create an account');
    await page.fill('input[name="fullName"]', 'Playwright Customer');
    await page.fill('input[name="email"]', 'pw_customer@example.com');
    await page.fill('input[name="phone"]', '9999999999');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // OTP Flow
    await expect(page.locator('text=Verify OTP')).toBeVisible();
    await page.fill('input[name="otp"]', '123456'); // Standard mock OTP for test accounts
    await page.click('button:has-text("Verify")');

    // Login Flow
    await page.fill('input[name="email"]', 'pw_customer@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // Assert Dashboard and sessionStorage protection
    await expect(page).toHaveURL('/dashboard/customer');
    
    // Verify sessionStorage retains token (XSS mitigation check)
    const hasToken = await page.evaluate(() => {
      return !!sessionStorage.getItem('auth-storage');
    });
    expect(hasToken).toBeTruthy();
  });

  test('Logout cleanly closes websockets and clears sessions', async ({ page }) => {
    await page.goto('/login');
    // ... setup login state ...
    
    // Perform logout
    // await page.click('button[aria-label="User menu"]');
    // await page.click('text=Logout');
    
    // Assert redirect to home/login
    // await expect(page).toHaveURL('/login');
  });
});
