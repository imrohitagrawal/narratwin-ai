import { expect, test } from "@playwright/test";

test.skip(process.env.NARRATWIN_REAL_STACK !== "1", "Requires the local Compose stack.");

test("CH-M1-02 real browser path reaches frontend, backend, and Compose services without API interception", async ({
  page,
}, testInfo) => {
  const apiCalls: string[] = [];
  const failedRequests: string[] = [];

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

  await expect(page.getByRole("heading", { name: "Avatar demo export" })).toBeVisible();
  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(page.getByLabel("Trace metadata")).toContainText("mock", { timeout: 20_000 });
  await expect(page.getByLabel("Trace metadata")).toContainText("es");
  await expect(page.getByLabel("Avatar metadata")).toContainText("CONFIRMED");
  await expect(page.getByLabel("Render job lifecycle")).toContainText("MOCK_LOCAL");
  await expect(page.getByLabel("Avatar demo preview")).toContainText("local-html");
  await expect(page.getByRole("link", { name: "Download script" })).toHaveAttribute("download", /-es-script\.md$/);
  await expect(page.getByRole("link", { name: "Download subtitles" })).toHaveAttribute("download", /-es\.srt$/);
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

  await page.screenshot({
    path: testInfo.outputPath("ch-m1-02-avatar-export.png"),
    fullPage: true,
  });

  expect(failedRequests).toEqual([]);
  expect(apiCalls).toHaveLength(8);
  expect(apiCalls[0]).toBe("POST /api/v1/projects");
  expect(apiCalls[1]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/knowledge-documents$/);
  expect(apiCalls[2]).toMatch(/^PATCH \/api\/v1\/projects\/project_\d+\/knowledge-documents\/doc_\d+\/approval$/);
  expect(apiCalls[3]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/ingestion-runs$/);
  expect(apiCalls[4]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/walkthrough-runs$/);
  expect(apiCalls[5]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/walkthrough-runs\/run_\d+\/multilingual-runs$/);
  expect(apiCalls[6]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/walkthrough-runs\/run_\d+\/avatar-consents$/);
  expect(apiCalls[7]).toMatch(/^POST \/api\/v1\/projects\/project_\d+\/walkthrough-runs\/run_\d+\/avatar-renders$/);
});
