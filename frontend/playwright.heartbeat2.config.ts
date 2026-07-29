import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "heartbeat2-browser.spec.ts",
  timeout: 60_000,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  workers: 1,
  reporter: [["json", { outputFile: process.env.H2_PLAYWRIGHT_REPORT ?? "../reports/heartbeat2/playwright.json" }]],
  use: { baseURL: "http://127.0.0.1:3122", serviceWorkers: "block", trace: "on", screenshot: "off", video: "off" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
