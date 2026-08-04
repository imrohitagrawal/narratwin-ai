export type GuideDemoInput = {
  projectName: string;
  knowledgeDocument: string;
  audience: string;
  depth: string;
  targetLanguage: string;
  glossaryTerms: string[];
};

export type GuideSource = {
  citationIndex: number;
  filename: string;
  excerpt: string;
  contextRefId: string;
};

export type GuideDemoResult = {
  explanation: string;
  translatedExplanation: string;
  targetLanguage: string;
  sources: GuideSource[];
  evaluation: {
    status: string;
    unsupportedClaimCount: number;
  };
  providerPosture: {
    avatar: string;
    avatarMode: string;
    translation: string;
    translationMode: string;
    voice: string;
    voiceMode: string;
    networkEgress: boolean;
    realMedia: boolean;
    clonedIdentity: boolean;
    consent: "CONFIRMED";
  };
  traceId: string;
  runId: string;
};

type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
type WalkthroughResponse = {
  runId: string;
  status: string;
  acceptedScriptText: string | null;
  contextRefs: Array<{
    contextRefId: string;
    chunkId: string;
    documentId: string;
    sourceFilename: string;
    evidenceSnapshot: { redactedExcerpt: string };
  }>;
  evaluation?: {
    evaluationId: string;
    evaluationStatus: string;
    unsupportedClaimCount: number;
    claimSupports: Array<{
      claimSupportId: string;
      contextRefId: string;
      chunkId: string;
      documentId: string;
      citationIndex: number;
    }>;
  };
  trace?: { traceId?: string };
};

type MultilingualResponse = {
  multilingualRunId: string;
  sourceRunId: string;
  targetLanguage: string;
  status: string;
  sourceScriptText: string;
  translatedScriptText: string;
  artifacts: {
    translatedScript: { checksum: string };
    subtitles: { checksum: string };
    voiceManifest: { checksum: string };
  };
  translationProvider: { provider: string; providerMode: string };
  voice: { provider: string; providerMode: string };
  trace: {
    sourceContextRefCount: number;
    sourceCitationCount: number;
    sourceContextRefIds: string[];
    sourceCitationIndexes: number[];
    sourceClaimSupportIds: string[];
    sourceEvaluationId: string;
    sourceEvaluationChecksum: string;
    evaluationStatus: string;
  };
};

type ConsentResponse = {
  consentRecordId: string;
  sourceRunId: string;
  sourceContextRefIds: string[];
  sourceCitationIndexes: number[];
  sourceEvaluationId: string;
  sourceEvaluationChecksum: string;
  evaluationStatus: string;
  consentStatementVersion: string;
};

type RenderResponse = {
  sourceRunId: string;
  status: string;
  renderJobStatus: string;
  sourceScriptText: string;
  avatarProvider: { provider: string; providerMode: string };
  providerConfig: {
    provider: string;
    providerMode: string;
    adapterKind: string;
    allowNetworkEgress: boolean;
    requiresApiKey: boolean;
    supportsRealVideo: boolean;
    supportsClonedIdentity: boolean;
  };
  disclosure: {
    consentStatus: string;
    clonedIdentity: boolean;
    message: string;
  };
  trace: {
    sourceContextRefCount: number;
    sourceCitationCount: number;
    sourceContextRefIds: string[];
    sourceCitationIndexes: number[];
    sourceEvaluationId: string;
    sourceEvaluationChecksum: string;
    evaluationStatus: string;
    multilingualRunId: string;
    targetLanguage: string;
    translatedScriptChecksum: string;
    subtitlesChecksum: string;
    voiceManifestChecksum: string;
  };
};

export class GuideWorkflowError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "GuideWorkflowError";
    this.code = code;
  }
}

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";

export async function runQuietPresenceDemo(
  input: GuideDemoInput,
  fetcher: Fetcher = fetch,
): Promise<GuideDemoResult> {
  const requestKey = workflowKey(input);
  const project = await postJson<{ projectId: string }>(
    fetcher,
    "/projects",
    {
      name: input.projectName,
      description: "Embedded grounded project guide",
      defaultAudience: input.audience,
      defaultLanguage: "en",
    },
    `${requestKey}-project`,
  );
  requireText(project.projectId, "PROJECT_INVALID");

  const upload = new FormData();
  upload.append(
    "file",
    new Blob([input.knowledgeDocument], { type: "text/markdown" }),
    "northwind-release.md",
  );
  const document = await requestJson<{ documentId: string }>(fetcher, 
    `/projects/${project.projectId}/knowledge-documents`,
    {
      method: "POST",
      headers: { "Idempotency-Key": `${requestKey}-upload` },
      body: upload,
    },
  );
  requireText(document.documentId, "DOCUMENT_INVALID");

  await requestJson(
    fetcher,
    `/projects/${project.projectId}/knowledge-documents/${document.documentId}/approval`,
    {
      method: "PATCH",
      headers: jsonHeaders(`${requestKey}-approval`),
      body: JSON.stringify({ approvalStatus: "APPROVED", reviewNote: "Approved local demo source." }),
    },
  );

  await postJson(
    fetcher,
    `/projects/${project.projectId}/ingestion-runs`,
    { documentIds: [document.documentId] },
    `${requestKey}-ingest`,
  );

  const walkthrough = await postJson<WalkthroughResponse>(
    fetcher,
    `/projects/${project.projectId}/walkthrough-runs`,
    {
      audience: input.audience,
      requestedLanguage: "en",
      depth: input.depth,
      style: "CONFIDENT",
      prompt: "Explain why deployment is blocked using only approved project evidence.",
    },
    `${requestKey}-walkthrough`,
  );
  validateWalkthrough(walkthrough);

  const multilingual = await postJson<MultilingualResponse>(
    fetcher,
    `/projects/${project.projectId}/walkthrough-runs/${walkthrough.runId}/multilingual-runs`,
    {
      targetLanguage: input.targetLanguage,
      glossaryTerms: input.glossaryTerms,
      requestedVoiceProvider: "mock",
    },
    `${requestKey}-multilingual`,
  );
  validateMultilingual(multilingual, walkthrough, input.targetLanguage);

  const consent = await postJson<ConsentResponse>(
    fetcher,
    `/projects/${project.projectId}/walkthrough-runs/${walkthrough.runId}/avatar-consents`,
    { consentToUseSyntheticAvatar: true },
    `${requestKey}-consent`,
  );
  validateConsent(consent, walkthrough, multilingual);

  const render = await postJson<RenderResponse>(
    fetcher,
    `/projects/${project.projectId}/walkthrough-runs/${walkthrough.runId}/avatar-renders`,
    {
      requestedAvatarProvider: "mock",
      consentToUseSyntheticAvatar: true,
      consentRecordId: consent.consentRecordId,
      clonedIdentityRequested: false,
      multilingualBundle: buildMultilingualBundle(multilingual, consent),
    },
    `${requestKey}-render`,
  );
  validateRender(render, walkthrough, multilingual, consent);

  const evaluation = walkthrough.evaluation!;
  const supports = new Map(evaluation.claimSupports.map((support) => [support.contextRefId, support]));
  return {
    explanation: walkthrough.acceptedScriptText!,
    translatedExplanation: multilingual.translatedScriptText,
    targetLanguage: multilingual.targetLanguage,
    sources: walkthrough.contextRefs.map((context) => ({
      citationIndex: supports.get(context.contextRefId)!.citationIndex,
      filename: context.sourceFilename,
      excerpt: context.evidenceSnapshot.redactedExcerpt,
      contextRefId: context.contextRefId,
    })),
    evaluation: {
      status: evaluation.evaluationStatus,
      unsupportedClaimCount: evaluation.unsupportedClaimCount,
    },
    providerPosture: {
      avatar: render.avatarProvider.provider,
      avatarMode: render.avatarProvider.providerMode,
      translation: multilingual.translationProvider.provider,
      translationMode: multilingual.translationProvider.providerMode,
      voice: multilingual.voice.provider,
      voiceMode: multilingual.voice.providerMode,
      networkEgress: render.providerConfig.allowNetworkEgress,
      realMedia: render.providerConfig.supportsRealVideo,
      clonedIdentity: render.disclosure.clonedIdentity,
      consent: "CONFIRMED",
    },
    traceId: walkthrough.trace?.traceId ?? "not-exposed",
    runId: walkthrough.runId,
  };
}

function buildMultilingualBundle(multilingual: MultilingualResponse, consent: ConsentResponse) {
  return {
    sourceRunId: multilingual.sourceRunId,
    multilingualRunId: multilingual.multilingualRunId,
    targetLanguage: multilingual.targetLanguage,
    translatedScriptChecksum: multilingual.artifacts.translatedScript.checksum,
    subtitlesChecksum: multilingual.artifacts.subtitles.checksum,
    voiceManifestChecksum: multilingual.artifacts.voiceManifest.checksum,
    contextRefIds: multilingual.trace.sourceContextRefIds,
    citationIndexes: multilingual.trace.sourceCitationIndexes,
    evaluationId: multilingual.trace.sourceEvaluationId,
    evaluationChecksum: multilingual.trace.sourceEvaluationChecksum,
    providerPosture: {
      translationProvider: multilingual.translationProvider.provider,
      translationProviderMode: multilingual.translationProvider.providerMode,
      voiceProvider: multilingual.voice.provider,
      voiceProviderMode: multilingual.voice.providerMode,
    },
    consentDisclosureVersion: consent.consentStatementVersion,
  };
}

function validateWalkthrough(value: WalkthroughResponse) {
  const evaluation = value.evaluation;
  if (
    value.status !== "COMPLETED" ||
    !value.acceptedScriptText ||
    value.contextRefs.length === 0 ||
    evaluation?.evaluationStatus !== "PASSED" ||
    !Number.isInteger(evaluation.unsupportedClaimCount) ||
    evaluation.unsupportedClaimCount !== 0 ||
    evaluation.claimSupports.length !== value.contextRefs.length
  ) {
    throw new GuideWorkflowError(
      "GROUNDING_REFUSED",
      "NarraTwin could not ground this explanation in the approved local project evidence.",
    );
  }
  const contextIds = new Set<string>();
  const supportIds = new Set<string>();
  const citations = new Set<number>();
  for (const context of value.contextRefs) {
    requireText(context.contextRefId, "GROUNDING_REFUSED");
    requireText(context.chunkId, "GROUNDING_REFUSED");
    requireText(context.documentId, "GROUNDING_REFUSED");
    requireText(context.sourceFilename, "GROUNDING_REFUSED");
    requireText(context.evidenceSnapshot?.redactedExcerpt, "GROUNDING_REFUSED", 4_000);
    if (contextIds.has(context.contextRefId)) invalidGrounding();
    contextIds.add(context.contextRefId);
    const support = evaluation.claimSupports.find((item) => item.contextRefId === context.contextRefId);
    if (
      !support || support.chunkId !== context.chunkId || support.documentId !== context.documentId ||
      !Number.isInteger(support.citationIndex) || support.citationIndex < 1 ||
      supportIds.has(support.claimSupportId) || citations.has(support.citationIndex)
    ) invalidGrounding();
    requireText(support.claimSupportId, "GROUNDING_REFUSED");
    supportIds.add(support.claimSupportId);
    citations.add(support.citationIndex);
  }
}

function validateMultilingual(value: MultilingualResponse, walkthrough: WalkthroughResponse, targetLanguage: string) {
  const evaluation = walkthrough.evaluation!;
  const contextIds = walkthrough.contextRefs.map((context) => context.contextRefId);
  const citationIndexes = evaluation.claimSupports.map((support) => support.citationIndex);
  const supportIds = evaluation.claimSupports.map((support) => support.claimSupportId);
  if (
    value.status !== "COMPLETED" ||
    value.sourceRunId !== walkthrough.runId ||
    value.targetLanguage !== targetLanguage ||
    value.sourceScriptText !== walkthrough.acceptedScriptText ||
    !value.translatedScriptText ||
    value.trace.sourceEvaluationId !== evaluation.evaluationId ||
    value.trace.evaluationStatus !== "PASSED" ||
    value.trace.sourceContextRefCount !== contextIds.length ||
    value.trace.sourceCitationCount !== citationIndexes.length ||
    !arraysEqual(value.trace.sourceContextRefIds, contextIds) ||
    !arraysEqual(value.trace.sourceCitationIndexes, citationIndexes) ||
    !arraysEqual(value.trace.sourceClaimSupportIds, supportIds) ||
    !isChecksum(value.trace.sourceEvaluationChecksum) ||
    !approvedLocalProvider(value.translationProvider, ["mock", "local-rule-based"]) ||
    !approvedLocalProvider(value.voice, ["mock"])
  ) {
    throw new GuideWorkflowError(
      "MULTILINGUAL_INVALID",
      "NarraTwin stopped before presentation because the translated result did not match the grounded run.",
    );
  }
}

function validateConsent(
  value: ConsentResponse,
  walkthrough: WalkthroughResponse,
  multilingual: MultilingualResponse,
) {
  const evaluation = walkthrough.evaluation!;
  if (
    !value.consentRecordId || value.sourceRunId !== walkthrough.runId ||
    value.sourceEvaluationId !== evaluation.evaluationId || value.evaluationStatus !== "PASSED" ||
    value.sourceEvaluationChecksum !== multilingual.trace.sourceEvaluationChecksum ||
    !arraysEqual(value.sourceContextRefIds, multilingual.trace.sourceContextRefIds) ||
    !arraysEqual(value.sourceCitationIndexes, multilingual.trace.sourceCitationIndexes) ||
    value.consentStatementVersion !== "stage7-synthetic-avatar-consent-v1"
  ) {
    throw new GuideWorkflowError(
      "CONSENT_INVALID",
      "NarraTwin stopped because consent did not match the verified project source.",
    );
  }
}

function validateRender(
  value: RenderResponse,
  walkthrough: WalkthroughResponse,
  multilingual: MultilingualResponse,
  consent: ConsentResponse,
) {
  const trace = value.trace;
  if (
    value.status !== "COMPLETED" || value.renderJobStatus !== "COMPLETED" ||
    value.sourceRunId !== walkthrough.runId || value.sourceScriptText !== multilingual.translatedScriptText ||
    !approvedLocalProvider(value.avatarProvider, ["mock"]) ||
    value.providerConfig?.provider !== value.avatarProvider.provider ||
    value.providerConfig?.providerMode !== "LOCAL" ||
    value.providerConfig.adapterKind !== "MOCK_LOCAL" ||
    value.providerConfig.allowNetworkEgress ||
    value.providerConfig.requiresApiKey ||
    value.providerConfig.supportsRealVideo ||
    value.providerConfig.supportsClonedIdentity ||
    value.disclosure?.consentStatus !== "CONFIRMED" ||
    value.disclosure?.clonedIdentity
    || !trace || trace.sourceContextRefCount !== multilingual.trace.sourceContextRefCount
    || trace.sourceCitationCount !== multilingual.trace.sourceCitationCount
    || !arraysEqual(trace.sourceContextRefIds, multilingual.trace.sourceContextRefIds)
    || !arraysEqual(trace.sourceCitationIndexes, multilingual.trace.sourceCitationIndexes)
    || trace.sourceEvaluationId !== multilingual.trace.sourceEvaluationId
    || trace.sourceEvaluationChecksum !== multilingual.trace.sourceEvaluationChecksum
    || trace.evaluationStatus !== "PASSED"
    || trace.multilingualRunId !== multilingual.multilingualRunId
    || trace.targetLanguage !== multilingual.targetLanguage
    || trace.translatedScriptChecksum !== multilingual.artifacts.translatedScript.checksum
    || trace.subtitlesChecksum !== multilingual.artifacts.subtitles.checksum
    || trace.voiceManifestChecksum !== multilingual.artifacts.voiceManifest.checksum
    || consent.sourceEvaluationChecksum !== trace.sourceEvaluationChecksum
  ) {
    throw new GuideWorkflowError(
      "PRESENTER_BOUNDARY_INVALID",
      "NarraTwin stopped because the presenter result exceeded the local synthetic-media boundary.",
    );
  }
}

function invalidGrounding(): never {
  throw new GuideWorkflowError(
    "GROUNDING_REFUSED",
    "NarraTwin could not ground this explanation in the approved local project evidence.",
  );
}

function approvedLocalProvider(
  value: { provider?: unknown; providerMode?: unknown } | undefined,
  providers: string[],
) {
  return value?.providerMode === "LOCAL" && typeof value.provider === "string" && providers.includes(value.provider);
}

function arraysEqual<T>(value: unknown, expected: T[]) {
  return Array.isArray(value) && value.length === expected.length && value.every((item, index) => item === expected[index]);
}

function isChecksum(value: unknown) {
  return typeof value === "string" && /^sha256:[0-9a-z]+$/i.test(value);
}

async function postJson<T>(
  fetcher: Fetcher,
  path: string,
  body: object,
  idempotencyKey: string,
) {
  return requestJson<T>(fetcher, path, {
    method: "POST",
    headers: jsonHeaders(idempotencyKey),
    body: JSON.stringify(body),
  });
}

async function requestJson<T>(fetcher: Fetcher, path: string, init: RequestInit) {
  let response: Response;
  try {
    response = await fetcher(`${apiBase}${path}`, init);
  } catch {
    throw new GuideWorkflowError(
      "REQUEST_FAILED",
      "The local NarraTwin demo could not complete safely. Check that the local API is running and try again.",
    );
  }
  if (!response.ok) {
    throw new GuideWorkflowError(
      "REQUEST_FAILED",
      "The local NarraTwin demo could not complete safely. Check the approved sample and try again.",
    );
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new GuideWorkflowError(
      "RESPONSE_INVALID",
      "NarraTwin stopped because the local API returned an invalid response.",
    );
  }
}

function jsonHeaders(idempotencyKey: string) {
  return {
    "Content-Type": "application/json",
    "Idempotency-Key": idempotencyKey,
  };
}

function requireText(value: unknown, code: string, maxLength = 160): asserts value is string {
  if (typeof value !== "string" || value.length === 0 || value.length > maxLength) {
    throw new GuideWorkflowError(code, "NarraTwin stopped because required local evidence was missing.");
  }
}

function workflowKey(input: GuideDemoInput) {
  const source = JSON.stringify(input);
  let hash = 2166136261;
  for (let index = 0; index < source.length; index += 1) {
    hash ^= source.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `quiet-presence-${(hash >>> 0).toString(16).padStart(8, "0")}`;
}
