// @ts-check
const { test, expect } = require("@playwright/test");

test.describe("Singularity Prime Dashboard", () => {
  test("loads the dashboard page", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Singularity Prime/);
  });

  test("header displays org name", async ({ page }) => {
    await page.goto("/");
    const orgBadge = page.locator("#sp-org");
    await expect(orgBadge).toBeVisible();
    await expect(orgBadge).toHaveText("Infinity-X-One-Systems");
  });

  test("navigation tabs are present", async ({ page }) => {
    await page.goto("/");
    const tabs = [
      "Overview",
      "Roadmap",
      "Validation Matrix",
      "Checklist",
      "Tech Registry",
      "Memory Ledger",
      "State Transitions",
      "Admin Controls",
    ];
    for (const tab of tabs) {
      await expect(page.getByRole("button", { name: tab })).toBeVisible();
    }
  });

  test("overview tab is active by default", async ({ page }) => {
    await page.goto("/");
    const overviewSection = page.locator("#tab-overview");
    await expect(overviewSection).toBeVisible();
  });

  test("tab navigation switches panels", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Roadmap" }).click();
    await expect(page.locator("#tab-roadmap")).toBeVisible();
    await expect(page.locator("#tab-overview")).not.toBeVisible();
  });

  test("admin controls: add milestone form is present", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Admin Controls" }).click();
    await expect(page.locator("#form-add-milestone")).toBeVisible();
    await expect(page.locator("#ms-title")).toBeVisible();
  });

  test("admin controls: adding a milestone appends to roadmap view", async ({ page }) => {
    await page.goto("/");
    // Switch to admin tab
    await page.getByRole("button", { name: "Admin Controls" }).click();
    // Fill the form
    await page.fill("#ms-title", "Test Milestone");
    await page.fill("#ms-date", "2026-Q4");
    await page.selectOption("#ms-status", "planned");
    await page.click("#form-add-milestone button[type=submit]");
    // Switch to roadmap tab to verify milestone was added
    await page.getByRole("button", { name: "Roadmap" }).click();
    await expect(page.locator(".sp-milestone__title").filter({ hasText: "Test Milestone" })).toBeVisible();
  });

  test("footer timestamp is rendered", async ({ page }) => {
    await page.goto("/");
    const footer = page.locator("#footer-ts");
    await expect(footer).not.toBeEmpty();
  });
});
