import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: /heartbeat1-browser\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 85_000,
  reporter: [["line"]],
  outputDir: `${process.env.NARRATWIN_HEARTBEAT1_CANDIDATE_DIR ?? "../reports/heartbeat1/candidate"}/playwright-${process.env.NARRATWIN_HEARTBEAT1_PHASE ?? "unset"}`,
  use: {
    baseURL: "http://127.0.0.1:3122",
    serviceWorkers: "block",
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
