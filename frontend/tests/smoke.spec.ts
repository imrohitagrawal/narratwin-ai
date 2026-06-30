import { expect, test } from "@playwright/test";

const walkthroughResponse = {
  runId: "run_ui_smoke",
  tenantId: "tenant_local",
  actorId: "user_local",
  projectId: "proj_ui",
  status: "COMPLETED",
  evaluationStatus: "PASSED",
  audience: "RECRUITER",
  requestedLanguage: "en",
  depth: "CONCISE",
  style: "CONFIDENT",
  acceptedScriptText:
    "For recruiters, NarraTwin AI turns approved project knowledge into grounded walkthrough scripts. [1]",
  contextRefs: [
    {
      contextRefId: "ctx_ui_001",
      tenantId: "tenant_local",
      projectId: "proj_ui",
      claimId: "claim_001",
      chunkId: "chunk_ui_001",
      documentId: "doc_ui",
      sourceFilename: "stage4_project.md",
      chunkIndex: 0,
      checksum: "sha256:chunk",
      scriptSpanStart: 0,
      scriptSpanEnd: 92,
      evidenceSnapshot: {
        evidenceSnapshotId: "evsnap_ui_001",
        tenantId: "tenant_local",
        projectId: "proj_ui",
        documentId: "doc_ui",
        chunkId: "chunk_ui_001",
        sourceFilename: "stage4_project.md",
        chunkIndex: 0,
        sourceDocumentChecksum: "sha256:document",
        chunkChecksum: "sha256:chunk",
        chunkingStrategyVersion: "stage4-chunk-v1",
        retrievalScore: 1,
        redactedExcerpt: "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.",
        excerptStart: 0,
        excerptEnd: 75,
        redactionFlags: [],
        capturedAt: "2026-06-30T00:00:00Z",
        snapshotChecksum: "sha256:snapshot",
      },
    },
  ],
  provider: { provider: "mock", providerMode: "LOCAL" },
  trace: { traceId: "trace_ui_smoke", latencyMs: 0, estimatedCost: 0 },
  createdAt: "2026-06-30T00:00:00Z",
  evaluation: {
    schema: "EvaluationSummary",
    evaluationId: "eval_ui",
    evaluationStatus: "PASSED",
    groundednessScore: 1,
    unsupportedClaimCount: 0,
    unsupportedClaims: [],
    claimSupports: [
      {
        claimSupportId: "claimsup_ui_001",
        tenantId: "tenant_local",
        projectId: "proj_ui",
        runId: "run_ui_smoke",
        evaluationId: "eval_ui",
        claimId: "claim_001",
        contextRefId: "ctx_ui_001",
        chunkId: "chunk_ui_001",
        documentId: "doc_ui",
        supportStatus: "SUPPORTED",
        supportScore: 1,
        supportReason: "Supported by retrieved chunk.",
        citationIndex: 1,
      },
    ],
    contextRefCoverage: 1,
    embeddingProvider: "mock",
    embeddingModel: "mock-embedding",
    embeddingModelVersion: "stage4-local-v1",
    embeddingDimension: 16,
    vectorStore: "memory",
    retrievalStrategyVersion: "stage4-rag-v1",
    retrievalTopK: 6,
    retrievalScoreThreshold: 0.72,
    policyVersion: "stage4-grounding-policy-v1",
    schemaVersion: "stage4-evaluation-schema-v1",
    safetyPolicyVersion: "stage4-safety-policy-v1",
    contextRefs: [],
  },
};

test("home page generates a Stage 4 grounded script through the API workflow", async ({ page }) => {
  const calls: string[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    calls.push(`${request.method()} ${path}`);

    if (request.method() === "POST" && path === "/api/v1/projects") {
      await route.fulfill({ json: { projectId: "proj_ui" } });
      return;
    }
    if (request.method() === "POST" && path === "/api/v1/projects/proj_ui/knowledge-documents") {
      await route.fulfill({ json: { documentId: "doc_ui" } });
      return;
    }
    if (
      request.method() === "PATCH" &&
      path === "/api/v1/projects/proj_ui/knowledge-documents/doc_ui/approval"
    ) {
      await route.fulfill({ json: { documentId: "doc_ui", approvalStatus: "APPROVED" } });
      return;
    }
    if (request.method() === "POST" && path === "/api/v1/projects/proj_ui/ingestion-runs") {
      await route.fulfill({ json: { ingestionRunId: "ing_ui", status: "COMPLETED" } });
      return;
    }
    if (request.method() === "POST" && path === "/api/v1/projects/proj_ui/walkthrough-runs") {
      await route.fulfill({ json: walkthroughResponse });
      return;
    }
    await route.fulfill({ status: 404, json: { error: "unexpected route" } });
  });

  const response = await page.goto("/");

  expect(response?.headers()["content-security-policy"]).toBe(
    "default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
  );
  expect(response?.headers()["referrer-policy"]).toBe("no-referrer");
  expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");

  await expect(page.getByRole("heading", { name: "Grounded script generation" })).toBeVisible();
  await page.getByRole("button", { name: "Generate grounded script" }).click();
  await expect.poll(() => calls, { timeout: 5000 }).toHaveLength(5);

  await expect(page.getByLabel("Trace metadata")).toContainText("trace_ui_smoke");
  await expect(page.getByLabel("Trace metadata")).toContainText("run_ui_smoke");
  await expect(page.getByText("0 unsupported claims")).toBeVisible();
  const firstCitation = page.locator("li").filter({ hasText: "chunk_ui_001" });
  await expect(firstCitation.getByText("[1]", { exact: true })).toBeVisible();
  await expect(firstCitation.getByText("stage4_project.md")).toBeVisible();
  await expect(firstCitation.getByText("chunk_ui_001")).toBeVisible();
  expect(calls).toEqual([
    "POST /api/v1/projects",
    "POST /api/v1/projects/proj_ui/knowledge-documents",
    "PATCH /api/v1/projects/proj_ui/knowledge-documents/doc_ui/approval",
    "POST /api/v1/projects/proj_ui/ingestion-runs",
    "POST /api/v1/projects/proj_ui/walkthrough-runs",
  ]);
});
