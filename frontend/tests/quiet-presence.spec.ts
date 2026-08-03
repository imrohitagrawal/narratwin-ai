import { expect, test } from "@playwright/test";

const json = (value: unknown) => ({
  status: 200,
  contentType: "application/json",
  body: JSON.stringify(value),
});

async function mockQuietPresencePipeline(page: Parameters<typeof test>[0]["page"]) {
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (path === "/api/v1/projects") {
      return route.fulfill(json({ projectId: "project_001" }));
    }
    if (path.endsWith("/knowledge-documents")) {
      return route.fulfill(json({ documentId: "document_001" }));
    }
    if (path.endsWith("/approval")) {
      return route.fulfill(json({ documentId: "document_001", approvalStatus: "APPROVED" }));
    }
    if (path.endsWith("/ingestion-runs")) {
      return route.fulfill(json({ ingestionRunId: "ingestion_001", status: "COMPLETED" }));
    }
    if (path.endsWith("/walkthrough-runs")) {
      return route.fulfill(json({
        runId: "run_001",
        status: "COMPLETED",
        acceptedScriptText: "The security review is still in progress. [1]",
        contextRefs: [{
          contextRefId: "context_001",
          chunkId: "chunk_001",
          documentId: "document_001",
          sourceFilename: "northwind-release.md",
          evidenceSnapshot: { redactedExcerpt: "Security review must pass before deployment." },
        }],
        evaluation: {
          evaluationId: "evaluation_001",
          evaluationStatus: "PASSED",
          unsupportedClaimCount: 0,
          claimSupports: [{ contextRefId: "context_001", citationIndex: 1 }],
        },
        trace: { traceId: "trace_001" },
      }));
    }
    if (path.endsWith("/multilingual-runs")) {
      return route.fulfill(json({
        multilingualRunId: "multilingual_001",
        sourceRunId: "run_001",
        targetLanguage: "es",
        translatedScriptText: "La revisión de seguridad sigue en curso. [1]",
        artifacts: {
          translatedScript: { checksum: "sha256:script" },
          subtitles: { checksum: "sha256:subtitles" },
          voiceManifest: { checksum: "sha256:voice" },
        },
        translationProvider: { provider: "mock", providerMode: "LOCAL" },
        voice: { provider: "mock", providerMode: "LOCAL" },
        trace: {
          sourceContextRefIds: ["context_001"],
          sourceCitationIndexes: [1],
          sourceEvaluationId: "evaluation_001",
          sourceEvaluationChecksum: "sha256:evaluation",
        },
      }));
    }
    if (path.endsWith("/avatar-consents")) {
      return route.fulfill(json({
        consentRecordId: "consent_001",
        consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
        consentStatementText: "Synthetic presenter approved for this local demo.",
      }));
    }
    if (path.endsWith("/avatar-renders")) {
      return route.fulfill(json({
        avatarRenderId: "render_001",
        status: "COMPLETED",
        renderJobStatus: "COMPLETED",
        sourceScriptText: "The security review is still in progress. [1]",
        avatarProvider: { provider: "mock", providerMode: "LOCAL" },
        providerConfig: { providerMode: "LOCAL", allowNetworkEgress: false, supportsRealVideo: false },
        disclosure: {
          consentStatus: "CONFIRMED",
          clonedIdentity: false,
          message: "Synthetic local presenter. No cloned identity.",
        },
      }));
    }
    return route.abort();
  });
}

test.describe("Quiet Presence mocked product UI", () => {
  test("keeps host context visible and exposes local grounded evidence", async ({ page }) => {
    await mockQuietPresencePipeline(page);
    await page.goto("/demo");

    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "NarraTwin project guide" })).toBeVisible();
    await page.getByRole("button", { name: "Run grounded demo" }).click();
    await expect(page.getByRole("heading", { name: "Why is deployment blocked?" })).toBeVisible();
    await expect(page.getByText("The security review is still in progress. [1]"),).toBeVisible();
    await page.getByRole("button", { name: /Verified sources/ }).click();
    await expect(page.getByText("Security review must pass before deployment.")).toBeVisible();
    await expect(page.getByText("Passed evaluation · 0 unsupported claims")).toBeVisible();
    await expect(page.getByText("No network egress")).toBeVisible();
  });

  test("supports dark theme and a mobile bottom-sheet layout without overflow", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/demo");
    await page.getByRole("button", { name: "Switch to dark theme" }).click();

    await expect(page.locator("main")).toHaveAttribute("data-theme", "dark");
    await expect(page.getByRole("complementary", { name: "NarraTwin project guide" })).toBeVisible();
    const overflows = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(overflows).toBe(false);
  });

  test("shows a bounded error and no fabricated evidence when the API fails", async ({ page }) => {
    await page.route("**/api/v1/projects", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ message: "token=secret /private/customer.md" }),
      }),
    );
    await page.goto("/demo");
    await page.getByRole("button", { name: "Run grounded demo" }).click();

    await expect(page.getByRole("alert")).toContainText("could not complete safely");
    await expect(page.getByText("token=secret")).toHaveCount(0);
    await expect(page.getByText("/private/customer.md")).toHaveCount(0);
    await expect(page.getByText("Passed evaluation · 0 unsupported claims")).toHaveCount(0);
  });
});
