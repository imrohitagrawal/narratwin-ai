import { expect, test, type Page } from "@playwright/test";
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";

test.skip(process.env.NARRATWIN_REAL_STACK !== "1", "Requires the local Compose stack.");

test("Issue #213 Checkpoint B real browser path reaches frontend, backend, and Compose services without API interception", async ({
  page,
}, testInfo) => {
  const startedAt = performance.now();
  const apiCalls: string[] = [];
  const failedRequests: string[] = [];
  const requestOrigins = new Set<string>();

  page.on("request", (request) => {
    const url = new URL(request.url());
    requestOrigins.add(url.origin);
  });
  page.on("requestfinished", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/v1/")) {
      apiCalls.push(`${request.method()} ${url.pathname}`);
    }
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.method()} ${request.url()} ${request.failure()?.errorText ?? "unknown"}`);
  });

  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  const appOrigin = new URL(response?.url() ?? page.url()).origin;

  await expect(page.getByRole("heading", { name: "Avatar demo export" })).toBeVisible();
  await page.getByLabel("Knowledge document").fill(`# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts with source chunk citations.

It supports recruiter and engineering audiences with audience-aware explanations.

The Stage 4 slice uses a mock local LLM and mock local embeddings for deterministic tests.

Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.`);
  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(page.getByLabel("Trace metadata")).toContainText("mock", { timeout: 20_000 });
  await expect(page.getByLabel("Trace metadata")).toContainText("es");
  await expect(page.getByLabel("Avatar metadata")).toContainText("CONFIRMED");
  await expect(page.getByLabel("Render job lifecycle")).toContainText("MOCK_LOCAL");
  await expect(page.getByLabel("Avatar demo preview")).toContainText("local-html");
  await expect(page.getByRole("link", { name: "Download script" })).toHaveAttribute("download", /-es-script\.md$/);
  await expect(page.getByRole("link", { name: "Download subtitles" })).toHaveAttribute("download", /-es\.srt$/);
  await expect(page.getByRole("link", { name: "Download voice manifest" })).toHaveAttribute(
    "download",
    /voice-manifest-es\.json$/,
  );
  await expect(page.getByRole("link", { name: "Download avatar demo" })).toHaveAttribute(
    "download",
    /-avatar-demo\.html$/,
  );
  await expect(page.getByRole("link", { name: "Download video placeholder" })).toHaveAttribute(
    "download",
    /-video-export-placeholder\.json$/,
  );
  await expect(page.getByText("AI-generated avatar demo export using a synthetic local presenter.")).toBeVisible();
  await expect(page.getByText("0 unsupported claims")).toBeVisible();
  const artifactMetadata = await Promise.all(
    [
      "Download script",
      "Download subtitles",
      "Download voice manifest",
      "Download avatar demo",
      "Download render manifest",
      "Download video placeholder",
    ].map((label) => readArtifactMetadata(page, label)),
  );

  await page.screenshot({
    path: testInfo.outputPath("issue-213-checkpoint-b-avatar-export.png"),
    fullPage: true,
  });

  const durationMs = Math.round(performance.now() - startedAt);
  await writeFile(
    testInfo.outputPath("issue-213-checkpoint-b-evidence.json"),
    JSON.stringify(
      {
        commit: process.env.NARRATWIN_EVIDENCE_COMMIT ?? "not-provided",
        baseURL: process.env.NARRATWIN_REAL_STACK_BASE_URL ?? "not-provided",
        caseCount: 1,
        durationMs,
        apiCallCount: apiCalls.length,
        artifactMetadata,
        requestOrigins: Array.from(requestOrigins).sort(),
        noApiInterception: true,
        providers: {
          llm: "mock",
          embedding: "mock",
          evaluation: "mock",
          translation: "mock",
          avatar: "mock",
          tts: "mock",
          stt: "mock",
          subtitle: "mock",
          videoRenderer: "local",
        },
        limitations: [
          "controlled local/mock evidence only",
          "no Product Mode 2",
          "no real audio",
          "no real video export",
          "no external/paid provider enablement",
          "no hosted/public launch",
          "production/public release remains No-Go",
        ],
      },
      null,
      2,
    ),
    "utf8",
  );

  expect(failedRequests).toEqual([]);
  expect(Array.from(requestOrigins).sort()).toEqual([appOrigin]);
  expect(durationMs).toBeLessThan(15_000);
  expect(apiCalls).toHaveLength(8);
  expect(apiCalls[0]).toBe("POST /api/v1/projects");
  expect(apiCalls[1]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/knowledge-documents$/);
  expect(apiCalls[2]).toMatch(/^PATCH \/api\/v1\/projects\/proj_\d+\/knowledge-documents\/doc_\d+\/approval$/);
  expect(apiCalls[3]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/ingestion-runs$/);
  expect(apiCalls[4]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/walkthrough-runs$/);
  expect(apiCalls[5]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/multilingual-runs$/);
  expect(apiCalls[6]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-consents$/);
  expect(apiCalls[7]).toMatch(/^POST \/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-renders$/);
});

async function readArtifactMetadata(page: Page, label: string) {
  const attributes = await page.getByRole("link", { name: label }).evaluate((link) => ({
    fileName: link.getAttribute("download") ?? "",
    href: link.getAttribute("href") ?? "",
  }));
  const dataUrlMatch = /^data:([^;]+);base64,(.+)$/.exec(attributes.href);
  expect(dataUrlMatch).not.toBeNull();
  const [, mimeType, contentBase64] = dataUrlMatch ?? ["", "", ""];
  const decoded = Buffer.from(contentBase64, "base64");
  return {
    label,
    fileName: attributes.fileName,
    mimeType,
    byteLength: decoded.byteLength,
    checksum: `sha256:${createHash("sha256").update(decoded).digest("hex")}`,
  };
}
