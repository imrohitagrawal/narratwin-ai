import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";

function artifactFromText(fileName: string, mimeType: string, text: string) {
  return {
    fileName,
    mimeType,
    contentBase64: Buffer.from(text, "utf-8").toString("base64"),
    checksum: `sha256:${createHash("sha256").update(text).digest("hex")}`,
  };
}

const languageCatalogResponse = {
  languages: [
    {
      languageTag: "es",
      englishName: "Spanish",
      nativeName: "Español",
      script: "Latin",
      direction: "ltr",
      marketPriority: 1,
      regionGroup: "Europe/Latin America",
      localDemoSupportStatus: "SUPPORTED",
      providerSupportStatus: "LOCAL_DEMO_FIXTURE",
      testCoverageLevel: "CHECKPOINT3A_EXHAUSTIVE",
    },
  ],
};

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

const refusedWalkthroughResponse = {
  runId: "run_ui_refused",
  tenantId: "tenant_local",
  actorId: "user_local",
  projectId: "proj_ui",
  status: "REFUSED",
  evaluationStatus: "REFUSED",
  audience: "RECRUITER",
  requestedLanguage: "en",
  depth: "CONCISE",
  style: "CONFIDENT",
  acceptedScriptText: null,
  contextRefs: [],
  provider: { provider: "mock", providerMode: "LOCAL" },
  trace: { traceId: "trace_ui_refused", latencyMs: 0, estimatedCost: 0 },
  createdAt: "2026-06-30T00:00:00Z",
  failure: {
    reasonCode: "LOW_RETRIEVAL_CONFIDENCE",
    message: "The request was refused because retrieved context was insufficient.",
    unsupportedClaimCount: 0,
  },
};

const translatedScriptText =
  "Para ingenieros, NarraTwin AI convierte el conocimiento aprobado del proyecto en guiones de recorrido fundamentados con citas de origen. [1]";
const subtitlesText =
  "1\n00:00:00,000 --> 00:00:04,000\nPara ingenieros, NarraTwin AI convierte el conocimiento aprobado del proyecto en guiones de recorrido fundamentados con citas de origen. [1]\n\n";
const voiceManifestText = JSON.stringify({
  provider: "mock",
  providerMode: "LOCAL",
  language: "es",
  languageDisplayName: "Spanish",
  textChecksum: `sha256:${createHash("sha256").update(translatedScriptText).digest("hex")}`,
  durationSecondsEstimate: 4,
  mockAudioProfile: {
    durationMillisecondsEstimate: 4000,
    sampleRateHz: 16000,
    channels: 1,
  },
  disclosure: "Mock local TTS placeholder. No cloned voice or paid provider was used.",
});
const transcriptSegments = [
  {
    segmentId: "seg_001",
    sourceText: walkthroughResponse.acceptedScriptText,
    targetLanguage: "es",
    targetText: translatedScriptText,
    englishReferenceText: walkthroughResponse.acceptedScriptText,
    citationMarkers: ["[1]"],
    citationIndexes: [1],
    contextRefIds: ["ctx_ui_001"],
    claimSupportIds: ["claimsup_ui_001"],
    sourceRunId: "run_ui_smoke",
    evaluationId: "eval_ui",
  },
];
const transcriptCorrectness = {
  validationStatus: "PASSED",
  script: "Latin",
  direction: "ltr",
  segmentCount: 1,
  citationIndexes: [1],
};
const translatedScriptArtifact = artifactFromText("run_ui_smoke-es-script.md", "text/markdown", translatedScriptText);
const subtitlesArtifact = artifactFromText("run_ui_smoke-es.srt", "application/x-subrip", subtitlesText);
const voiceManifestArtifact = artifactFromText("voice-manifest-es.json", "application/json", voiceManifestText);
const transcriptMetadataText = JSON.stringify({
  multilingualRunId: "mlrun_ui_smoke",
  sourceRunId: "run_ui_smoke",
  targetLanguage: "es",
  sourceContextRefIds: ["ctx_ui_001"],
  sourceCitationIndexes: [1],
  transcriptCorrectness,
  transcriptSegments,
});
const transcriptMetadataArtifact = artifactFromText(
  "run_ui_smoke-es-metadata.json",
  "application/json",
  transcriptMetadataText,
);

const multilingualResponse = {
  multilingualRunId: "mlrun_ui_smoke",
  sourceRunId: "run_ui_smoke",
  sourceLanguage: "en",
  targetLanguage: "es",
  status: "COMPLETED",
  sourceScriptText: walkthroughResponse.acceptedScriptText,
  translatedScriptText,
  subtitlesText,
  transcriptSegments,
  transcriptCorrectness,
  glossaryTerms: ["NarraTwin AI"],
  preservedTerms: ["NarraTwin AI"],
  translationProvider: { provider: "mock", providerMode: "LOCAL" },
  voice: {
    provider: "mock",
    providerMode: "LOCAL",
    requestedProvider: "mock",
    language: "es",
    artifact: voiceManifestArtifact,
  },
  artifacts: {
    translatedScript: translatedScriptArtifact,
    subtitles: subtitlesArtifact,
    voiceManifest: voiceManifestArtifact,
    metadata: transcriptMetadataArtifact,
  },
  trace: {
    traceId: "trace_ui_smoke",
    sourceContextRefCount: 1,
    sourceCitationCount: 1,
    sourceContextRefIds: ["ctx_ui_001"],
    sourceCitationIndexes: [1],
    sourceEvaluationId: "eval_ui",
    sourceEvaluationChecksum: "sha256:evaluation",
  },
	};

const stage7MultilingualBundle = {
  sourceRunId: multilingualResponse.sourceRunId,
  multilingualRunId: multilingualResponse.multilingualRunId,
  targetLanguage: multilingualResponse.targetLanguage,
  translatedScriptChecksum: multilingualResponse.artifacts.translatedScript.checksum,
  subtitlesChecksum: multilingualResponse.artifacts.subtitles.checksum,
  voiceManifestChecksum: multilingualResponse.artifacts.voiceManifest.checksum,
  contextRefIds: multilingualResponse.trace.sourceContextRefIds,
  citationIndexes: multilingualResponse.trace.sourceCitationIndexes,
  evaluationId: multilingualResponse.trace.sourceEvaluationId,
  evaluationChecksum: multilingualResponse.trace.sourceEvaluationChecksum,
  providerPosture: {
    translationProvider: multilingualResponse.translationProvider.provider,
    translationProviderMode: multilingualResponse.translationProvider.providerMode,
    voiceProvider: multilingualResponse.voice.provider,
    voiceProviderMode: multilingualResponse.voice.providerMode,
  },
  consentDisclosureVersion: "stage7-synthetic-avatar-consent-v1",
};

const stage7ProviderConfig = {
  provider: "mock",
  providerMode: "LOCAL",
  adapterKind: "MOCK_LOCAL",
  allowNetworkEgress: false,
  requiresApiKey: false,
  supportsRealVideo: false,
  supportsClonedIdentity: false,
};

const stage7SourceMetadata = {
  runId: "run_ui_smoke",
  traceId: "trace_ui_smoke",
  contextRefIds: multilingualResponse.trace.sourceContextRefIds,
  citationIndexes: multilingualResponse.trace.sourceCitationIndexes,
  evaluationId: multilingualResponse.trace.sourceEvaluationId,
  evaluationChecksum: multilingualResponse.trace.sourceEvaluationChecksum,
  evaluationStatus: "PASSED",
};

const avatarRenderResponse = {
  avatarRenderId: "avrun_ui_smoke",
  consentRecordId: "consent_ui_smoke",
  sourceRunId: "run_ui_smoke",
  status: "COMPLETED",
  renderJobStatus: "COMPLETED",
  renderJobStatusHistory: [
    { status: "QUEUED", message: "Avatar render job queued." },
    { status: "RUNNING", message: "Avatar provider render started." },
    { status: "COMPLETED", message: "Avatar render job completed." },
  ],
  sourceScriptText: multilingualResponse.translatedScriptText,
  avatarProvider: {
    provider: "mock",
    providerMode: "LOCAL",
    requestedProvider: "mock",
    fallbackReason: null,
  },
	  providerConfig: {
	    ...stage7ProviderConfig,
	  },
  videoRenderer: {
    renderer: "local-html",
    rendererMode: "LOCAL",
    exportFormat: "html",
  },
  disclosure: {
    aiGenerated: true,
    clonedIdentity: false,
    consentRequired: true,
    consentStatus: "CONFIRMED",
    message:
      "AI-generated avatar demo export using a synthetic local presenter. No cloned face, cloned voice, or paid avatar provider was used.",
  },
  artifacts: {
	    demoExport: artifactFromText(
	      "run_ui_smoke-avatar-demo.html",
	      "text/html",
	      "<!doctype html>\n<html lang=\"en\"><body><main>NarraTwin AI Avatar Demo Export</main></body></html>\n",
	    ),
	    renderManifest: artifactFromText(
	      "run_ui_smoke-avatar-render-manifest.json",
	      "application/json",
	      JSON.stringify({
	        publicUseLicenseCheck: "mock-local-provider-only-no-third-party-media",
	        schema: "Stage7AvatarRenderManifest",
	        providerConfig: stage7ProviderConfig,
	        source: stage7SourceMetadata,
	        multilingualBundle: stage7MultilingualBundle,
	      }),
	    ),
	    videoExportPlaceholder: artifactFromText(
	      "run_ui_smoke-video-export-placeholder.json",
	      "application/json",
	      JSON.stringify({
	        publicUseLicenseCheck: "mock-local-provider-only-no-third-party-media",
	        schema: "Stage7VideoExportPlaceholder",
	        realVideoProduced: false,
	        providerConfig: stage7ProviderConfig,
	        source: stage7SourceMetadata,
	        multilingualBundle: stage7MultilingualBundle,
	      }),
	    ),
	  },
  trace: {
    traceId: "trace_ui_smoke",
    sourceContextRefCount: 1,
    sourceCitationCount: 1,
    sourceContextRefIds: ["ctx_ui_001"],
    sourceCitationIndexes: [1],
    sourceEvaluationId: "eval_ui",
    sourceEvaluationChecksum: "sha256:evaluation",
    evaluationStatus: "PASSED",
    multilingualRunId: "mlrun_ui_smoke",
    targetLanguage: "es",
    translatedScriptChecksum: multilingualResponse.artifacts.translatedScript.checksum,
    subtitlesChecksum: multilingualResponse.artifacts.subtitles.checksum,
    voiceManifestChecksum: multilingualResponse.artifacts.voiceManifest.checksum,
  },
};

function checksumSeed(...values: string[]) {
  let hash = 0;
  for (const value of values.join("|")) {
    hash = (hash * 31 + value.charCodeAt(0)) >>> 0;
  }
  return hash.toString(16);
}

test("home page generates a Stage 7 avatar demo export through the API workflow", async ({ page }) => {
  const calls: string[] = [];
  let multilingualIdempotencyKey = "";
  let avatarConsentIdempotencyKey = "";
  let avatarIdempotencyKey = "";
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    calls.push(`${request.method()} ${path}`);

    if (request.method() === "GET" && path === "/api/v1/languages") {
      await route.fulfill({ json: languageCatalogResponse });
      return;
    }
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
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-consents"
    ) {
      avatarConsentIdempotencyKey = request.headers()["idempotency-key"] ?? "";
      expect(await request.postDataJSON()).toEqual({ consentToUseSyntheticAvatar: true });
      await route.fulfill({
        json: {
          consentRecordId: "consent_ui_smoke",
          consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
          consentStatementText:
            "I affirm that I am authorized to approve this Stage 7 synthetic local avatar demo for the selected walkthrough run.",
          requestChecksum: "sha256:ui-consent-request",
        },
      });
      return;
    }
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-renders"
    ) {
      avatarIdempotencyKey = request.headers()["idempotency-key"] ?? "";
      expect(await request.postDataJSON()).toEqual({
        requestedAvatarProvider: "mock",
        consentToUseSyntheticAvatar: true,
        consentRecordId: "consent_ui_smoke",
        clonedIdentityRequested: false,
	        multilingualBundle: stage7MultilingualBundle,
	      });
      await route.fulfill({ json: avatarRenderResponse });
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

  await expect(page.getByRole("heading", { name: "Avatar demo export" })).toBeVisible();
  await page.getByLabel("Synthetic avatar consent").check();
  const defaultKnowledge = await page.getByLabel("Knowledge document").inputValue();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();
  await expect.poll(() => calls, { timeout: 5000 }).toHaveLength(9);
  const baseSeed = checksumSeed(
    "NarraTwin AI",
    defaultKnowledge,
    "RECRUITER",
    "CONCISE",
    "es",
  );
  expect(multilingualIdempotencyKey).not.toBe(`ui-multilingual-${baseSeed}`);
  expect(avatarConsentIdempotencyKey).toBe(
    `ui-avatar-consent-${checksumSeed(baseSeed, "mock", "true", "avatar-consent-v1")}`,
  );
  expect(avatarIdempotencyKey).toBe(
    `ui-avatar-${checksumSeed(baseSeed, "mock", "true", "consent_ui_smoke", "cloned-identity-false")}`,
  );

  await expect(page.getByLabel("Trace metadata")).toContainText("trace_ui_smoke");
  await expect(page.getByLabel("Trace metadata")).toContainText("run_ui_smoke");
  await expect(page.getByLabel("Trace metadata")).toContainText("es");
  await expect(page.getByLabel("Trace metadata")).toContainText("mock");
  await expect(page.getByRole("link", { name: "Download script" })).toHaveAttribute(
    "download",
    "run_ui_smoke-es-script.md",
  );
  await expect(page.getByRole("link", { name: "Download subtitles" })).toHaveAttribute(
    "download",
    "run_ui_smoke-es.srt",
  );
  await expect(page.getByRole("link", { name: "Download voice manifest" })).toHaveAttribute(
    "download",
    "voice-manifest-es.json",
  );
  await expect(page.getByRole("link", { name: "Download avatar demo" })).toHaveAttribute(
    "download",
    "run_ui_smoke-avatar-demo.html",
  );
  await expect(page.getByRole("link", { name: "Download render manifest" })).toHaveAttribute(
    "download",
    "run_ui_smoke-avatar-render-manifest.json",
  );
  await expect(page.getByRole("link", { name: "Download video placeholder" })).toHaveAttribute(
    "download",
    "run_ui_smoke-video-export-placeholder.json",
  );
  await expect(page.getByRole("link", { name: "Download transcript metadata" })).toHaveAttribute(
    "download",
    "run_ui_smoke-es-metadata.json",
  );
  await expect(page.getByLabel("Avatar metadata")).toContainText("local-html");
  await expect(page.getByLabel("Avatar metadata")).toContainText("CONFIRMED");
  await expect(page.getByLabel("Render job lifecycle")).toContainText("COMPLETED");
  await expect(page.getByLabel("Render job lifecycle")).toContainText("MOCK_LOCAL");
  await expect(page.getByLabel("Avatar demo preview")).toContainText("local-html");
  await expect(page.getByLabel("Avatar demo preview")).toContainText("Para ingenieros, NarraTwin AI convierte");
  await expect(page.getByLabel("Export artifact list")).toContainText("Video placeholder");
  await expect(page.getByLabel("Export artifact list")).toContainText("run_ui_smoke-video-export-placeholder.json");
  await expect(page.getByRole("link", { name: "Download export artifact Video placeholder" })).toHaveAttribute(
    "download",
    "run_ui_smoke-video-export-placeholder.json",
  );
  await expect(page.getByText("AI-generated avatar demo export using a synthetic local presenter.")).toBeVisible();
  await expect(page.getByText("0 unsupported claims")).toBeVisible();
  const firstCitation = page.locator("li").filter({ hasText: "chunk_ui_001" });
  await expect(firstCitation.getByText("[1]", { exact: true })).toBeVisible();
  await expect(firstCitation.getByText("stage4_project.md")).toBeVisible();
  await expect(firstCitation.getByText("chunk_ui_001")).toBeVisible();
  expect(calls).toEqual([
    "GET /api/v1/languages",
    "POST /api/v1/projects",
    "POST /api/v1/projects/proj_ui/knowledge-documents",
    "PATCH /api/v1/projects/proj_ui/knowledge-documents/doc_ui/approval",
    "POST /api/v1/projects/proj_ui/ingestion-runs",
    "POST /api/v1/projects/proj_ui/walkthrough-runs",
    "POST /api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/multilingual-runs",
    "POST /api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-consents",
    "POST /api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-renders",
  ]);
});

test("home page stops before media generation when the walkthrough is refused", async ({ page }) => {
  const calls: string[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    calls.push(`${request.method()} ${path}`);

    if (request.method() === "GET" && path === "/api/v1/languages") {
      await route.fulfill({ json: languageCatalogResponse });
      return;
    }
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
      await route.fulfill({ json: refusedWalkthroughResponse });
      return;
    }
    await route.fulfill({ status: 500, json: { error: "unexpected downstream media route" } });
  });

  await page.goto("/");
  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByLabel("Knowledge document").fill("Too little unrelated text.");
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(
    page.getByText("Walkthrough refused: The request was refused because retrieved context was insufficient."),
  ).toBeVisible();
  await page.waitForTimeout(250);

  expect(calls).toEqual([
    "GET /api/v1/languages",
    "POST /api/v1/projects",
    "POST /api/v1/projects/proj_ui/knowledge-documents",
    "PATCH /api/v1/projects/proj_ui/knowledge-documents/doc_ui/approval",
    "POST /api/v1/projects/proj_ui/ingestion-runs",
    "POST /api/v1/projects/proj_ui/walkthrough-runs",
  ]);
  expect(calls.some((call) => call.includes("/multilingual-runs"))).toBe(false);
  expect(calls.some((call) => call.includes("/avatar-consents"))).toBe(false);
  expect(calls.some((call) => call.includes("/avatar-renders"))).toBe(false);
});

test("home page blocks avatar artifacts with mismatched multilingual provenance", async ({ page }) => {
  const mismatchedRenderManifest = artifactFromText(
    "run_ui_smoke-avatar-render-manifest.json",
    "application/json",
    JSON.stringify({
      publicUseLicenseCheck: "mock-local-provider-only-no-third-party-media",
      schema: "Stage7AvatarRenderManifest",
      providerConfig: stage7ProviderConfig,
      source: stage7SourceMetadata,
      multilingualBundle: { ...stage7MultilingualBundle, targetLanguage: "fr" },
    }),
  );
  const mismatchedAvatarRenderResponse = {
    ...avatarRenderResponse,
    artifacts: {
      ...avatarRenderResponse.artifacts,
      renderManifest: mismatchedRenderManifest,
    },
  };

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (request.method() === "GET" && path === "/api/v1/languages") {
      await route.fulfill({ json: languageCatalogResponse });
      return;
    }
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
      await route.fulfill({ json: multilingualResponse });
      return;
    }
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-consents"
    ) {
      await route.fulfill({
        json: {
          consentRecordId: "consent_ui_smoke",
          consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
          consentStatementText:
            "I affirm that I am authorized to approve this Stage 7 synthetic local avatar demo for the selected walkthrough run.",
          requestChecksum: "sha256:ui-consent-request",
        },
      });
      return;
    }
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-renders"
    ) {
      await route.fulfill({ json: mismatchedAvatarRenderResponse });
      return;
    }
    await route.fulfill({ status: 404, json: { error: "unexpected route" } });
  });

  await page.goto("/");
  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(page.getByRole("button", { name: "Download render manifest blocked" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Download render manifest" })).toHaveCount(0);
  await expect(page.getByText("Blocked: JSON metadata shape is invalid.").first()).toBeVisible();
});

test("home page shows bounded durable avatar consent render errors", async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (request.method() === "GET" && path === "/api/v1/languages") {
      await route.fulfill({ json: languageCatalogResponse });
      return;
    }
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
      await route.fulfill({ json: multilingualResponse });
      return;
    }
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-consents"
    ) {
      await route.fulfill({
        json: {
          consentRecordId: "consent_ui_smoke",
          consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
          consentStatementText:
            "I affirm that I am authorized to approve this Stage 7 synthetic local avatar demo for the selected walkthrough run.",
          requestChecksum: "sha256:ui-consent-request",
        },
      });
      return;
    }
    if (
      request.method() === "POST" &&
      path === "/api/v1/projects/proj_ui/walkthrough-runs/run_ui_smoke/avatar-renders"
    ) {
      await route.fulfill({
        status: 422,
        json: {
          error: {
            code: "AVATAR_CONSENT_INVALID",
            message: "Synthetic avatar consent record is invalid or already consumed.",
          },
        },
      });
      return;
    }
    await route.fulfill({ status: 404, json: { error: "unexpected route" } });
  });

  await page.goto("/");

  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(page.getByRole("alert").filter({ hasText: "AVATAR_CONSENT_INVALID" })).toHaveText(
    "AVATAR_CONSENT_INVALID: Synthetic avatar consent record is invalid or already consumed.",
  );
  await expect(page.getByRole("link", { name: "Download avatar demo" })).toHaveCount(0);
});
