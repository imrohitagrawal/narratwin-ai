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
    translation: string;
    voice: string;
    networkEgress: boolean;
    realMedia: boolean;
    clonedIdentity: boolean;
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
    claimSupports: Array<{ contextRefId: string; citationIndex: number }>;
  };
  trace?: { traceId?: string };
};

type MultilingualResponse = {
  multilingualRunId: string;
  sourceRunId: string;
  targetLanguage: string;
  translatedScriptText: string;
  artifacts: {
    translatedScript: { checksum: string };
    subtitles: { checksum: string };
    voiceManifest: { checksum: string };
  };
  translationProvider: { provider: string; providerMode: string };
  voice: { provider: string; providerMode: string };
  trace: {
    sourceContextRefIds: string[];
    sourceCitationIndexes: number[];
    sourceEvaluationId: string;
    sourceEvaluationChecksum: string;
  };
};

type ConsentResponse = {
  consentRecordId: string;
  consentStatementVersion: string;
};

type RenderResponse = {
  sourceScriptText?: string;
  avatarProvider: { provider: string; providerMode: string };
  providerConfig: {
    providerMode: string;
    allowNetworkEgress: boolean;
    supportsRealVideo: boolean;
  };
  disclosure: {
    consentStatus: string;
    clonedIdentity: boolean;
    message: string;
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
  validateMultilingual(multilingual, walkthrough);

  const consent = await postJson<ConsentResponse>(
    fetcher,
    `/projects/${project.projectId}/walkthrough-runs/${walkthrough.runId}/avatar-consents`,
    { consentToUseSyntheticAvatar: true },
    `${requestKey}-consent`,
  );
  requireText(consent.consentRecordId, "CONSENT_INVALID");

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
  validateRender(render);

  const supports = new Map(
    walkthrough.evaluation?.claimSupports.map((support) => [support.contextRefId, support]) ?? [],
  );
  return {
    explanation: render.sourceScriptText ?? walkthrough.acceptedScriptText ?? "",
    translatedExplanation: multilingual.translatedScriptText,
    targetLanguage: multilingual.targetLanguage,
    sources: walkthrough.contextRefs.map((context, index) => ({
      citationIndex: supports.get(context.contextRefId)?.citationIndex ?? index + 1,
      filename: context.sourceFilename,
      excerpt: context.evidenceSnapshot.redactedExcerpt,
      contextRefId: context.contextRefId,
    })),
    evaluation: {
      status: walkthrough.evaluation?.evaluationStatus ?? "UNKNOWN",
      unsupportedClaimCount: walkthrough.evaluation?.unsupportedClaimCount ?? 0,
    },
    providerPosture: {
      avatar: render.avatarProvider.provider,
      translation: multilingual.translationProvider.provider,
      voice: multilingual.voice.provider,
      networkEgress: render.providerConfig.allowNetworkEgress,
      realMedia: render.providerConfig.supportsRealVideo,
      clonedIdentity: render.disclosure.clonedIdentity,
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
  if (
    value.status !== "COMPLETED" ||
    !value.acceptedScriptText ||
    value.contextRefs.length === 0 ||
    value.evaluation?.evaluationStatus !== "PASSED"
  ) {
    throw new GuideWorkflowError(
      "GROUNDING_REFUSED",
      "NarraTwin could not ground this explanation in the approved local project evidence.",
    );
  }
}

function validateMultilingual(value: MultilingualResponse, walkthrough: WalkthroughResponse) {
  if (
    value.sourceRunId !== walkthrough.runId ||
    !value.translatedScriptText ||
    value.trace.sourceEvaluationId !== walkthrough.evaluation?.evaluationId
  ) {
    throw new GuideWorkflowError(
      "MULTILINGUAL_INVALID",
      "NarraTwin stopped before presentation because the translated result did not match the grounded run.",
    );
  }
}

function validateRender(value: RenderResponse) {
  if (
    value.avatarProvider?.providerMode !== "LOCAL" ||
    value.providerConfig?.providerMode !== "LOCAL" ||
    value.providerConfig.allowNetworkEgress ||
    value.disclosure?.clonedIdentity
  ) {
    throw new GuideWorkflowError(
      "PRESENTER_BOUNDARY_INVALID",
      "NarraTwin stopped because the presenter result exceeded the local synthetic-media boundary.",
    );
  }
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

function requireText(value: unknown, code: string): asserts value is string {
  if (typeof value !== "string" || value.length === 0 || value.length > 160) {
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
