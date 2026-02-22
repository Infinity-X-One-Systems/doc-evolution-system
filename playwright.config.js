// @ts-check
const { defineConfig, devices } = require("@playwright/test");

/** @type {import('@playwright/test').Config} */
module.exports = defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    headless: true,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npx serve singularity/ui -l 3000 --no-clipboard",
    url: "http://localhost:3000",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
