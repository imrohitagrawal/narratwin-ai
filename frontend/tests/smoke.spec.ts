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

const multilingualResponse = {
  multilingualRunId: "mlrun_ui_smoke",
  sourceRunId: "run_ui_smoke",
  sourceLanguage: "en",
  targetLanguage: "es",
  status: "COMPLETED",
  sourceScriptText: walkthroughResponse.acceptedScriptText,
  translatedScriptText:
    "For recruiters, NarraTwin AI convierte approved project knowledge en grounded walkthrough scripts. [1]",
  subtitlesText:
    "1\n00:00:00,000 --> 00:00:04,000\nFor recruiters, NarraTwin AI convierte approved project knowledge en grounded walkthrough scripts. [1]\n\n",
  glossaryTerms: ["NarraTwin AI", "project knowledge", "source chunks"],
  preservedTerms: ["NarraTwin AI", "project knowledge"],
  translationProvider: { provider: "mock", providerMode: "LOCAL" },
  voice: {
    provider: "mock",
    providerMode: "LOCAL",
    requestedProvider: "mock",
    language: "es",
    artifact: {
      fileName: "voice-manifest-es.json",
      mimeType: "application/json",
      contentBase64: "e30=",
      checksum: "sha256:voice",
    },
  },
  artifacts: {
    translatedScript: {
      fileName: "run_ui_smoke-es-script.md",
      mimeType: "text/markdown",
      contentBase64: "U3RhZ2UgNiBzY3JpcHQ=",
      checksum: "sha256:script",
    },
    subtitles: {
      fileName: "run_ui_smoke-es.srt",
      mimeType: "application/x-subrip",
      contentBase64: "MQo=",
      checksum: "sha256:srt",
    },
    voiceManifest: {
      fileName: "voice-manifest-es.json",
      mimeType: "application/json",
      contentBase64: "e30=",
      checksum: "sha256:voice",
    },
  },
  trace: {
    traceId: "trace_ui_smoke",
    sourceContextRefCount: 1,
    sourceCitationCount: 1,
  },
};

function checksumSeed(...values: string[]) {
  let hash = 0;
  for (const value of values.join("|")) {
    hash = (hash * 31 + value.charCodeAt(0)) >>> 0;
  }
  return hash.toString(16);
}

test("home page generates a Stage 6 multilingual walkthrough through the API workflow", async ({ page }) => {
  const calls: string[] = [];
  let multilingualIdempotencyKey = "";
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
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/multilingual-runs"
    ) {
      multilingualIdempotencyKey = request.headers()["idempotency-key"] ?? "";
      await route.fulfill({ json: multilingualResponse });
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

  await expect(page.getByRole("heading", { name: "Multilingual walkthrough generation" })).toBeVisible();
  await page.getByRole("button", { name: "Generate multilingual walkthrough" }).click();
  await expect.poll(() => calls, { timeout: 5000 }).toHaveLength(6);
  const baseSeed = checksumSeed(
    "NarraTwin AI",
    "NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.\n\nEvery generated walkthrough claim must cite retrieved source chunks from approved knowledge.",
    "RECRUITER",
    "CONCISE",
    "es",
  );
  expect(multilingualIdempotencyKey).not.toBe(`ui-multilingual-${baseSeed}`);

  await expect(page.getByLabel("Trace metadata")).toContainText("trace_ui_smoke");
  await expect(page.getByLabel("Trace metadata")).toContainText("run_ui_smoke");
  await expect(page.getByLabel("Trace metadata")).toContainText("es");
  await expect(page.getByRole("link", { name: "Download script" })).toHaveAttribute(
    "download",
    "run_ui_smoke-es-script.md",
  );
  await expect(page.getByRole("link", { name: "Download subtitles" })).toHaveAttribute(
    "download",
    "run_ui_smoke-es.srt",
  );
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
    "POST /api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/multilingual-runs",
  ]);
});
