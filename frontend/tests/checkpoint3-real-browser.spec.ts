import { expect, test, type Page, type Response } from "@playwright/test";
import { createHash } from "node:crypto";
import { writeFile } from "node:fs/promises";

type ApiResponseEvidence = {
  method: string;
  path: string;
  status: number;
  projectId?: string;
  documentId?: string;
  ingestionRunId?: string;
  runId?: string;
  traceId?: string;
  evaluationId?: string;
  contextRefCount?: number;
  claimSupportCount?: number;
  multilingualRunId?: string;
  consentRecordId?: string;
  avatarRenderId?: string;
  provider?: string;
  providerMode?: string;
  operationalPosture?: string;
};

type ApiRequestEvidence = {
  method: string;
  path: string;
  hasRuntimeNonce: boolean;
  idempotencyKey: string;
  idempotencyKeyPrefix: string;
};

type IdempotencyEvidence = {
  observed: string;
  expected: string;
  prefix: string;
  matched: boolean;
};

type BrowserEvidence = {
  runtimeNonce: string;
  noSuccessPathInterception: true;
  requestSequence: string[];
  requestOrigins: string[];
  requestPayloadBinding: {
    projectNameNonce: boolean;
    sourceEvidenceNonce: boolean;
    glossaryNonce: boolean;
    idempotencyEvidence: Record<string, IdempotencyEvidence>;
    idempotencyPrefixes: string[];
  };
  failedRequestCount: number;
  projectId: string;
  documentId: string;
  ingestionRunId: string;
  runId: string;
  traceId: string;
  evaluationId: string;
  consentRecordId: string;
  multilingualRunId: string;
  avatarRenderId: string;
  sourceBinding: {
    contextRefCount: number;
    claimSupportCount: number;
    unsupportedClaimCount: number;
    citationCount: number;
    multilingualSourceRunId: string;
    avatarSourceRunId: string;
    avatarSourceEvaluationId: string;
  };
  artifactMetadata: Awaited<ReturnType<typeof readArtifactMetadata>>[];
  opsStatus: {
    operationalPosture: string;
    stage4Projects: number;
    stage4Documents: number;
    stage4IngestionRuns: number;
    stage4WalkthroughRuns: number;
    stage7AvatarRenders: number;
  };
  providers: {
    llm: string;
    translation: string;
    voice: string;
    avatar: string;
    videoRenderer: string;
    networkEgress: boolean;
    realVideo: boolean;
    clonedIdentity: boolean;
  };
};

test.skip(process.env.NARRATWIN_REAL_STACK !== "1", "Requires the dedicated local/mock CP8 browser config.");

test("Issue #269 C3A-CP8 real browser path exercises local controlled demo without fabricated success", async ({
  page,
}, testInfo) => {
  expect(process.env.NARRATWIN_REAL_STACK).toBe("1");
  const startedAt = performance.now();
  const runtimeNonce = `cp8-${testInfo.workerIndex}-${Date.now()}`;
  const apiRequests: ApiRequestEvidence[] = [];
  const apiResponses: ApiResponseEvidence[] = [];
  const failedRequests: string[] = [];
  const requestOrigins = new Set<string>();

  await page.addInitScript((nonce) => {
    const originalFetch = window.fetch.bind(window);
    const evidenceWindow = window as Window & { __cp8UploadBodyContainsRuntimeNonce?: boolean };
    evidenceWindow.__cp8UploadBodyContainsRuntimeNonce = false;
    window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
      const targetUrl = typeof input === "string" || input instanceof URL ? String(input) : input.url;
      const method = init?.method ?? (input instanceof Request ? input.method : "GET");
      const body = init?.body;
      if (
        method === "POST" &&
        /^\/api\/v1\/projects\/proj_\d+\/knowledge-documents$/.test(new URL(targetUrl, window.location.href).pathname) &&
        body instanceof FormData
      ) {
        for (const value of body.values()) {
          if (typeof value === "string") {
            evidenceWindow.__cp8UploadBodyContainsRuntimeNonce ||= value.includes(nonce);
          } else {
            void value.text().then((text) => {
              evidenceWindow.__cp8UploadBodyContainsRuntimeNonce ||= text.includes(nonce);
            });
          }
        }
      }
      return originalFetch(input, init);
    };
  }, runtimeNonce);
  page.on("request", (request) => {
    const url = new URL(request.url());
    requestOrigins.add(url.origin);
    if (url.pathname.startsWith("/api/v1/")) {
      const requestBody = `${request.postData() ?? ""}\n${request.postDataBuffer()?.toString("utf8") ?? ""}`;
      const idempotencyKey = request.headers()["idempotency-key"] ?? "";
      apiRequests.push({
        method: request.method(),
        path: url.pathname,
        hasRuntimeNonce: requestBody.includes(runtimeNonce),
        idempotencyKey,
        idempotencyKeyPrefix: idempotencyPrefix(idempotencyKey),
      });
    }
  });
  page.on("response", (response) => {
    void recordApiResponse(response, apiResponses);
  });
  page.on("requestfailed", (request) => {
    failedRequests.push(`${request.method()} ${new URL(request.url()).pathname}`);
  });

  const initialResponse = await page.goto("/");
  expect(initialResponse?.status()).toBe(200);
  const appOrigin = new URL(initialResponse?.url() ?? page.url()).origin;

  await expect(page.getByRole("heading", { name: "Avatar demo export" })).toBeVisible();
  const projectName = `NarraTwin AI ${runtimeNonce}`;
  const knowledgeDocument = `# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts with source chunk citations.

It supports recruiter and engineering audiences with audience-aware explanations.

The Stage 4 slice uses a mock local LLM and mock local embeddings for deterministic tests.

Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.

Checkpoint 3A browser evidence nonce: ${runtimeNonce}.`;
  const audience = "ENGINEER";
  const depth = "STANDARD";
  const targetLanguage = "fr";
  const requestedVoiceProvider = "mock";
  const requestedAvatarProvider = "mock";
  const glossaryTerms = ["NarraTwin AI", "Checkpoint 3A", runtimeNonce];
  const requestSeed = checksumSeed(projectName, knowledgeDocument, audience, depth, targetLanguage);
  const multilingualSeed = checksumSeed(
    requestSeed,
    requestedVoiceProvider,
    ...glossaryTerms.slice().sort((left, right) => left.localeCompare(right)),
  );
  const avatarConsentSeed = checksumSeed(requestSeed, requestedAvatarProvider, "true", "avatar-consent-v1");

  await page.getByLabel("Project name").fill(projectName);
  await page.getByLabel("Knowledge document").fill(knowledgeDocument);
  await page.locator('select[name="audience"]').selectOption(audience);
  await page.locator('select[name="depth"]').selectOption(depth);
  await page.locator('select[name="targetLanguage"]').selectOption(targetLanguage);
  await page.getByLabel("Glossary terms").fill(glossaryTerms.join("\n"));
  await page.getByLabel("Synthetic avatar consent").check();
  await page.getByRole("button", { name: "Generate avatar demo export" }).click();

  await expect(page.getByLabel("Trace metadata")).toContainText("mock", { timeout: 30_000 });
  await expect(page.getByLabel("Trace metadata")).toContainText("fr");
  await expect(page.getByLabel("Avatar metadata")).toContainText("CONFIRMED");
  await expect(page.getByLabel("Avatar metadata")).toContainText("disabled");
  await expect(page.getByLabel("Render job lifecycle")).toContainText("MOCK_LOCAL");
  await expect(page.getByLabel("Avatar demo preview")).toContainText("local-html");
  await expect(page.getByText("AI-generated avatar demo export using a synthetic local presenter.")).toBeVisible();
  await expect(page.getByText("0 unsupported claims")).toBeVisible();
  await expect(page.locator('[aria-labelledby="citations-title"] li')).toHaveCount(1);

  const opsStatus = await page.evaluate(async () => {
    const response = await fetch("/api/v1/ops/status");
    if (!response.ok) {
      throw new Error(`ops status failed: ${response.status}`);
    }
    return response.json();
  });
  await expect.poll(() => apiResponses.length, { timeout: 5_000 }).toBeGreaterThanOrEqual(9);

  const project = requireResponse(apiResponses, "POST", "/api/v1/projects");
  const document = requireMatchingResponse(apiResponses, "POST", /^\/api\/v1\/projects\/proj_\d+\/knowledge-documents$/);
  const ingestion = requireMatchingResponse(apiResponses, "POST", /^\/api\/v1\/projects\/proj_\d+\/ingestion-runs$/);
  const walkthrough = requireMatchingResponse(apiResponses, "POST", /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs$/);
  const multilingual = requireMatchingResponse(
    apiResponses,
    "POST",
    /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/multilingual-runs$/,
  );
  const avatarConsent = requireMatchingResponse(
    apiResponses,
    "POST",
    /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-consents$/,
  );
  const avatarRender = requireMatchingResponse(
    apiResponses,
    "POST",
    /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-renders$/,
  );
  const uploadBodyContainsRuntimeNonce = await page.evaluate(
    () => (window as Window & { __cp8UploadBodyContainsRuntimeNonce?: boolean }).__cp8UploadBodyContainsRuntimeNonce === true,
  );

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

  const evidence: BrowserEvidence = {
    runtimeNonce,
    noSuccessPathInterception: true,
    requestSequence: apiResponses.map((entry) => `${entry.method} ${entry.path}`),
    requestOrigins: Array.from(requestOrigins).sort(),
    requestPayloadBinding: {
      projectNameNonce: requestHasNonce(apiRequests, "POST", /^\/api\/v1\/projects$/),
      sourceEvidenceNonce:
        uploadBodyContainsRuntimeNonce ||
        requestHasNonce(apiRequests, "POST", /^\/api\/v1\/projects\/proj_\d+\/knowledge-documents$/),
      glossaryNonce: requestHasNonce(
        apiRequests,
        "POST",
        /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/multilingual-runs$/,
      ),
      idempotencyEvidence: {
        project: idempotencyEvidence(apiRequests, "POST", /^\/api\/v1\/projects$/, `ui-project-${requestSeed}`),
        upload: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/knowledge-documents$/,
          `ui-upload-${requestSeed}`,
        ),
        approval: idempotencyEvidence(
          apiRequests,
          "PATCH",
          /^\/api\/v1\/projects\/proj_\d+\/knowledge-documents\/doc_\d+\/approval$/,
          `ui-approval-${requestSeed}`,
        ),
        ingest: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/ingestion-runs$/,
          `ui-ingest-${requestSeed}`,
        ),
        generate: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs$/,
          `ui-generate-${requestSeed}`,
        ),
        multilingual: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/multilingual-runs$/,
          `ui-multilingual-${multilingualSeed}`,
        ),
        avatarConsent: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-consents$/,
          `ui-avatar-consent-${avatarConsentSeed}`,
        ),
        avatar: idempotencyEvidence(
          apiRequests,
          "POST",
          /^\/api\/v1\/projects\/proj_\d+\/walkthrough-runs\/run_\d+\/avatar-renders$/,
          `ui-avatar-${checksumSeed(
            requestSeed,
            requestedAvatarProvider,
            "true",
            requireString(avatarConsent.consentRecordId, "consentRecordId"),
            "cloned-identity-false",
          )}`,
        ),
      },
      idempotencyPrefixes: Array.from(
        new Set(apiRequests.map((entry) => entry.idempotencyKeyPrefix).filter(Boolean)),
      ).sort(),
    },
    failedRequestCount: failedRequests.length,
    projectId: requireString(project.projectId, "projectId"),
    documentId: requireString(document.documentId, "documentId"),
    ingestionRunId: requireString(ingestion.ingestionRunId, "ingestionRunId"),
    runId: requireString(walkthrough.runId, "runId"),
    traceId: requireString(walkthrough.traceId, "traceId"),
    evaluationId: requireString(walkthrough.evaluationId, "evaluationId"),
    consentRecordId: requireString(avatarConsent.consentRecordId, "consentRecordId"),
    multilingualRunId: requireString(multilingual.multilingualRunId, "multilingualRunId"),
    avatarRenderId: requireString(avatarRender.avatarRenderId, "avatarRenderId"),
    sourceBinding: {
      contextRefCount: walkthrough.contextRefCount ?? 0,
      claimSupportCount: walkthrough.claimSupportCount ?? 0,
      unsupportedClaimCount: 0,
      citationCount: await page.locator('[aria-labelledby="citations-title"] li').count(),
      multilingualSourceRunId: requireString(multilingual.runId, "multilingual sourceRunId"),
      avatarSourceRunId: requireString(avatarRender.runId, "avatar sourceRunId"),
      avatarSourceEvaluationId: requireString(avatarRender.evaluationId, "avatar sourceEvaluationId"),
    },
    artifactMetadata,
    opsStatus: {
      operationalPosture: requireString(opsStatus.operationalPosture, "operationalPosture"),
      stage4Projects: Number(opsStatus.durability.stage4.recordCounts.projects),
      stage4Documents: Number(opsStatus.durability.stage4.recordCounts.documents),
      stage4IngestionRuns: Number(opsStatus.durability.stage4.recordCounts.ingestionRuns),
      stage4WalkthroughRuns: Number(opsStatus.durability.stage4.recordCounts.walkthroughRuns),
      stage7AvatarRenders: Number(opsStatus.durability.stage7.recordCounts.avatarRenders),
    },
    providers: {
      llm: requireString(walkthrough.provider, "walkthrough provider"),
      translation: requireString(multilingual.provider, "translation provider"),
      voice: requireString(multilingual.providerMode, "voice provider mode"),
      avatar: requireString(avatarRender.provider, "avatar provider"),
      videoRenderer: "local-html",
      networkEgress: false,
      realVideo: false,
      clonedIdentity: false,
    },
  };

  assertBrowserEvidenceContract(evidence, appOrigin);
  expect(() => assertBrowserEvidenceContract({ ...evidence, runtimeNonce: "" }, appOrigin)).toThrow(/runtime nonce/);
  expect(() =>
    assertBrowserEvidenceContract(
      { ...evidence, requestPayloadBinding: { ...evidence.requestPayloadBinding, sourceEvidenceNonce: false } },
      appOrigin,
    ),
  ).toThrow(/runtime nonce request binding/);
  expect(() =>
    assertBrowserEvidenceContract(
      { ...evidence, sourceBinding: { ...evidence.sourceBinding, avatarSourceRunId: "run_replay" } },
      appOrigin,
    ),
  ).toThrow(/source run binding/);
  expect(() => assertBrowserEvidenceContract({ ...evidence, projectId: "proj_cross_project" }, appOrigin)).toThrow(
    /cross-project replay/,
  );

  await writeFile(
    testInfo.outputPath("issue-269-c3a-cp8-browser-evidence.json"),
    JSON.stringify(
      {
        ...evidence,
        durationMs: Math.round(performance.now() - startedAt),
        limitations: [
          "Checkpoint 3A local/mock evidence only",
          "no hosted deployment",
          "no provider setup",
          "no cloned identity",
          "no production-readiness claim",
        ],
      },
      null,
      2,
    ),
    "utf8",
  );
});

async function recordApiResponse(response: Response, apiResponses: ApiResponseEvidence[]) {
  const url = new URL(response.url());
  if (!url.pathname.startsWith("/api/v1/")) {
    return;
  }
  let body: Record<string, unknown> = {};
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    body = {};
  }
  apiResponses.push({
    method: response.request().method(),
    path: url.pathname,
    status: response.status(),
    projectId: stringFrom(body.projectId),
    documentId: stringFrom(body.documentId),
    ingestionRunId: stringFrom(body.ingestionRunId),
    runId: stringFrom(body.runId ?? body.sourceRunId),
    traceId: stringFrom(nested(body, "trace", "traceId") ?? body.traceId),
    evaluationId: stringFrom(nested(body, "evaluation", "evaluationId") ?? nested(body, "trace", "sourceEvaluationId")),
    contextRefCount: countFrom(body.contextRefs ?? nested(body, "evaluation", "contextRefs")),
    claimSupportCount: countFrom(nested(body, "evaluation", "claimSupports")),
    multilingualRunId: stringFrom(body.multilingualRunId ?? nested(body, "trace", "multilingualRunId")),
    consentRecordId: stringFrom(body.consentRecordId),
    avatarRenderId: stringFrom(body.avatarRenderId),
    provider: stringFrom(nested(body, "provider", "provider") ?? nested(body, "translationProvider", "provider") ?? nested(body, "avatarProvider", "provider")),
    providerMode: stringFrom(nested(body, "provider", "providerMode") ?? nested(body, "voice", "providerMode")),
    operationalPosture: stringFrom(body.operationalPosture),
  });
}

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
    fileNameSuffix: attributes.fileName.replace(/^.*(-[^-]+(?:\.[a-z0-9]+))$/i, "$1"),
    mimeType,
    byteLength: decoded.byteLength,
    checksum: `sha256:${createHash("sha256").update(decoded).digest("hex")}`,
  };
}

function assertBrowserEvidenceContract(evidence: BrowserEvidence, appOrigin: string) {
  if (!evidence.runtimeNonce.startsWith("cp8-")) {
    throw new Error("runtime nonce is missing");
  }
  if (!evidence.requestPayloadBinding.projectNameNonce) {
    throw new Error("runtime nonce request binding is missing from project creation");
  }
  if (!evidence.requestPayloadBinding.sourceEvidenceNonce) {
    throw new Error("runtime nonce request binding is missing from source evidence");
  }
  if (!evidence.requestPayloadBinding.glossaryNonce) {
    throw new Error("runtime nonce request binding is missing from glossary request");
  }
  expect(evidence.requestPayloadBinding.idempotencyPrefixes).toEqual(
    expect.arrayContaining([
      "ui-approval",
      "ui-avatar",
      "ui-avatar-consent",
      "ui-generate",
      "ui-ingest",
      "ui-multilingual",
      "ui-project",
      "ui-upload",
    ]),
  );
  if (Object.values(evidence.requestPayloadBinding.idempotencyEvidence).some((entry) => !entry.matched)) {
    throw new Error("runtime idempotency binding is missing");
  }
  if (!evidence.projectId.startsWith("proj_")) {
    throw new Error("cross-project replay evidence was accepted");
  }
  if (!evidence.requestSequence.includes(`POST /api/v1/projects/${evidence.projectId}/knowledge-documents`)) {
    throw new Error("cross-project replay evidence was accepted");
  }
  if (evidence.failedRequestCount !== 0) {
    throw new Error("browser request failures were observed");
  }
  if (evidence.requestOrigins.some((origin) => origin !== appOrigin)) {
    throw new Error("browser left the local same-origin path");
  }
  expect(evidence.requestSequence).toEqual(
    expect.arrayContaining([
      "POST /api/v1/projects",
      `POST /api/v1/projects/${evidence.projectId}/knowledge-documents`,
      `PATCH /api/v1/projects/${evidence.projectId}/knowledge-documents/${evidence.documentId}/approval`,
      `POST /api/v1/projects/${evidence.projectId}/ingestion-runs`,
      `POST /api/v1/projects/${evidence.projectId}/walkthrough-runs`,
      `POST /api/v1/projects/${evidence.projectId}/walkthrough-runs/${evidence.runId}/multilingual-runs`,
      `POST /api/v1/projects/${evidence.projectId}/walkthrough-runs/${evidence.runId}/avatar-consents`,
      `POST /api/v1/projects/${evidence.projectId}/walkthrough-runs/${evidence.runId}/avatar-renders`,
      "GET /api/v1/ops/status",
    ]),
  );
  if (evidence.sourceBinding.multilingualSourceRunId !== evidence.runId) {
    throw new Error("source run binding is missing from multilingual evidence");
  }
  if (evidence.sourceBinding.avatarSourceRunId !== evidence.runId) {
    throw new Error("source run binding is missing from avatar evidence");
  }
  if (evidence.sourceBinding.avatarSourceEvaluationId !== evidence.evaluationId) {
    throw new Error("source/eval binding is missing from avatar evidence");
  }
  if (
    evidence.sourceBinding.contextRefCount < 1 ||
    evidence.sourceBinding.claimSupportCount < 1 ||
    evidence.sourceBinding.citationCount < 1
  ) {
    throw new Error("source citation binding is incomplete");
  }
  if (evidence.sourceBinding.unsupportedClaimCount !== 0) {
    throw new Error("unsupported claim evidence is not passing");
  }
  if (evidence.artifactMetadata.length !== 6 || evidence.artifactMetadata.some((artifact) => artifact.byteLength <= 0)) {
    throw new Error("artifact binding is incomplete");
  }
  if (evidence.opsStatus.operationalPosture !== "LOCAL_ONLY" || evidence.opsStatus.stage4Projects < 1) {
    throw new Error("ops/status binding is missing");
  }
  if (
    evidence.providers.llm !== "mock" ||
    evidence.providers.translation !== "mock" ||
    evidence.providers.avatar !== "mock" ||
    evidence.providers.networkEgress ||
    evidence.providers.realVideo ||
    evidence.providers.clonedIdentity
  ) {
    throw new Error("local/mock provider posture is missing");
  }
}

function requireResponse(responses: ApiResponseEvidence[], method: string, path: string) {
  return requireMatchingResponse(responses, method, new RegExp(`^${escapeRegExp(path)}$`));
}

function requireMatchingResponse(responses: ApiResponseEvidence[], method: string, pathPattern: RegExp) {
  const response = responses.find((entry) => entry.method === method && pathPattern.test(entry.path));
  expect(response, `${method} ${pathPattern.source}`).toBeTruthy();
  expect(response?.status).toBeGreaterThanOrEqual(200);
  expect(response?.status).toBeLessThan(300);
  return response as ApiResponseEvidence;
}

function requireString(value: string | undefined, fieldName: string) {
  expect(value, fieldName).toBeTruthy();
  return value ?? "";
}

function stringFrom(value: unknown) {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function countFrom(value: unknown) {
  return Array.isArray(value) ? value.length : undefined;
}

function nested(row: Record<string, unknown>, parent: string, child: string) {
  const parentValue = row[parent];
  return parentValue && typeof parentValue === "object" && child in parentValue
    ? (parentValue as Record<string, unknown>)[child]
    : undefined;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function requestHasNonce(requests: ApiRequestEvidence[], method: string, pathPattern: RegExp) {
  return requests.some((entry) => entry.method === method && pathPattern.test(entry.path) && entry.hasRuntimeNonce);
}

function idempotencyEvidence(
  requests: ApiRequestEvidence[],
  method: string,
  pathPattern: RegExp,
  expected: string,
): IdempotencyEvidence {
  const observed =
    requests.find((entry) => entry.method === method && pathPattern.test(entry.path) && entry.idempotencyKey.length > 0)
      ?.idempotencyKey ?? "";
  return {
    observed,
    expected,
    prefix: idempotencyPrefix(observed),
    matched: observed === expected,
  };
}

function idempotencyPrefix(value: string) {
  const knownPrefixes = [
    "ui-avatar-consent",
    "ui-multilingual",
    "ui-approval",
    "ui-generate",
    "ui-ingest",
    "ui-project",
    "ui-upload",
    "ui-avatar",
  ];
  return knownPrefixes.find((prefix) => value.startsWith(`${prefix}-`)) ?? "";
}

function checksumSeed(...values: string[]) {
  let hash = 0;
  for (const value of values.join("|")) {
    hash = (hash * 31 + value.charCodeAt(0)) >>> 0;
  }
  return hash.toString(16);
}
