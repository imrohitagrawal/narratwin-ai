import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: /real-stack\.spec\.ts/,
  timeout: 60_000,
  outputDir: "../reports/issue-213-checkpoint-b/playwright-output",
  use: {
    baseURL: process.env.NARRATWIN_REAL_STACK_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "on",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
