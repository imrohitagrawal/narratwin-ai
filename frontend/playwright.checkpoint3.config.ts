import { defineConfig, devices } from "@playwright/test";

const backendPort = Number(process.env.NARRATWIN_CP8_BACKEND_PORT ?? "8120");
const frontendPort = Number(process.env.NARRATWIN_CP8_FRONTEND_PORT ?? "3120");
const backendBaseURL = `http://127.0.0.1:${backendPort}`;
const frontendBaseURL = `http://127.0.0.1:${frontendPort}`;

process.env.NARRATWIN_CP3_PRODUCT_FAITHFUL = "1";
process.env.NARRATWIN_REAL_STACK = "1";

const localMockEnvironment = {
  ANTHROPIC_API_KEY: "",
  AVATAR_PROVIDER: "mock",
  DID_API_KEY: "",
  ELEVENLABS_API_KEY: "",
  EMBEDDING_PROVIDER: "mock",
  EVALUATION_PROVIDER: "mock",
  GEMINI_API_KEY: "",
  GOOGLE_API_KEY: "",
  HEYGEN_API_KEY: "",
  LANGFUSE_HOST: "",
  LANGFUSE_PUBLIC_KEY: "",
  LANGFUSE_SECRET_KEY: "",
  LLM_PROVIDER: "mock",
  NARRATWIN_CP3_PRODUCT_FAITHFUL: "1",
  NARRATWIN_REAL_STACK: "1",
  NARRATWIN_STAGE4_STATE_FILE: "",
  NARRATWIN_STAGE6_STATE_FILE: "",
  NARRATWIN_STAGE7_STATE_FILE: "",
  NARRATWIN_STATE_DIR: "",
  OPENAI_API_KEY: "",
  OPENROUTER_API_KEY: "",
  STORAGE_PROVIDER: "local",
  STT_PROVIDER: "mock",
  SUBTITLE_PROVIDER: "mock",
  TAVUS_API_KEY: "",
  TRANSLATION_PROVIDER: "mock",
  TTS_PROVIDER: "mock",
};

export default defineConfig({
  testDir: "./tests",
  testMatch: /checkpoint3-real-browser\.spec\.ts/,
  timeout: 90_000,
  expect: {
    timeout: 20_000,
  },
  outputDir: "../reports/checkpoint3-real-browser/playwright-output",
  use: {
    baseURL: frontendBaseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `uv run uvicorn backend.app.main:app --host 127.0.0.1 --port ${backendPort}`,
      cwd: "..",
      url: `${backendBaseURL}/api/v1/healthz`,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ...localMockEnvironment,
        APP_ENV: "test",
      },
    },
    {
      command: `npm run dev -- -H 127.0.0.1 -p ${frontendPort}`,
      url: frontendBaseURL,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ...localMockEnvironment,
        NARRATWIN_API_PROXY_TARGET: backendBaseURL,
      },
    },
  ],
});
