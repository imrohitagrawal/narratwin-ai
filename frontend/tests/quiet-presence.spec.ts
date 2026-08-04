import { expect, test, type Page } from "@playwright/test";

const json = (value: unknown) => ({
  status: 200,
  contentType: "application/json",
  body: JSON.stringify(value),
});

async function mockQuietPresencePipeline(page: Page) {
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
          claimSupports: [{
            claimSupportId: "support_001",
            contextRefId: "context_001",
            chunkId: "chunk_001",
            documentId: "document_001",
            citationIndex: 1,
          }],
        },
        trace: { traceId: "trace_001" },
      }));
    }
    if (path.endsWith("/multilingual-runs")) {
      return route.fulfill(json({
        multilingualRunId: "multilingual_001",
        sourceRunId: "run_001",
        targetLanguage: "en",
        status: "COMPLETED",
        sourceScriptText: "The security review is still in progress. [1]",
        translatedScriptText: "The security review is still in progress. [1]",
        artifacts: {
          translatedScript: { checksum: "sha256:script" },
          subtitles: { checksum: "sha256:subtitles" },
          voiceManifest: { checksum: "sha256:voice" },
        },
        translationProvider: { provider: "mock", providerMode: "LOCAL" },
        voice: { provider: "mock", providerMode: "LOCAL" },
        trace: {
          sourceContextRefCount: 1,
          sourceCitationCount: 1,
          sourceContextRefIds: ["context_001"],
          sourceCitationIndexes: [1],
          sourceClaimSupportIds: ["support_001"],
          sourceEvaluationId: "evaluation_001",
          sourceEvaluationChecksum: "sha256:evaluation001",
          evaluationStatus: "PASSED",
        },
      }));
    }
    if (path.endsWith("/avatar-consents")) {
      return route.fulfill(json({
        consentRecordId: "consent_001",
        sourceRunId: "run_001",
        sourceContextRefIds: ["context_001"],
        sourceCitationIndexes: [1],
        sourceEvaluationId: "evaluation_001",
        sourceEvaluationChecksum: "sha256:evaluation001",
        evaluationStatus: "PASSED",
        consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
        consentStatementText: "Synthetic presenter approved for this local demo.",
      }));
    }
    if (path.endsWith("/avatar-renders")) {
      return route.fulfill(json({
        avatarRenderId: "render_001",
        status: "COMPLETED",
        renderJobStatus: "COMPLETED",
        sourceRunId: "run_001",
        sourceScriptText: "The security review is still in progress. [1]",
        avatarProvider: { provider: "mock", providerMode: "LOCAL" },
        providerConfig: {
          provider: "mock",
          providerMode: "LOCAL",
          adapterKind: "MOCK_LOCAL",
          allowNetworkEgress: false,
          requiresApiKey: false,
          supportsRealVideo: false,
          supportsClonedIdentity: false,
        },
        disclosure: {
          consentStatus: "CONFIRMED",
          clonedIdentity: false,
          message: "Synthetic local presenter. No cloned identity.",
        },
        trace: {
          sourceContextRefCount: 1,
          sourceCitationCount: 1,
          sourceContextRefIds: ["context_001"],
          sourceCitationIndexes: [1],
          sourceEvaluationId: "evaluation_001",
          sourceEvaluationChecksum: "sha256:evaluation001",
          evaluationStatus: "PASSED",
          multilingualRunId: "multilingual_001",
          targetLanguage: "en",
          translatedScriptChecksum: "sha256:script",
          subtitlesChecksum: "sha256:subtitles",
          voiceManifestChecksum: "sha256:voice",
        },
      }));
    }
    return route.abort();
  });
}

test.describe("Quiet Presence mocked product UI", () => {
  test("keeps host context visible and exposes local grounded evidence", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await mockQuietPresencePipeline(page);
    await page.goto("/demo");

    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
    await expect(page.getByRole("complementary", { name: "NarraTwin project guide" })).toBeVisible();
    await page.getByRole("button", { name: "Run grounded demo" }).click();
    await expect(page.getByRole("heading", { name: "Why is deployment blocked?" })).toBeVisible();
    await expect(page.getByText("The security review is still in progress. [1]").first()).toBeVisible();
    await page.getByRole("button", { name: /Verified sources/ }).click();
    await expect(page.getByText("Security review must pass before deployment.")).toBeVisible();
    await expect(page.getByText("Passed evaluation · 0 unsupported claims")).toBeVisible();
    await expect(page.getByText("No network egress")).toBeVisible();
    await expect(page.getByText("Verified project source").first()).toBeVisible();
    await expect(page.getByText("Local providers · mock / mock / mock")).toBeVisible();
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

  test("collapses the ribbon and opens a focus stage without losing host context", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/demo");

    await page.getByRole("button", { name: "Minimize guide" }).click();
    await expect(page.locator('[data-guide-state="collapsed"]')).toBeVisible();
    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();

    await page.getByRole("button", { name: "Expand guide" }).click();
    await page.getByRole("button", { name: "Expand focus" }).click();
    await expect(page.getByRole("dialog", { name: "NarraTwin focus stage" })).toBeVisible();
    await expect(page.getByText("Synthetic presenter preview · still image")).toBeVisible();
    const close = page.getByRole("button", { name: "Close focus stage" });
    await expect(close).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(page.getByRole("dialog").getByRole("button", { name: "Run grounded demo" })).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(close).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Expand focus" })).toBeFocused();
  });

  test("uses a full-screen mobile guide with an explicit return to the host project", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/demo");

    await expect(page.locator('[data-mobile-guide="open"]')).toBeVisible();
    await expect(page.getByRole("button", { name: "Back to project" })).toBeVisible();
    await page.getByRole("button", { name: "Back to project" }).click();
    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open NarraTwin guide" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open NarraTwin guide" })).toBeFocused();
  });

  test("minimize returns mobile users to the host and captions truthfully control translated text", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 700 });
    await mockQuietPresencePipeline(page);
    await page.goto("/demo");
    await page.getByRole("button", { name: "Run grounded demo" }).click();
    await expect(page.getByTestId("translated-captions")).toBeVisible();
    await page.getByRole("button", { name: /Captions on/ }).click();
    await expect(page.getByTestId("translated-captions")).toHaveCount(0);
    await page.getByRole("button", { name: "Minimize guide" }).click();
    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open NarraTwin guide" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Open NarraTwin guide" })).toBeFocused();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth)).toBe(false);
  });

  test("defaults to the bounded 60 px ribbon on a short laptop viewport", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/demo");
    await expect(page.locator('[data-guide-state="collapsed"]')).toBeVisible();
    await expect(page.locator('[data-guide-state="collapsed"]')).toHaveCSS("height", "60px");
    await expect(page.getByRole("heading", { name: "Release 2.4.0" })).toBeVisible();
  });

  test("shows a bounded error and no fabricated evidence when the API fails", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.route("**/api/v1/projects", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ message: "sensitivity-canary must never reach the interface" }),
      }),
    );
    await page.goto("/demo");
    await page.getByRole("button", { name: "Run grounded demo" }).click();

    await expect(
      page.getByRole("complementary", { name: "NarraTwin project guide" }).getByRole("alert"),
    ).toContainText("could not complete safely");
    await expect(page.getByText("sensitivity-canary")).toHaveCount(0);
    await expect(page.getByText("Passed evaluation · 0 unsupported claims")).toHaveCount(0);
  });

  test("traverses the real local/mock API through the browser without request interception", async ({ page }) => {
    test.skip(!process.env.NARRATWIN_DEMO_LOCAL_E2E, "Run only with the local mock backend on the configured proxy.");
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/demo");
    await page.getByRole("button", { name: "Run grounded demo" }).click();
    await expect(page.getByText("Verified project source").first()).toBeVisible();
    await expect(page.getByText("No network egress")).toBeVisible();
    await expect(page.getByText("Local providers · mock / mock / mock")).toBeVisible();
  });
});
