import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  outputDir: "../reports/ch-m1-02/playwright-output",
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
