"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import styles from "./page.module.css";

type ClaimSupport = {
  claimId: string;
  contextRefId: string;
  citationIndex: number;
  documentId?: string;
  chunkId?: string;
  evidenceSnapshot?: { chunkChecksum: string };
};

type ContextRef = {
  contextRefId: string;
  sourceFilename: string;
  chunkId: string;
  documentId?: string;
  claimId?: string;
  evidenceSnapshot: {
    redactedExcerpt: string;
    sourceDocumentChecksum?: string;
    chunkChecksum?: string;
  };
};

type WalkthroughRun = {
  runId: string;
  status: string;
  acceptedScriptText?: string;
  evaluation?: {
    evaluationId?: string;
    evaluationStatus?: string;
    unsupportedClaimCount: number;
    claimSupports: ClaimSupport[];
  };
  failure?: {
    reasonCode?: string;
    message?: string;
    unsupportedClaimCount?: number;
  };
  contextRefs: ContextRef[];
  trace: {
    traceId: string;
  };
};

type DownloadableArtifact = {
  fileName: string;
  mimeType: string;
  contentBase64: string;
  checksum: string;
};

type MultilingualWalkthrough = {
  multilingualRunId: string;
  status: string;
  sourceRunId: string;
  sourceLanguage: string;
  targetLanguage: string;
  translatedScriptText: string;
  subtitlesText: string;
  transcriptSegments: TranscriptSegment[];
  transcriptCorrectness: {
    validationStatus: "PASSED";
    script: string;
    direction: "ltr" | "rtl";
    segmentCount: number;
    citationIndexes: number[];
  };
  preservedTerms: string[];
  voice: {
    provider: string;
    providerMode: string;
    requestedProvider: string;
    fallbackReason?: string;
  };
  translationProvider: {
    provider: string;
    providerMode: string;
  };
  artifacts: {
    translatedScript: DownloadableArtifact;
    subtitles: DownloadableArtifact;
    voiceManifest: DownloadableArtifact;
    metadata: DownloadableArtifact;
  };
  trace: {
    sourceContextRefIds: string[];
    sourceCitationIndexes: number[];
    sourceEvaluationId: string;
    sourceEvaluationChecksum: string;
  };
};

type TranscriptSegment = {
  segmentId: string;
  sourceText: string;
  targetLanguage: string;
  targetText: string;
  englishReferenceText: string;
  citationMarkers: string[];
  citationIndexes: number[];
  contextRefIds: string[];
  claimSupportIds: string[];
  sourceRunId: string;
  evaluationId: string;
};

type LanguageCatalogRecord = {
  languageTag: string;
  englishName: string;
  nativeName: string;
  script: string;
  direction: "ltr" | "rtl";
  marketPriority: 1 | 2;
  regionGroup: string;
  localDemoSupportStatus: "SUPPORTED" | "PLANNED_UNSUPPORTED_LOCAL_DEMO";
  providerSupportStatus: "LOCAL_DEMO_FIXTURE" | "UNSUPPORTED_LOCAL_DEMO";
  testCoverageLevel: "CHECKPOINT3A_EXHAUSTIVE" | "CATALOG_ONLY";
};

type LanguageCatalogResponse = {
  languages: LanguageCatalogRecord[];
};

type AvatarConsent = {
  consentRecordId: string;
  consentStatementVersion: string;
  consentStatementText: string;
  requestChecksum: string;
};

type AvatarRender = {
  avatarRenderId: string;
  consentRecordId: string;
  sourceRunId: string;
  status: string;
  renderJobStatus: string;
  renderJobStatusHistory: Array<{
    status: string;
    message: string;
  }>;
  sourceScriptText: string;
  avatarProvider: {
    provider: string;
    providerMode: string;
    requestedProvider: string;
    fallbackReason?: string;
  };
  providerConfig: {
    provider: string;
    providerMode: string;
    adapterKind: string;
    allowNetworkEgress: boolean;
    requiresApiKey: boolean;
    supportsRealVideo: boolean;
    supportsClonedIdentity: boolean;
  };
  videoRenderer: {
    renderer: string;
    exportFormat: string;
  };
  disclosure: {
    aiGenerated: boolean;
    clonedIdentity: boolean;
    consentStatus: string;
    message: string;
  };
  artifacts: {
    demoExport: DownloadableArtifact;
    renderManifest: DownloadableArtifact;
    videoExportPlaceholder: DownloadableArtifact;
  };
	  trace: {
	    traceId: string;
	    sourceCitationCount: number;
	    sourceContextRefIds: string[];
	    sourceCitationIndexes: number[];
	    sourceEvaluationId: string;
	    sourceEvaluationChecksum: string;
	    evaluationStatus: string;
	    multilingualRunId: string | null;
	    targetLanguage: string | null;
	    translatedScriptChecksum: string | null;
	    subtitlesChecksum: string | null;
	    voiceManifestChecksum: string | null;
	  };
	};

type ProjectResponse = {
  projectId: string;
};

type H1Outcome = {
  code: string; sourceId: string; decisionId: string; checksum: string; sourceVersion: string;
  assertionsFingerprint: string; policyVersion: string; decisionState: string; ingestionStatus?: string;
  rawContentRetained: boolean; reason?: string;
};
type H1SummaryItem = H1Outcome & { acceptedChunks: Array<{ chunkId: string; checksum: string }> };
type H1Summary = {
  projectId: string; ownerId: string; curatedSources: H1SummaryItem[];
  excludedDecisions: H1Outcome[]; legacySources: unknown[];
};

type DocumentResponse = {
  documentId: string;
};

type ApiErrorPayload = {
  error?: {
    code?: unknown;
    message?: unknown;
  };
};

type Issue280Depth = "CONCISE" | "STANDARD" | "DEEP";

type Issue280TranscriptSegment = {
  segmentId: string;
  sourceText: string;
  targetText: string;
  englishReferenceText: string;
  contextRefIds: string[];
  citationIndexes: number[];
  claimSupportIds: string[];
};

type Issue280ContextRef = {
  contextRefId: string;
  documentId: string;
  chunkId: string;
  sourceChecksum: string;
  factChecksum: string;
  sectionHeading: string;
  relevanceScore: number;
};

type Issue280ClaimSupport = {
  claimSupportId: string;
  claimText: string;
  supportStatus: "SUPPORTED";
  contextRefId: string;
  citationIndex: number;
};

type Issue280LocalDemoResponse = {
  status: "COMPLETED";
  accepted: boolean;
  request: {
    documentCount: number;
    audience: string;
    depth: Issue280Depth;
    targetLanguage: string;
    glossaryTermCount: number;
  };
  session: {
    sessionId: string;
    projectId: string;
    documentIds: string[];
    outputId: string;
    replayed: boolean;
  };
  retrieval: {
    strategy: string;
    contextRefs: Issue280ContextRef[];
  };
  generated: {
    acceptedScriptText: string;
    sourceLanguage: "en";
    generationMode: string;
  };
  multilingual: {
    sourceLanguage: "en";
    targetLanguage: string;
    direction: "ltr" | "rtl";
    translationMode: string;
    multilingualRunId: string;
    preservedGlossaryTerms: string[];
    segments: Issue280TranscriptSegment[];
  };
  evaluation: {
    evaluationId: string;
    evaluationChecksum: string;
    status: "PASSED";
    unsupportedClaimCount: number;
    claimSupports: Issue280ClaimSupport[];
  };
  storage: {
    stored: boolean;
    outputId: string;
    outputChecksum: string;
    metadataChecksum: string;
    artifactBundleChecksum: string;
    reportChecksum: string;
  };
  artifacts: {
    translatedScript: DownloadableArtifact;
    subtitles: DownloadableArtifact;
    transcriptMetadata: DownloadableArtifact;
    voiceManifest: DownloadableArtifact;
    avatarDemo: DownloadableArtifact;
    renderManifest: DownloadableArtifact;
    videoPlaceholder: DownloadableArtifact;
  };
  correctnessReport: {
    status: "PASSED";
    traceId: string;
    audience: string;
    depth: Issue280Depth;
    targetLanguage: string;
    direction: "ltr" | "rtl";
    segmentCount: number;
    evaluationId: string;
    evaluationChecksum: string;
    outputChecksum: string;
    metadataChecksum: string;
    artifactBundleChecksum: string;
    reportChecksum: string;
    checks: Record<string, string>;
  };
  providerPosture: {
    llm: "mock";
    translation: "mock";
    voice: "mock";
    avatar: "mock";
    videoRenderer: "local-html";
    networkEgress: boolean;
    paidProvidersEnabled: boolean;
    realProviderCalls: boolean;
    clonedIdentity: boolean;
    realMedia: boolean;
  };
  trace: {
    requestId: string;
    evidenceLevel: string;
    runtimeProviderMode: "LOCAL_MOCK_DISABLED_EXTERNAL";
  };
};

type Issue280ResultView = {
  projectName: string;
  document: {
    filename: string;
    contentType: string;
    sizeBytes: number;
    checksum: string;
  };
  glossaryTerms: string[];
  response: Issue280LocalDemoResponse;
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
const audienceOptions = [
  { value: "RECRUITER", label: "Recruiter", promptLabel: "recruiter" },
  { value: "HIRING_MANAGER", label: "Hiring manager", promptLabel: "hiring manager" },
  { value: "ENGINEER", label: "Engineer", promptLabel: "engineer" },
  { value: "PRODUCT_LEADER", label: "Product leader", promptLabel: "product leader" },
  { value: "CUSTOMER", label: "Customer", promptLabel: "customer" },
  { value: "BEGINNER", label: "Beginner", promptLabel: "beginner" },
  { value: "GLOBAL_VIEWER", label: "Global viewer", promptLabel: "global viewer" },
];
export const defaultKnowledge = `# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.

It supports recruiters, hiring managers, engineers, product leaders, customers, beginners, and global audiences with audience-aware explanations.

The local demo uses mock local LLM, translation, voice, and avatar adapters for deterministic review.

Every generated walkthrough claim must cite retrieved source chunks from approved knowledge.`;
const safeApiErrorCodes = new Set([
  "AVATAR_CONSENT_INVALID",
  "AVATAR_CONSENT_RECORD_REQUIRED",
  "AVATAR_CONSENT_REQUIRED",
  "CLONED_IDENTITY_DISABLED",
  "FORBIDDEN",
  "IDEMPOTENCY_CONFLICT",
  "IDEMPOTENCY_IN_PROGRESS",
  "IDEMPOTENCY_KEY_REQUIRED",
  "NOT_FOUND",
  "SOURCE_RUN_NOT_RENDERABLE",
  "SOURCE_RUN_NOT_TRANSLATABLE",
  "VALIDATION_ERROR",
  "DUPLICATE_JSON_KEY",
  "EVALUATION_NOT_PASSED",
  "HOSTED_DEMO_DISABLED",
  "IDEMPOTENCY_CONFLICT",
  "LOCAL_DEMO_TRANSLATION_UNSUPPORTED",
  "LOCAL_DEMO_LANGUAGE_UNSUPPORTED",
  "TRANSCRIPT_CORRECTNESS_FAILED",
  "UNSUPPORTED_LANGUAGE",
  "UNSAFE_DISPLAY_TEXT",
  "UNSAFE_URL",
  "ISSUE280_INPUT_TOO_LARGE",
  "ISSUE280_UNSUPPORTED_FILE_TYPE",
  "ISSUE280_TOO_MANY_DOCUMENTS",
  "ISSUE280_PROMPT_INJECTION_REJECTED",
  "ISSUE280_UNSAFE_OR_PRIVATE_INPUT_REJECTED",
  "ISSUE280_GLOSSARY_INVALID",
  "ISSUE280_TRANSLATION_REFUSED",
  "ISSUE280_INTERNAL_ERROR_SAFE",
]);

const unsafeApiErrorMessagePattern =
  /contentBase64|fake-invite-input|fake-session-input|idem_[A-Za-z0-9_.:-]*|session_[A-Za-z0-9_.:-]*|inviteSecret|sessionSecret|auth token|bearer token|cookie|raw prompt|raw script|provider payload/i;

const safeIssue280Defaults = {
  projectName: "Issue 280 PR E Synthetic Demo",
  markdown: `# Meridian Planner

Meridian Planner accepts bounded public-safe markdown from product teams.

The local demo extracts source-backed claims about release rituals, adoption signals, and evidence handoffs.

Unsupported claims are refused before the stored walkthrough is shown in the browser.

Local mock artifacts keep citations, context references, claim supports, and checksums aligned.`,
};

const issue280SupportedLanguageOptions = [
  { value: "en", label: "English / English" },
  { value: "hi", label: "Hindi / हिन्दी" },
  { value: "es", label: "Spanish / Español" },
  { value: "de", label: "German / Deutsch" },
  { value: "fr", label: "French / Français" },
  { value: "pt-BR", label: "Brazilian Portuguese / Português do Brasil" },
  { value: "it", label: "Italian / Italiano" },
  { value: "nl", label: "Dutch / Nederlands" },
  { value: "pl", label: "Polish / Polski" },
  { value: "uk", label: "Ukrainian / Українська" },
  { value: "ru", label: "Russian / Русский" },
  { value: "zh-Hans", label: "Chinese Simplified / 简体中文" },
  { value: "zh-Hant", label: "Chinese Traditional / 繁體中文" },
  { value: "ja", label: "Japanese / 日本語" },
  { value: "ko", label: "Korean / 한국어" },
  { value: "ar", label: "Arabic / العربية" },
  { value: "arz", label: "Egyptian Arabic / مصري" },
  { value: "he", label: "Hebrew / עברית" },
  { value: "fa", label: "Persian/Farsi / فارسی" },
  { value: "tr", label: "Turkish / Türkçe" },
  { value: "vi", label: "Vietnamese / Tiếng Việt" },
  { value: "id", label: "Indonesian / Bahasa Indonesia" },
  { value: "fil", label: "Filipino/Tagalog / Filipino" },
  { value: "th", label: "Thai / ไทย" },
  { value: "ms", label: "Malay / Bahasa Melayu" },
  { value: "bn", label: "Bengali / বাংলা - planned refusal" },
];

async function postJson<T>(path: string, body: object, idempotencyKey: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(body),
  });
  return readJson<T>(response);
}

export async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let payload: ApiErrorPayload = {};
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = {};
    }
    const code = typeof payload.error?.code === "string" ? payload.error.code : "";
    const message = typeof payload.error?.message === "string" ? payload.error.message : "";
    if (
      safeApiErrorCodes.has(code) &&
      message.length > 0 &&
      message.length <= 240 &&
      !unsafeApiErrorMessagePattern.test(message)
    ) {
      throw new Error(`${code}: ${message}`);
    }
    throw new Error(`NarraTwin API request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

async function h1Json<T>(path: string, principal: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Local-User-Id", principal);
  const response = await fetch(`${apiBase}${path}`, { ...init, headers });
  const payload = (await response.json()) as T & { error?: { code?: unknown } };
  if (!response.ok) {
    const code = typeof payload.error?.code === "string" && /^[A-Z0-9_]{1,64}$/.test(payload.error.code) ? payload.error.code : `HTTP_${response.status}`;
    throw new Error(code);
  }
  return payload;
}

function issue280SafeError(caught: unknown) {
  const message = caught instanceof Error ? caught.message : "Issue 280 local demo request failed.";
  if (unsafeApiErrorMessagePattern.test(message)) {
    return "Issue 280 refusal: NarraTwin API request failed safely. Try again with bounded public-safe synthetic markdown.";
  }
  return `Issue 280 refusal: ${message}. Try again with bounded public-safe synthetic markdown.`;
}

export function productSafeError(caught: unknown) {
  const message = caught instanceof Error ? caught.message : "Stage 7 API request failed.";
  if (unsafeApiErrorMessagePattern.test(message)) {
    return "NarraTwin API request failed safely. Try again with bounded public-safe project knowledge.";
  }
  if (message.startsWith("LOCAL_DEMO_TRANSLATION_UNSUPPORTED:")) {
    return (
      "Local demo translation is limited to controlled acceptance fixture scripts. " +
      "The grounded English script may still be available; arbitrary project-knowledge multilingual conversion is not proven in this PR."
    );
  }
  return message;
}

function visibleLoadingStateDelay() {
  return new Promise((resolve) => {
    window.setTimeout(resolve, 120);
  });
}

export function evaluationBadgeLabel(run: WalkthroughRun | null): string {
  if (!run?.evaluation) {
    return "Evaluation pending";
  }
  return `${run.evaluation.unsupportedClaimCount} unsupported claims`;
}

function infoControl(label: string, text: string) {
  return (
    <span className={styles.infoWrap}>
      <button className={styles.infoButton} type="button" aria-label={label}>
        ?
      </button>
      <span className={styles.tooltip} role="tooltip">
        {text}
      </span>
    </span>
  );
}

const safeWalkthroughFailureReasons = new Set([
  "LOW_RETRIEVAL_CONFIDENCE",
  "PROMPT_INJECTION_DETECTED",
  "UNSAFE_RETRIEVED_CONTEXT",
  "UNSUPPORTED_PROJECT_FACT",
]);
const AVATAR_PREVIEW_COLLAPSED_CHARACTER_LIMIT = 280;

export function walkthroughDemoBlockReason(run: WalkthroughRun): string {
  if (run.status === "COMPLETED" && run.acceptedScriptText && run.evaluation) {
    return "";
  }
  const reasonCode = run.failure?.reasonCode ?? "";
  const message = run.failure?.message ?? "";
  if (
    run.status === "REFUSED" &&
    safeWalkthroughFailureReasons.has(reasonCode) &&
    message.length > 0 &&
    message.length <= 240 &&
    !unsafeApiErrorMessagePattern.test(message)
  ) {
    return `Walkthrough refused: ${message}`;
  }
  return "Walkthrough could not continue because the grounded script was not accepted. Add approved project details that support the requested walkthrough and try again.";
}

export default function Home() {
  const [run, setRun] = useState<WalkthroughRun | null>(null);
  const [multilingualRun, setMultilingualRun] = useState<MultilingualWalkthrough | null>(null);
  const [avatarRender, setAvatarRender] = useState<AvatarRender | null>(null);
  const [syntheticAvatarConsent, setSyntheticAvatarConsent] = useState(false);
  const [avatarPreviewExpanded, setAvatarPreviewExpanded] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");
  const [languageCatalog, setLanguageCatalog] = useState<LanguageCatalogRecord[]>([]);
  const [targetLanguage, setTargetLanguage] = useState("es");
  const [issue280Result, setIssue280Result] = useState<Issue280ResultView | null>(null);
  const [issue280Error, setIssue280Error] = useState("");
  const [issue280IsRunning, setIssue280IsRunning] = useState(false);
  const [issue280TranscriptExpanded, setIssue280TranscriptExpanded] = useState(false);
  const [issue280AvatarBoundary, setIssue280AvatarBoundary] = useState(false);
  const [h1Principal, setH1Principal] = useState("curator_demo");
  const [h1ProjectId, setH1ProjectId] = useState("");
  const [h1Source, setH1Source] = useState<H1Outcome | null>(null);
  const [h1Exclusion, setH1Exclusion] = useState<H1Outcome | null>(null);
  const [h1Summary, setH1Summary] = useState<H1Summary | null>(null);
  const [h1Error, setH1Error] = useState("");
  const [h2Principal, setH2Principal] = useState("curator_demo");
  const [h2ProjectId, setH2ProjectId] = useState("");
  const [h2Source, setH2Source] = useState<H1Outcome | null>(null);
  const [h2Summary, setH2Summary] = useState<H1Summary | null>(null);
  const [h2Consent, setH2Consent] = useState<AvatarConsent | null>(null);
  const [h2Error, setH2Error] = useState("");

  useEffect(() => {
    let isActive = true;
    fetch(`${apiBase}/languages`, { headers: { "X-Local-User-Id": "curator_demo" } })
      .then((response) => readJson<LanguageCatalogResponse>(response))
      .then((catalog) => {
        if (isActive && Array.isArray(catalog.languages) && catalog.languages.length > 0) {
          setLanguageCatalog(catalog.languages);
        }
      })
      .catch(() => {
        if (isActive) {
          setError("Language catalog could not be loaded from the local API.");
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  async function generateWalkthrough(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const projectName = String(form.get("projectName") ?? "NarraTwin AI").trim();
    const knowledgeDocument = String(form.get("knowledgeDocument") ?? "").trim();
    const audience = String(form.get("audience") ?? "RECRUITER");
    const depth = String(form.get("depth") ?? "CONCISE");
    const selectedTargetLanguage = String(form.get("targetLanguage") ?? targetLanguage);
    const selectedLanguage = languageCatalog.find((language) => language.languageTag === selectedTargetLanguage);
    if (!selectedLanguage || selectedLanguage.localDemoSupportStatus !== "SUPPORTED") {
      setError("Selected language is cataloged as planned and unsupported in the local demo.");
      return;
    }
    const consentToUseSyntheticAvatar = syntheticAvatarConsent;
    const glossaryTerms = String(form.get("glossaryTerms") ?? "")
      .split("\n")
      .map((term) => term.trim())
      .filter(Boolean);
    const requestSeed = checksumSeed(projectName, knowledgeDocument, audience, depth, selectedTargetLanguage);
    const requestedVoiceProvider = "mock";
    const requestedAvatarProvider = "mock";
    const multilingualSeed = checksumSeed(
      requestSeed,
      requestedVoiceProvider,
      ...glossaryTerms.slice().sort((left, right) => left.localeCompare(right)),
    );
    const avatarConsentSeed = checksumSeed(
      requestSeed,
      requestedAvatarProvider,
      String(consentToUseSyntheticAvatar),
      "avatar-consent-v1",
    );

    setIsGenerating(true);
    setError("");
    setAvatarPreviewExpanded(false);

    try {
      const project = await postJson<ProjectResponse>(
        "/projects",
        {
          name: projectName,
          description: "Grounded walkthrough generator",
          defaultAudience: audience,
          defaultLanguage: "en",
        },
        `ui-project-${requestSeed}`,
      );

      const uploadBody = new FormData();
      uploadBody.append(
        "file",
        new Blob([knowledgeDocument], { type: "text/markdown" }),
        "stage4_project.md",
      );
      const uploadResponse = await fetch(
        `${apiBase}/projects/${project.projectId}/knowledge-documents`,
        {
          method: "POST",
          headers: { "Idempotency-Key": `ui-upload-${requestSeed}` },
          body: uploadBody,
        },
      );
      const document = await readJson<DocumentResponse>(uploadResponse);

      const approvalResponse = await fetch(
        `${apiBase}/projects/${project.projectId}/knowledge-documents/${document.documentId}/approval`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": `ui-approval-${requestSeed}`,
          },
          body: JSON.stringify({ approvalStatus: "APPROVED", reviewNote: "Approved from UI." }),
        },
      );
      await readJson<DocumentResponse>(approvalResponse);

      await postJson(
        `/projects/${project.projectId}/ingestion-runs`,
        { documentIds: [document.documentId] },
        `ui-ingest-${requestSeed}`,
      );

      const generated = await postJson<WalkthroughRun>(
        `/projects/${project.projectId}/walkthrough-runs`,
        {
          audience,
          requestedLanguage: "en",
          depth,
          style: "CONFIDENT",
          prompt: `Create a concise grounded walkthrough for a ${audiencePromptLabel(audience)}.`,
        },
        `ui-generate-${requestSeed}`,
      );
      setRun(generated);
      setMultilingualRun(null);
      setAvatarRender(null);

      const blockReason = walkthroughDemoBlockReason(generated);
      if (blockReason) {
        setError(blockReason);
        return;
      }

      const multilingual = await postJson<MultilingualWalkthrough>(
        `/projects/${project.projectId}/walkthrough-runs/${generated.runId}/multilingual-runs`,
        {
          targetLanguage: selectedTargetLanguage,
          glossaryTerms,
          requestedVoiceProvider,
        },
        `ui-multilingual-${multilingualSeed}`,
      );

      const avatarConsent = await postJson<AvatarConsent>(
        `/projects/${project.projectId}/walkthrough-runs/${generated.runId}/avatar-consents`,
        {
          consentToUseSyntheticAvatar,
        },
        `ui-avatar-consent-${avatarConsentSeed}`,
      );
      const avatarSeed = checksumSeed(
        requestSeed,
        requestedAvatarProvider,
        String(consentToUseSyntheticAvatar),
        avatarConsent.consentRecordId,
        "cloned-identity-false",
      );
      const avatar = await postJson<AvatarRender>(
        `/projects/${project.projectId}/walkthrough-runs/${generated.runId}/avatar-renders`,
        {
          requestedAvatarProvider,
          consentToUseSyntheticAvatar,
          consentRecordId: avatarConsent.consentRecordId,
          clonedIdentityRequested: false,
          multilingualBundle: buildStage7MultilingualBundle(multilingual, avatarConsent),
        },
        `ui-avatar-${avatarSeed}`,
      );

      setRun(generated);
      setMultilingualRun(multilingual);
      setAvatarRender(avatar);
    } catch (caught) {
      setRun(null);
      setMultilingualRun(null);
      setAvatarRender(null);
      setError(productSafeError(caught));
    } finally {
      setIsGenerating(false);
    }
  }

  async function runIssue280LocalDemo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const projectName = String(form.get("issue280ProjectName") ?? safeIssue280Defaults.projectName).trim();
    const markdown = String(form.get("issue280KnowledgeDocument") ?? "").trim();
    const contentType = String(form.get("issue280ContentType") ?? "text/markdown");
    const audience = String(form.get("issue280Audience") ?? "ENGINEER");
    const depth = String(form.get("issue280Depth") ?? "STANDARD") as Issue280Depth;
    const selectedTargetLanguage = String(form.get("issue280TargetLanguage") ?? "en");
    const glossaryTerms = String(form.get("issue280GlossaryTerms") ?? "")
      .split("\n")
      .map((term) => term.trim())
      .filter(Boolean);
    const request = {
      documents: [
        {
          filename: "issue280_synthetic_project.md",
          contentType,
          markdown,
        },
      ],
      audience,
      depth,
      targetLanguage: selectedTargetLanguage,
      glossaryTerms,
    };
    const requestSeed = checksumSeed(
      "issue280-pr-e",
      projectName,
      markdown,
      contentType,
      audience,
      depth,
      selectedTargetLanguage,
      ...glossaryTerms.slice().sort((left, right) => left.localeCompare(right)),
    );

    setIssue280IsRunning(true);
    setIssue280Error("");
    setIssue280TranscriptExpanded(false);

    try {
      await visibleLoadingStateDelay();
      const response = await postJson<Issue280LocalDemoResponse>(
        "/checkpoint3/issue280/local-e2e-demo",
        request,
        `ui-issue280-${requestSeed}`,
      );
      setIssue280Result({
        projectName,
        document: {
          filename: "issue280_synthetic_project.md",
          contentType,
          sizeBytes: new TextEncoder().encode(markdown).length,
          checksum: `sha256:${sha256Hex(markdown)}`,
        },
        glossaryTerms,
        response,
      });
    } catch (caught) {
      setIssue280Error(issue280SafeError(caught));
    } finally {
      setIssue280IsRunning(false);
    }
  }

  async function h1Run(action: () => Promise<void>) {
    setH1Error("");
    try { await action(); } catch (caught) { setH1Error(caught instanceof Error ? caught.message : "REQUEST_FAILED"); }
  }

  function h1Headers(key: string, json = false) {
    return { "Idempotency-Key": key, ...(json ? { "Content-Type": "application/json" } : {}) };
  }

  async function h1Create() {
    await h1Run(async () => {
      const project = await h1Json<ProjectResponse>("/projects", h1Principal, {
        method: "POST", headers: h1Headers("heartbeat1-project", true),
        body: JSON.stringify({ name: "Heartbeat 1 browser proof", description: "Local controlled curation proof" }),
      });
      setH1ProjectId(project.projectId);
    });
  }

  async function h1Submit(event: FormEvent<HTMLFormElement>, kind: "public" | "internal") {
    event.preventDefault();
    const form = event.currentTarget;
    await h1Run(async () => {
      const input = new FormData(form).get("file");
      if (!(input instanceof File) || !h1ProjectId) throw new Error("FILE_REQUIRED");
      const body = new FormData();
      body.append("file", input);
      const fields = kind === "public"
        ? ["ACCEPT_FOR_REVIEW", "PUBLIC_SAFE", "PROJECT_AUTHORED_SYNTHETIC", "PROJECT_OWNED", "ELIGIBLE", "LOCAL_TEST_REUSE_ALLOWED"]
        : ["EXCLUDE", "INTERNAL", "PROJECT_AUTHORED_SYNTHETIC", "PROJECT_OWNED", "INELIGIBLE", "INTERNAL_NO_REUSE"];
      for (const [name, value] of [["action", fields[0]], ["classification", fields[1]], ["provenance", fields[2]], ["rightsBasis", fields[3]], ["rightsStatus", fields[4]], ["usagePolicy", fields[5]], ["curationSchemaVersion", "source-curation-v1"], ["sourceVersion", `heartbeat1-${kind}-v1`]]) body.append(name, value);
      const outcome = await h1Json<H1Outcome>(`/projects/${h1ProjectId}/knowledge-documents`, h1Principal, {
        method: "POST", headers: h1Headers(`heartbeat1-${kind}-${h1ProjectId}`), body,
      });
      if (kind === "public") setH1Source(outcome); else setH1Exclusion(outcome);
    });
    form.reset();
  }

  async function h1Approve() {
    if (!h1Source) return;
    await h1Run(async () => setH1Source(await h1Json<H1Outcome>(`/projects/${h1ProjectId}/knowledge-documents/${h1Source.sourceId}/approval`, h1Principal, {
      method: "PATCH", headers: h1Headers(`heartbeat1-approve-${h1ProjectId}`, true),
      body: JSON.stringify({ approvalStatus: "APPROVED", action: "APPROVE", curationSchemaVersion: "source-curation-v1", sourceId: h1Source.sourceId, decisionId: h1Source.decisionId, policyVersion: h1Source.policyVersion, sourceVersion: h1Source.sourceVersion, checksum: h1Source.checksum, assertionsFingerprint: h1Source.assertionsFingerprint }),
    })));
  }

  async function h1Ingest() {
    if (!h1Source) return;
    await h1Run(async () => { await h1Json(`/projects/${h1ProjectId}/ingestion-runs`, h1Principal, {
      method: "POST", headers: h1Headers(`heartbeat1-ingest-${h1ProjectId}`, true), body: JSON.stringify({ documentIds: [], sourceIds: [h1Source.sourceId] }),
    }); await h1Reopen(); });
  }

  async function h1Reopen() {
    await h1Run(async () => setH1Summary(await h1Json<H1Summary>(`/projects/${h1ProjectId}/source-curation-summary`, h1Principal)));
  }

  function h1ChangePrincipal(value: string) {
    setH1Principal(value); setH1Source(null); setH1Exclusion(null); setH1Summary(null); setH1Error("");
  }

  async function h2Run(action: () => Promise<void>) {
    setH2Error("");
    try { await action(); } catch (caught) { setH2Error(caught instanceof Error ? caught.message : "REQUEST_FAILED"); }
  }

  async function h2Create() {
    await h2Run(async () => {
      const project = await h1Json<ProjectResponse>("/projects", h2Principal, { method: "POST", headers: h1Headers("heartbeat2-project", true), body: JSON.stringify({ name: "Heartbeat 2 reviewer demo", description: "Controlled synthetic curated walkthrough", defaultAudience: "RECRUITER", defaultLanguage: "en" }) });
      setH2ProjectId(project.projectId);
    });
  }

  async function h2Submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    await h2Run(async () => {
      const file = new FormData(form).get("file");
      if (!(file instanceof File) || !h2ProjectId) throw new Error("FILE_REQUIRED");
      const body = new FormData();
      for (const [name, value] of Object.entries({ action: "ACCEPT_FOR_REVIEW", classification: "PUBLIC_SAFE", provenance: "PROJECT_AUTHORED_SYNTHETIC", rightsBasis: "PROJECT_OWNED", rightsStatus: "ELIGIBLE", usagePolicy: "LOCAL_TEST_REUSE_ALLOWED", curationSchemaVersion: "source-curation-v1", sourceVersion: "heartbeat2-public-v1" })) body.append(name, value);
      body.append("file", file);
      setH2Source(await h1Json<H1Outcome>(`/projects/${h2ProjectId}/knowledge-documents`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-submit"), body }));
    });
    form.reset();
  }

  async function h2Approve() {
    if (!h2Source) return;
    await h2Run(async () => setH2Source(await h1Json<H1Outcome>(`/projects/${h2ProjectId}/knowledge-documents/${h2Source.sourceId}/approval`, h2Principal, { method: "PATCH", headers: h1Headers("heartbeat2-approve", true), body: JSON.stringify({ approvalStatus: "APPROVED", action: "APPROVE", curationSchemaVersion: "source-curation-v1", sourceId: h2Source.sourceId, decisionId: h2Source.decisionId, policyVersion: h2Source.policyVersion, sourceVersion: h2Source.sourceVersion, checksum: h2Source.checksum, assertionsFingerprint: h2Source.assertionsFingerprint }) })));
  }

  async function h2Reopen() {
    await h2Run(async () => setH2Summary(await h1Json<H1Summary>(`/projects/${h2ProjectId}/source-curation-summary`, h2Principal)));
  }

  async function h2Ingest() {
    if (!h2Source) return;
    await h2Run(async () => {
      await h1Json(`/projects/${h2ProjectId}/ingestion-runs`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-ingest", true), body: JSON.stringify({ documentIds: [], sourceIds: [h2Source.sourceId] }) });
      setH2Summary(await h1Json<H1Summary>(`/projects/${h2ProjectId}/source-curation-summary`, h2Principal));
    });
  }

  const h2WalkthroughBody = { audience: "RECRUITER", requestedLanguage: "en", depth: "CONCISE", style: "CONFIDENT", prompt: "Create the controlled synthetic grounded reviewer walkthrough." };
  const h2MediaBody = { targetLanguage: "es", glossaryTerms: [], requestedVoiceProvider: "mock" };
  const h2ConsentBody = { consentToUseSyntheticAvatar: true };

  async function h2Generate() {
    await h2Run(async () => {
      const generated = await h1Json<WalkthroughRun>(`/projects/${h2ProjectId}/walkthrough-runs`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-walkthrough", true), body: JSON.stringify(h2WalkthroughBody) });
      const multilingual = await h1Json<MultilingualWalkthrough>(`/projects/${h2ProjectId}/walkthrough-runs/${generated.runId}/multilingual-runs`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-multilingual", true), body: JSON.stringify(h2MediaBody) });
      const consent = await h1Json<AvatarConsent>(`/projects/${h2ProjectId}/walkthrough-runs/${generated.runId}/avatar-consents`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-consent", true), body: JSON.stringify(h2ConsentBody) });
      const avatar = await h1Json<AvatarRender>(`/projects/${h2ProjectId}/walkthrough-runs/${generated.runId}/avatar-renders`, h2Principal, { method: "POST", headers: h1Headers("heartbeat2-render", true), body: JSON.stringify({ requestedAvatarProvider: "mock", consentToUseSyntheticAvatar: true, consentRecordId: consent.consentRecordId, clonedIdentityRequested: false, multilingualBundle: buildStage7MultilingualBundle(multilingual, consent) }) });
      setRun(generated); setMultilingualRun(multilingual); setH2Consent(consent); setAvatarRender(avatar);
    });
  }

  async function h2Probe(operation: "walkthrough" | "multilingual" | "consent" | "render") {
    if (!run || !multilingualRun || !h2Consent) return;
    const requests = {
      walkthrough: [`/projects/${h2ProjectId}/walkthrough-runs`, h2WalkthroughBody, "heartbeat2-other-walkthrough"],
      multilingual: [`/projects/${h2ProjectId}/walkthrough-runs/${run.runId}/multilingual-runs`, h2MediaBody, "heartbeat2-other-multilingual"],
      consent: [`/projects/${h2ProjectId}/walkthrough-runs/${run.runId}/avatar-consents`, h2ConsentBody, "heartbeat2-other-consent"],
      render: [`/projects/${h2ProjectId}/walkthrough-runs/${run.runId}/avatar-renders`, { requestedAvatarProvider: "mock", consentToUseSyntheticAvatar: true, consentRecordId: h2Consent.consentRecordId, clonedIdentityRequested: false, multilingualBundle: buildStage7MultilingualBundle(multilingualRun, h2Consent) }, "heartbeat2-other-render"],
    } as const;
    const [path, body, key] = requests[operation];
    await h2Run(async () => { await h1Json(path, h2Principal, { method: "POST", headers: h1Headers(key, true), body: JSON.stringify(body) }); });
  }

  const supports = run?.evaluation?.claimSupports ?? [];
  const selectedLanguage = languageCatalog.find((language) => language.languageTag === targetLanguage);
  const previewScript =
    multilingualRun?.translatedScriptText ??
    run?.acceptedScriptText ??
    "Generate a grounded script to display cited output.";
  const avatarPreviewScript =
	    avatarRender?.sourceScriptText ?? run?.acceptedScriptText ?? "Generate a grounded script to display cited output.";
	  const artifactContext = { multilingualRun, avatarRender };
  const avatarPreviewCanExpand = avatarPreviewScript.length > AVATAR_PREVIEW_COLLAPSED_CHARACTER_LIMIT;
  const h2Accepted = h2Summary?.curatedSources[0];
  const h2Ready = h2Summary?.curatedSources.length === 1 && h2Accepted?.decisionState === "APPROVED" && h2Accepted.ingestionStatus === "SOURCE_INGESTED" && h2Accepted.acceptedChunks.length > 0;

  return (
    <main className={styles.page} aria-busy={isGenerating || issue280IsRunning}>
      <section className={styles.workspace} data-testid="h2-curation-panel" aria-labelledby="h2-title">
        <h2 id="h2-title">Heartbeat 2 curated reviewer demo</h2>
        <p>Synthetic local media only — no provider calls, cloned identity, or hosted-production claim.</p>
        <label className={styles.field}>Principal<select data-testid="h2-principal" value={h2Principal} onChange={(event) => { setH2Principal(event.currentTarget.value); setH2Error(""); }}><option>curator_demo</option><option>other_demo</option></select></label>
        <p data-testid="h2-project-id">{h2ProjectId}</p>
        <button type="button" data-testid="h2-create-project" onClick={h2Create} hidden={h2Principal !== "curator_demo"} disabled={Boolean(h2ProjectId)}>Create one project</button>
        <form hidden={h2Principal !== "curator_demo"} onSubmit={h2Submit}><label className={styles.field}>Controlled public-safe source<input name="file" type="file" accept=".md,text/markdown" data-testid="h2-public-file" /></label><button type="submit" data-testid="h2-submit-source" disabled={!h2ProjectId}>Submit for review</button></form>
        {h2Source ? <p data-testid="h2-source-state">{h2Source.decisionState} <span data-testid="h2-source-id">{h2Source.sourceId}</span> <span data-testid="h2-source-checksum">{h2Source.checksum}</span> <span data-testid="h2-source-version">{h2Source.sourceVersion}</span></p> : null}
        <div data-testid="h2-owner-actions" hidden={h2Principal !== "curator_demo"}>
          <button type="button" data-testid="h2-approve-source" onClick={h2Approve} disabled={!h2Source}>Approve source</button>
          <button type="button" data-testid="h2-ingest-source" onClick={h2Ingest} disabled={h2Source?.decisionState !== "APPROVED"}>Ingest source</button>
          <button type="button" data-testid="h2-generate-demo" onClick={h2Generate} disabled={!h2Ready}>Generate local reviewer demo</button>
        </div>
        <button type="button" data-testid="h2-reopen-project" onClick={h2Reopen} hidden={h2Principal !== "curator_demo" || !h2ProjectId}>Reopen curated project</button>
        <button type="button" data-testid="h2-other-walkthrough" onClick={() => h2Probe("walkthrough")} hidden>Probe walkthrough authorization</button>
        <button type="button" data-testid="h2-other-multilingual" onClick={() => h2Probe("multilingual")} hidden>Probe multilingual authorization</button>
        <button type="button" data-testid="h2-other-consent" onClick={() => h2Probe("consent")} hidden>Probe consent authorization</button>
        <button type="button" data-testid="h2-other-render" onClick={() => h2Probe("render")} hidden>Probe render authorization</button>
        {!h2Ready ? <p>One curated source must be approved and ingested before generation.</p> : null}
        {h2Error ? <p role="alert" data-testid="h2-safe-error">{h2Error}</p> : null}
        {h2Accepted ? <article data-testid="h2-accepted-source" data-identity={`${h2Accepted.sourceId}|${h2Accepted.checksum}|${h2Accepted.sourceVersion}`}><p>{h2Accepted.sourceId} {h2Accepted.checksum} {h2Accepted.sourceVersion} {h2Accepted.ingestionStatus}</p>{h2Accepted.acceptedChunks.map((chunk) => <span data-testid="h2-accepted-chunk" key={chunk.chunkId}>{chunk.chunkId}:{chunk.checksum}</span>)}</article> : null}
        {run ? <section data-testid="h2-walkthrough" data-run-id={run.runId}><p>{run.status} evaluation={run.evaluation?.evaluationStatus} unsupported={run.evaluation?.unsupportedClaimCount}</p>{run.contextRefs.map((context) => <p data-testid="h2-visible-citation" data-claim-id={context.claimId} data-context-ref-id={context.contextRefId} data-document-id={context.documentId} data-chunk-id={context.chunkId} data-source-checksum={context.evidenceSnapshot.sourceDocumentChecksum} data-chunk-checksum={context.evidenceSnapshot.chunkChecksum} key={context.contextRefId}>[{supports.find((support) => support.contextRefId === context.contextRefId)?.citationIndex}] {context.contextRefId} {context.chunkId}</p>)}</section> : null}
        {multilingualRun ? <section data-testid="h2-multilingual" data-run-id={multilingualRun.multilingualRunId}><p>{multilingualRun.status} {multilingualRun.targetLanguage} translation={multilingualRun.translationProvider.providerMode} voice={multilingualRun.voice.providerMode}</p>{[["translated", multilingualRun.artifacts.translatedScript], ["subtitles", multilingualRun.artifacts.subtitles], ["voice", multilingualRun.artifacts.voiceManifest]].map(([name, artifact]) => <p data-testid={`h2-artifact-${name}`} data-filename={(artifact as DownloadableArtifact).fileName} data-checksum={(artifact as DownloadableArtifact).checksum} key={name as string}>{(artifact as DownloadableArtifact).fileName} {(artifact as DownloadableArtifact).checksum}</p>)}</section> : null}
        {h2Consent ? <p data-testid="h2-consent">consent={h2Consent.consentRecordId} version={h2Consent.consentStatementVersion}</p> : null}
        {avatarRender ? <section data-testid="h2-render" data-render-id={avatarRender.avatarRenderId}><p>{avatarRender.status} renderer={avatarRender.videoRenderer.renderer} egress={String(avatarRender.providerConfig.allowNetworkEgress)} cloned={String(avatarRender.disclosure.clonedIdentity)}</p>{[["preview", avatarRender.artifacts.demoExport], ["renderManifest", avatarRender.artifacts.renderManifest], ["video", avatarRender.artifacts.videoExportPlaceholder]].map(([name, artifact]) => <p data-testid={`h2-artifact-${name}`} data-filename={(artifact as DownloadableArtifact).fileName} data-checksum={(artifact as DownloadableArtifact).checksum} key={name as string}>{(artifact as DownloadableArtifact).fileName} {(artifact as DownloadableArtifact).checksum}</p>)}</section> : null}
      </section>
      <section className={styles.workspace} data-testid="h1-curation-panel" aria-labelledby="h1-title">
        <h2 id="h1-title">Heartbeat 1 source curation</h2>
        <label className={styles.field}>Principal<select data-testid="h1-principal" value={h1Principal} onChange={(event) => h1ChangePrincipal(event.currentTarget.value)}><option>curator_demo</option><option>other_demo</option></select></label>
        <label className={styles.field}>Project ID<input data-testid="h1-project-id" value={h1ProjectId} onChange={(event) => setH1ProjectId(event.currentTarget.value)} /></label>
        <button type="button" data-testid="h1-create-project" onClick={h1Create} hidden={h1Principal !== "curator_demo"} disabled={Boolean(h1ProjectId)}>Create project</button>
        <form hidden={h1Principal !== "curator_demo"} onSubmit={(event) => h1Submit(event, "public")}><label className={styles.field}>Public source<input name="file" type="file" accept=".md,text/markdown" data-testid="h1-public-file" /></label><button type="submit" data-testid="h1-submit-public" disabled={!h1ProjectId}>Submit public source</button></form>
        <form hidden={h1Principal !== "curator_demo"} onSubmit={(event) => h1Submit(event, "internal")}><label className={styles.field}>Internal source<input name="file" type="file" accept=".md,text/markdown" data-testid="h1-internal-file" /></label><button type="submit" data-testid="h1-submit-internal" disabled={!h1ProjectId}>Exclude internal source</button></form>
        {h1Source ? <p data-testid="h1-public-status">{h1Source.code} <span data-testid="h1-public-source-id">{h1Source.sourceId}</span> <span data-testid="h1-public-checksum">{h1Source.checksum}</span> <span data-testid="h1-public-version">{h1Source.sourceVersion}</span></p> : null}
        {h1Exclusion ? <p data-testid="h1-exclusion-status">{h1Exclusion.code} {h1Exclusion.decisionState} retained={String(h1Exclusion.rawContentRetained)} <span data-testid="h1-exclusion-decision-id">{h1Exclusion.decisionId}</span> <span data-testid="h1-exclusion-checksum">{h1Exclusion.checksum}</span></p> : null}
        <div data-testid="h1-owner-actions" hidden={h1Principal !== "curator_demo" || !h1Source}><button type="button" data-testid="h1-approve-source" onClick={h1Approve}>Approve source</button><button type="button" data-testid="h1-ingest-source" onClick={h1Ingest}>Ingest source</button></div>
        <button type="button" data-testid="h1-reopen-project" onClick={h1Reopen} disabled={!h1ProjectId} hidden={h1Principal !== "curator_demo" && h1Error === "FORBIDDEN"}>Reopen project</button>
        {h1Error ? <p role="alert" data-testid="h1-safe-error">{h1Error}</p> : null}
        {h1Summary ? <section data-testid="h1-summary" aria-label="Heartbeat 1 metadata summary">
          {h1Summary.curatedSources.map((source) => <article data-testid="h1-curated-item" data-identity={`${source.sourceId}|${source.checksum}|${source.sourceVersion}`} key={source.sourceId}><span>{source.sourceId}</span> <span>{source.checksum}</span> <span>{source.sourceVersion}</span> {source.decisionState} {source.ingestionStatus} {source.acceptedChunks.map((chunk) => <span data-testid="h1-accepted-chunk" key={chunk.chunkId}>{chunk.chunkId}:{chunk.checksum}</span>)}</article>)}
          {h1Summary.excludedDecisions.map((decision) => <article data-testid="h1-excluded-item" data-identity={`${decision.decisionId}|${decision.checksum}`} key={decision.decisionId}>{decision.decisionId} {decision.checksum} {decision.decisionState} {decision.reason} retained={String(decision.rawContentRetained)}</article>)}
        </section> : null}
      </section>
      <section className={styles.workspace} aria-labelledby="workspace-title">
        <div className={styles.header}>
          <p className={styles.kicker}>NarraTwin AI</p>
          <h1 id="workspace-title">Avatar demo export</h1>
        </div>

        <form className={styles.form} aria-label="Project knowledge form" onSubmit={generateWalkthrough}>
          <label className={styles.field}>
            <span>Project name</span>
            <input name="projectName" defaultValue="NarraTwin AI" />
          </label>

          <label className={styles.field}>
            <span>Knowledge document</span>
            <textarea name="knowledgeDocument" defaultValue={defaultKnowledge} rows={8} />
          </label>

          <div className={styles.controls}>
            <label className={styles.field}>
              <span>Audience</span>
              <select name="audience" defaultValue="RECRUITER">
                {audienceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className={styles.field}>
              <span>Depth</span>
              <select name="depth" defaultValue="CONCISE">
                <option value="CONCISE">Concise</option>
                <option value="STANDARD">Standard</option>
                <option value="DEEP">Deep</option>
              </select>
            </label>
          </div>

          <div className={styles.controls}>
            <label className={styles.field}>
              <span>Target language</span>
              <select
                name="targetLanguage"
                value={targetLanguage}
                disabled={languageCatalog.length === 0}
                onChange={(event) => setTargetLanguage(event.currentTarget.value)}
              >
                {languageCatalog.map((language) => (
                  <option
                    key={language.languageTag}
                    value={language.languageTag}
                    disabled={language.localDemoSupportStatus !== "SUPPORTED"}
                  >
                    {languageOptionLabel(language)}
                  </option>
                ))}
              </select>
              <small className={styles.supportStatus}>
                {selectedLanguage
                  ? `${selectedLanguage.script}, ${selectedLanguage.direction.toUpperCase()}, ${
                      selectedLanguage.localDemoSupportStatus === "SUPPORTED" ? "Local demo supported" : "Planned"
                    }`
                  : "Language catalog unavailable"}
              </small>
            </label>

            <label className={styles.field}>
              <span>Glossary terms</span>
              <textarea
                name="glossaryTerms"
                defaultValue={"NarraTwin AI"}
                rows={4}
              />
            </label>
          </div>

          <p className={styles.localLimitNotice}>
            Local/demo multilingual output uses controlled acceptance fixtures. A bounded project can generate an
            English grounded script while arbitrary project-knowledge translation may safely refuse until a later
            implementation slice proves that behavior.
          </p>

          <label className={styles.checkboxField}>
            <input
              name="syntheticAvatarConsent"
              type="checkbox"
              checked={syntheticAvatarConsent}
              onChange={(event) => setSyntheticAvatarConsent(event.currentTarget.checked)}
            />
            <span>Synthetic avatar consent: local AI presenter, no cloned face or voice</span>
          </label>

          <button
            className={styles.primaryAction}
            type="submit"
            disabled={isGenerating || !syntheticAvatarConsent || languageCatalog.length === 0}
          >
            {isGenerating ? "Generating" : "Generate avatar demo export"}
          </button>
        </form>

        {error ? (
          <p className={styles.errorStatus} role="alert" aria-live="assertive">
            {error}
          </p>
        ) : null}

        <section className={styles.result} aria-labelledby="result-title">
          <div className={styles.resultHeader}>
            <h2 id="result-title">Walkthrough script</h2>
            <span className={styles.badge}>{multilingualRun?.status ?? run?.status ?? "READY"}</span>
          </div>
          {multilingualRun?.transcriptSegments?.length
            ? renderTranscriptSegments(multilingualRun.transcriptSegments, multilingualRun.transcriptCorrectness.direction)
            : <p>{previewScript}</p>}
          <div className={styles.artifactActions} aria-label="Downloadable artifacts">
	            {renderArtifactAction("Download script", "script", multilingualRun?.artifacts.translatedScript, artifactContext)}
	            {renderArtifactAction("Download subtitles", "subtitles", multilingualRun?.artifacts.subtitles, artifactContext)}
	            {renderArtifactAction(
	              "Download voice manifest",
	              "voiceManifest",
	              multilingualRun?.artifacts.voiceManifest,
	              artifactContext,
	            )}
	            {renderArtifactAction(
	              "Download transcript metadata",
	              "metadata",
	              multilingualRun?.artifacts.metadata,
	              artifactContext,
	            )}
	            {renderArtifactAction("Download avatar demo", "avatarDemo", avatarRender?.artifacts.demoExport, artifactContext)}
	            {renderArtifactAction(
	              "Download render manifest",
	              "renderManifest",
	              avatarRender?.artifacts.renderManifest,
	              artifactContext,
	            )}
	            {renderArtifactAction(
	              "Download video placeholder",
	              "videoPlaceholder",
	              avatarRender?.artifacts.videoExportPlaceholder,
	              artifactContext,
	            )}
          </div>
          <dl className={styles.metadata} aria-label="Trace metadata">
            <div>
              <dt>Trace</dt>
              <dd>{run?.trace.traceId ?? "pending"}</dd>
            </div>
            <div>
              <dt>Run</dt>
              <dd>{run?.runId ?? "pending"}</dd>
            </div>
            <div>
              <dt>Language</dt>
              <dd>{multilingualRun?.targetLanguage ?? "pending"}</dd>
            </div>
            <div>
              <dt>Voice</dt>
              <dd>{multilingualRun?.voice.provider ?? "pending"}</dd>
            </div>
            <div>
              <dt>Avatar</dt>
              <dd>{avatarRender?.avatarProvider.provider ?? "pending"}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.result} aria-labelledby="avatar-title">
          <div className={styles.resultHeader}>
            <h2 id="avatar-title">Avatar export</h2>
            <span className={styles.badge}>{avatarRender?.status ?? "READY"}</span>
          </div>
          <p>
            {avatarRender?.disclosure.message ??
              "Avatar export metadata and AI disclosure will appear after generation."}
          </p>
          <dl className={styles.metadata} aria-label="Avatar metadata">
            <div>
              <dt>Renderer</dt>
              <dd>{avatarRender?.videoRenderer.renderer ?? "pending"}</dd>
            </div>
            <div>
              <dt>Consent</dt>
              <dd>{avatarRender?.disclosure.consentStatus ?? "pending"}</dd>
            </div>
            <div>
              <dt>Cloned identity</dt>
              <dd>{avatarRender?.disclosure.clonedIdentity ? "enabled" : "disabled"}</dd>
            </div>
            <div>
              <dt>Evaluation</dt>
              <dd>{avatarRender?.trace.evaluationStatus ?? "pending"}</dd>
            </div>
            <div>
              <dt>Network</dt>
              <dd>{avatarRender?.providerConfig.allowNetworkEgress ? "enabled" : "disabled"}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.result} aria-labelledby="preview-title">
          <div className={styles.resultHeader}>
            <div className={styles.previewTitleGroup}>
              <h2 id="preview-title">Demo preview</h2>
              <div className={styles.previewHeaderActions} aria-label="Demo preview downloads">
                {renderArtifactAction(
                  "Save preview transcript",
                  "script",
                  multilingualRun?.artifacts.translatedScript,
                  artifactContext,
                )}
                {renderArtifactAction(
                  "Save preview avatar export",
                  "avatarDemo",
                  avatarRender?.artifacts.demoExport,
                  artifactContext,
                )}
              </div>
            </div>
            <span className={styles.badge}>{avatarRender?.renderJobStatus ?? "READY"}</span>
          </div>
          <div className={styles.previewFrame} aria-label="Avatar demo preview">
            <div className={styles.previewScreen}>
              <div className={styles.previewPresenter} aria-hidden="true">
                AI
              </div>
              <div className={styles.previewCopy}>
                <strong>{avatarRender?.videoRenderer.renderer ?? "local-html"}</strong>
                <p
                  id="avatar-preview-script"
                  className={avatarPreviewExpanded ? styles.previewCopyExpanded : styles.previewCopyCollapsed}
                >
                  {avatarPreviewScript}
                </p>
                {avatarPreviewCanExpand ? (
                  <button
                    className={styles.previewToggle}
                    type="button"
                    aria-controls="avatar-preview-script"
                    aria-expanded={avatarPreviewExpanded}
                    onClick={() => setAvatarPreviewExpanded(!avatarPreviewExpanded)}
                  >
                    {avatarPreviewExpanded ? "Collapse demo preview transcript" : "Expand full demo preview transcript"}
                  </button>
                ) : null}
              </div>
            </div>
          </div>
          <dl className={styles.metadata} aria-label="Render job lifecycle">
            <div>
              <dt>Status</dt>
              <dd>{avatarRender?.renderJobStatus ?? "pending"}</dd>
            </div>
            <div>
              <dt>Provider mode</dt>
              <dd>{avatarRender?.providerConfig.providerMode ?? "pending"}</dd>
            </div>
            <div>
              <dt>Adapter</dt>
              <dd>{avatarRender?.providerConfig.adapterKind ?? "pending"}</dd>
            </div>
            <div>
              <dt>Real video</dt>
              <dd>{avatarRender?.providerConfig.supportsRealVideo ? "enabled" : "placeholder"}</dd>
            </div>
          </dl>
        </section>

        <section className={styles.result} aria-labelledby="artifacts-title">
          <div className={styles.resultHeader}>
            <h2 id="artifacts-title">Export artifacts</h2>
            <span className={styles.badge}>{avatarRender ? "7 artifacts" : "READY"}</span>
          </div>
          <div className={styles.artifactList} aria-label="Export artifact list">
	            {renderArtifactRow("Translated script", "script", multilingualRun?.artifacts.translatedScript, artifactContext)}
	            {renderArtifactRow("Subtitles", "subtitles", multilingualRun?.artifacts.subtitles, artifactContext)}
	            {renderArtifactRow("Voice manifest", "voiceManifest", multilingualRun?.artifacts.voiceManifest, artifactContext)}
	            {renderArtifactRow("Transcript metadata", "metadata", multilingualRun?.artifacts.metadata, artifactContext)}
	            {renderArtifactRow("Avatar demo", "avatarDemo", avatarRender?.artifacts.demoExport, artifactContext)}
	            {renderArtifactRow("Render manifest", "renderManifest", avatarRender?.artifacts.renderManifest, artifactContext)}
	            {renderArtifactRow(
	              "Video placeholder",
	              "videoPlaceholder",
	              avatarRender?.artifacts.videoExportPlaceholder,
	              artifactContext,
	            )}
          </div>
        </section>

        <section className={styles.citations} aria-labelledby="citations-title">
          <div className={styles.resultHeader}>
            <h2 id="citations-title">Citations</h2>
            <span className={styles.badge}>{evaluationBadgeLabel(run)}</span>
          </div>
          {run ? (
            <ul>
              {run.contextRefs.map((citation) => {
                const support = supports.find(
                  (candidate) => candidate.contextRefId === citation.contextRefId,
                );
                return (
                  <li key={citation.contextRefId}>
                    <strong>[{support?.citationIndex}]</strong>
                    <span>{citation.sourceFilename}</span>
                    <code>{citation.chunkId}</code>
                    <p>{citation.evidenceSnapshot.redactedExcerpt}</p>
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className={styles.emptyState}>Citations will appear after generation.</p>
          )}
        </section>

        <section className={styles.issue280Shell} aria-labelledby="issue280-title">
          <div className={styles.resultHeader}>
            <div>
              <p className={styles.kicker}>Issue 280 PR E</p>
              <h2 id="issue280-title">Issue 280 local multilingual demo</h2>
            </div>
            <span className={styles.badge}>local/mock only</span>
          </div>
          <p className={styles.scopeNotice}>
            Local/demo path for arbitrary bounded public-safe synthetic markdown. It generates a grounded
            English script, deterministically converts it into the selected supported language, preserves
            citations and evaluation metadata, and keeps all providers disabled or mocked.
          </p>
          <form className={styles.issue280Form} aria-label="Issue 280 local demo form" onSubmit={runIssue280LocalDemo}>
            <div className={styles.field}>
              <span className={styles.labelWithInfo}>
                Project name
                {infoControl("Issue 280 project field info", "Names only the public-safe synthetic project used for the local demo.")}
              </span>
              <input
                aria-label="Issue 280 synthetic project"
                name="issue280ProjectName"
                defaultValue={safeIssue280Defaults.projectName}
              />
            </div>

            <div className={styles.field}>
              <span className={styles.labelWithInfo}>
                Synthetic project knowledge
                {infoControl(
                  "Issue 280 knowledge field info",
                  "Submit bounded public-safe markdown; the local demo extracts grounded facts and converts the generated script.",
                )}
              </span>
              <textarea
                aria-label="Issue 280 synthetic markdown"
                name="issue280KnowledgeDocument"
                defaultValue={safeIssue280Defaults.markdown}
                rows={7}
              />
            </div>

            <div className={styles.controls}>
              <label className={styles.field}>
                <span>Issue 280 content type</span>
                <select aria-label="Issue 280 content type" name="issue280ContentType" defaultValue="text/markdown">
                  <option value="text/markdown">Markdown</option>
                  <option value="text/plain">Unsupported text/plain</option>
                </select>
              </label>
              <label className={styles.field}>
                <span className={styles.labelWithInfo}>
                  Audience
                  {infoControl("Audience info", "Controls the reader emphasis used by the deterministic source-grounded script.")}
                </span>
                <select aria-label="Issue 280 audience" name="issue280Audience" defaultValue="ENGINEER">
                  {audienceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className={styles.controls}>
              <label className={styles.field}>
                <span className={styles.labelWithInfo}>
                  Depth
                  {infoControl("Depth info", "Select CONCISE, STANDARD, or DEEP coverage for the same grounded facts.")}
                </span>
                <select aria-label="Issue 280 depth" name="issue280Depth" defaultValue="STANDARD">
                  <option value="CONCISE">Concise</option>
                  <option value="STANDARD">Standard</option>
                  <option value="DEEP">Deep</option>
                </select>
              </label>
              <label className={styles.field}>
                <span className={styles.labelWithInfo}>
                  Target language
                  {infoControl("Target language info", "The local demo supports the 25 Priority 1 languages and safely refuses planned languages.")}
                </span>
                <select aria-label="Issue 280 target language" name="issue280TargetLanguage" defaultValue="hi">
                  {issue280SupportedLanguageOptions.map((language) => (
                    <option key={language.value} value={language.value}>
                      {language.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className={styles.field}>
              <span className={styles.labelWithInfo}>
                Preserved glossary terms
                {infoControl("Issue 280 glossary help", "Preserved project terms are separated from instructions and bounded by the PR B contract.")}
              </span>
              <textarea
                aria-label="Issue 280 preserved terms"
                name="issue280GlossaryTerms"
                defaultValue={"NarraTwin AI\nlocal demo"}
                rows={3}
              />
            </div>

            <div className={styles.checkboxField}>
              <input
                aria-label="Confirm Issue 280 local mock boundary"
                name="issue280SyntheticAvatarBoundary"
                type="checkbox"
                checked={issue280AvatarBoundary}
                onChange={(event) => setIssue280AvatarBoundary(event.currentTarget.checked)}
              />
              <span className={styles.labelWithInfo}>
                Synthetic avatar boundary: local/mock preview only, no cloned face or voice
                {infoControl("Issue 280 avatar boundary info", "No cloned face or voice is enabled; PR E shows local/mock artifact evidence only.")}
              </span>
            </div>

            <button className={styles.primaryAction} type="submit" disabled={issue280IsRunning || !issue280AvatarBoundary}>
              {issue280IsRunning ? "Running Issue 280 local demo" : "Run Issue 280 local demo"}
            </button>
          </form>

          {issue280IsRunning ? (
            <p className={styles.supportStatus} aria-live="polite">
              Running local/mock Issue 280 multilingual demo.
            </p>
          ) : null}
          {issue280Error ? (
            <p className={styles.errorStatus} role="alert" aria-live="assertive">
              {issue280Error}
            </p>
          ) : null}

          {renderIssue280Evidence(issue280Result, issue280TranscriptExpanded, setIssue280TranscriptExpanded)}
        </section>
      </section>
    </main>
  );
}

function renderIssue280Evidence(
  result: Issue280ResultView | null,
  transcriptExpanded: boolean,
  setTranscriptExpanded: (expanded: boolean) => void,
) {
  if (!result) {
    return (
      <div className={styles.issue280Evidence} aria-label="Issue 280 output evidence">
        <section className={styles.result} aria-labelledby="issue280-empty-script">
          <div className={styles.resultHeader}>
            <h3 id="issue280-empty-script">
              Grounded English script {infoControl("Walkthrough script info", "The accepted script is English citation-bound output generated from the submitted markdown.")}
            </h3>
            <span className={styles.badge}>READY</span>
          </div>
          <p className={styles.emptyState}>No Issue 280 result yet.</p>
          <p className={styles.emptyState}>Script pending</p>
        </section>
        <section className={styles.result} aria-labelledby="issue280-empty-transcript">
          <div className={styles.resultHeader}>
            <h3 id="issue280-empty-transcript">Target transcript evidence {infoControl("Demo preview info", "A local/mock target transcript appears after the stored result exists.")}</h3>
            <span className={styles.badge}>READY</span>
          </div>
          <p className={styles.emptyState}>Transcript pending</p>
          <p className={styles.emptyState}>Target transcript is deterministic local/mock conversion evidence.</p>
        </section>
        <section className={styles.result} aria-labelledby="issue280-empty-citations">
          <div className={styles.resultHeader}>
            <h3 id="issue280-empty-citations">Citations {infoControl("Citations info", "Citations bind visible claims to retrieved context refs and claim supports.")}</h3>
            <span className={styles.badge}>READY</span>
          </div>
          <p className={styles.emptyState}>Citations pending</p>
          <p className={styles.emptyState}>Evaluation pending</p>
        </section>
        <section className={styles.result} aria-labelledby="issue280-empty-posture">
          <div className={styles.resultHeader}>
            <h3 id="issue280-empty-posture">
              Local mock provider posture
              {infoControl(
                "Local mock provider posture info",
                "PR D keeps paid providers disabled, network egress off, and real media/cloned identity unavailable.",
              )}
            </h3>
            <span className={styles.badge}>READY</span>
          </div>
          <p className={styles.emptyState}>Storage pending</p>
          <p className={styles.emptyState}>Provider posture pending</p>
          <p className={styles.emptyState}>Export artifacts pending</p>
          <span className={styles.visuallyInline}>
            {infoControl("Export artifacts info", "Export artifact parity appears after the local/mock run completes.")}
          </span>
        </section>
      </div>
    );
  }

  const { response } = result;
  const segments = response.multilingual.segments;
  const visibleSegments = transcriptExpanded ? segments : segments.slice(0, 2);
  const posture = response.providerPosture;
  const postureText = [
    `llm=${posture.llm}`,
    `translation=${posture.translation}`,
    `voice=${posture.voice}`,
    `avatar=${posture.avatar}`,
    `videoRenderer=${posture.videoRenderer}`,
    `networkEgress=${String(posture.networkEgress)}`,
    `paidProvidersEnabled=${String(posture.paidProvidersEnabled)}`,
    `realProviderCalls=${String(posture.realProviderCalls)}`,
    `clonedIdentity=${String(posture.clonedIdentity)}`,
    `realMedia=${String(posture.realMedia)}`,
    `runtimeProviderMode=${response.trace.runtimeProviderMode}`,
  ].join(" ");

  return (
    <div className={styles.issue280Evidence} aria-label="Issue 280 output evidence">
      <section className={styles.result} aria-labelledby="issue280-script-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-script-title">
            Grounded English script {infoControl("Walkthrough script info", "The accepted script is English citation-bound output generated from the submitted markdown.")}
          </h3>
          <span className={styles.badge}>{response.status}</span>
        </div>
        <dl className={styles.metadata} aria-label="Issue 280 request metadata">
          <div>
            <dt>Project</dt>
            <dd>{result.projectName}</dd>
          </div>
          <div>
            <dt>Knowledge document</dt>
            <dd>{`${result.document.filename} ${result.document.contentType} ${result.document.sizeBytes} bytes`}</dd>
          </div>
          <div>
            <dt>Document checksum</dt>
            <dd>{result.document.checksum}</dd>
          </div>
          <div>
            <dt>Audience</dt>
            <dd>{response.request.audience}</dd>
          </div>
          <div>
            <dt>Depth</dt>
            <dd>{`depth=${response.request.depth}`}</dd>
          </div>
          <div>
            <dt>Target language</dt>
            <dd>{`targetLanguage=${response.request.targetLanguage}`}</dd>
          </div>
          <div>
            <dt>Conversion run</dt>
            <dd>{response.multilingual.multilingualRunId}</dd>
          </div>
          <div>
            <dt>Glossary terms</dt>
            <dd>{result.glossaryTerms.length ? result.glossaryTerms.join(", ") : "none"}</dd>
          </div>
          <div>
            <dt>Accepted</dt>
            <dd>{`accepted=${String(response.accepted)}`}</dd>
          </div>
        </dl>
        <p>{response.generated.acceptedScriptText}</p>
      </section>

      <section className={styles.result} aria-labelledby="issue280-preview-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-preview-title">Target transcript evidence {infoControl("Demo preview info", "Preview shows deterministic local/mock converted transcript evidence.")}</h3>
          <span className={styles.badge}>{response.multilingual.translationMode}</span>
        </div>
        <p className={styles.supportStatus}>
          {`Showing ${visibleSegments.length} of ${segments.length} transcript segments. Target transcript is deterministic local/mock conversion evidence.`}
        </p>
        <div className={styles.transcript} aria-label="Issue 280 validated transcript" dir={response.multilingual.direction}>
          {visibleSegments.map((segment) => (
            <article className={styles.transcriptSegment} key={segment.segmentId}>
              <div className={styles.segmentTextGrid}>
                <div>
                  <strong>Source English</strong>
                  <p>{segment.sourceText}</p>
                </div>
                <div>
                  <strong>Target transcript</strong>
                  <p>{segment.targetText}</p>
                </div>
                <div>
                  <strong>English reference</strong>
                  <p>{segment.englishReferenceText}</p>
                </div>
              </div>
              <dl className={styles.segmentBindings}>
                <div>
                  <dt>Citations</dt>
                  <dd>{segment.citationIndexes.map((index) => `[${index}]`).join(" ")}</dd>
                </div>
                <div>
                  <dt>Context</dt>
                  <dd>{segment.contextRefIds.join(", ")}</dd>
                </div>
                <div>
                  <dt>Claims</dt>
                  <dd>{segment.claimSupportIds.join(", ")}</dd>
                </div>
                <div>
                  <dt>Eval</dt>
                  <dd>{response.evaluation.evaluationId}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
        {segments.length > 2 ? (
          <button className={styles.secondaryAction} type="button" onClick={() => setTranscriptExpanded(!transcriptExpanded)}>
            {transcriptExpanded ? "Collapse Issue 280 transcript" : "Expand full Issue 280 transcript"}
          </button>
        ) : null}
      </section>

      <section className={styles.citations} aria-labelledby="issue280-citations-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-citations-title">
            Citations {infoControl("Citations info", "Visible citations show context refs, chunks, claim supports, and evaluation metadata.")}
          </h3>
          <span className={styles.badge}>{`unsupportedClaimCount=${response.evaluation.unsupportedClaimCount}`}</span>
        </div>
        <ul>
          {response.retrieval.contextRefs.map((contextRef) => {
            const support = response.evaluation.claimSupports.find(
              (candidate) => candidate.contextRefId === contextRef.contextRefId,
            );
            return (
              <li key={contextRef.contextRefId}>
                <strong>[{support?.citationIndex}]</strong>
                <span>{contextRef.sectionHeading}</span>
                <code>{contextRef.contextRefId}</code>
                <p>{`${contextRef.chunkId} supportStatus=${support?.supportStatus ?? "pending"} claimSupportId=${support?.claimSupportId ?? "pending"} evaluationId=${response.evaluation.evaluationId}`}</p>
              </li>
            );
          })}
        </ul>
      </section>

      <section className={styles.result} aria-labelledby="issue280-posture-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-posture-title">
            Local mock provider posture
            {infoControl(
              "Local mock provider posture info",
              "This controlled demo keeps paid providers disabled and uses local/mock providers only.",
            )}
          </h3>
          <span className={styles.badge}>local/mock only</span>
        </div>
        <p>{postureText}</p>
        <dl className={styles.metadata} aria-label="Issue 280 storage and trace metadata">
          <div>
            <dt>Session</dt>
            <dd>{`sessionId=${response.session.sessionId}`}</dd>
          </div>
          <div>
            <dt>Output</dt>
            <dd>{`outputId=${response.storage.outputId}`}</dd>
          </div>
          <div>
            <dt>Stored</dt>
            <dd>{`stored=${String(response.storage.stored)}`}</dd>
          </div>
          <div>
            <dt>Replay</dt>
            <dd>{`replayed=${String(response.session.replayed)}`}</dd>
          </div>
          <div>
            <dt>Request</dt>
            <dd>{response.trace.requestId}</dd>
          </div>
          <div>
            <dt>Output checksum</dt>
            <dd>{response.storage.outputChecksum}</dd>
          </div>
          <div>
            <dt>Metadata checksum</dt>
            <dd>{response.storage.metadataChecksum}</dd>
          </div>
          <div>
            <dt>Artifact bundle</dt>
            <dd>{response.storage.artifactBundleChecksum}</dd>
          </div>
          <div>
            <dt>Report checksum</dt>
            <dd>{response.storage.reportChecksum}</dd>
          </div>
          <div>
            <dt>Evaluation checksum</dt>
            <dd>{response.evaluation.evaluationChecksum}</dd>
          </div>
        </dl>
        {response.session.replayed ? <p className={styles.supportStatus}>Idempotent replay observed</p> : null}
      </section>

      <section className={styles.result} aria-labelledby="issue280-artifacts-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-artifacts-title">
            Export artifacts
            {infoControl("Export artifacts info", "Artifacts are generated locally and preserve transcript, subtitle, metadata, voice, render, and placeholder evidence.")}
          </h3>
          <span className={styles.badge}>7 artifacts</span>
        </div>
        <div className={styles.artifactList} aria-label="Issue 280 export artifact list">
          {renderIssue280ArtifactRow("Translated script", response.artifacts.translatedScript)}
          {renderIssue280ArtifactRow("Subtitles", response.artifacts.subtitles)}
          {renderIssue280ArtifactRow("Transcript metadata", response.artifacts.transcriptMetadata)}
          {renderIssue280ArtifactRow("Voice manifest", response.artifacts.voiceManifest)}
          {renderIssue280ArtifactRow("Avatar demo", response.artifacts.avatarDemo)}
          {renderIssue280ArtifactRow("Render manifest", response.artifacts.renderManifest)}
          {renderIssue280ArtifactRow("Video placeholder", response.artifacts.videoPlaceholder)}
        </div>
      </section>

      <section className={styles.result} aria-labelledby="issue280-report-title">
        <div className={styles.resultHeader}>
          <h3 id="issue280-report-title">Output correctness report</h3>
          <span className={styles.badge}>{response.correctnessReport.status}</span>
        </div>
        <dl className={styles.metadata} aria-label="Issue 280 correctness report">
          <div>
            <dt>Trace</dt>
            <dd>{response.correctnessReport.traceId}</dd>
          </div>
          <div>
            <dt>Segments</dt>
            <dd>{response.correctnessReport.segmentCount}</dd>
          </div>
          <div>
            <dt>Checks</dt>
            <dd>{Object.entries(response.correctnessReport.checks).map(([name, status]) => `${name}=${status}`).join(" ")}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}

export function languageOptionLabel(language: LanguageCatalogRecord) {
  const baseLabel = `${language.englishName} / ${language.nativeName}`;
  return language.localDemoSupportStatus === "SUPPORTED" ? baseLabel : `${baseLabel} - Planned`;
}

function renderIssue280ArtifactRow(label: string, artifact: DownloadableArtifact) {
  const href = `data:${artifact.mimeType};base64,${artifact.contentBase64}`;
  return (
    <div className={styles.artifactRow}>
      <div>
        <strong>{label}</strong>
        <span>{artifact.fileName}</span>
        <small>{artifact.checksum}</small>
      </div>
      <a href={href} download={artifact.fileName} aria-label={`Download Issue 280 artifact ${label}`}>
        Download
      </a>
    </div>
  );
}

function audiencePromptLabel(audience: string) {
  return audienceOptions.find((option) => option.value === audience)?.promptLabel ?? "viewer";
}

export function renderTranscriptSegmentsForTest(segments: TranscriptSegment[]) {
  return renderTranscriptSegments(segments, transcriptDirection(segments[0]?.targetLanguage ?? "en"));
}

function renderTranscriptSegments(segments: TranscriptSegment[], direction: "ltr" | "rtl") {
  return (
    <div className={styles.transcript} aria-label="Validated multilingual transcript">
      {segments.map((segment) => (
        <article className={styles.transcriptSegment} key={segment.segmentId} dir={direction}>
          <div className={styles.segmentTextGrid}>
            <div dir="ltr">
              <strong>Source English</strong>
              <p>{segment.sourceText}</p>
            </div>
            <div dir={direction}>
              <strong>Target transcript</strong>
              <p>{segment.targetText}</p>
            </div>
            <div dir="ltr">
              <strong>English reference</strong>
              <p>{segment.englishReferenceText}</p>
            </div>
          </div>
          <dl className={styles.segmentBindings} dir="ltr">
            <div>
              <dt>Citations</dt>
              <dd>{segment.citationMarkers.join(" ")}</dd>
            </div>
            <div>
              <dt>Context</dt>
              <dd>{segment.contextRefIds.join(", ")}</dd>
            </div>
            <div>
              <dt>Claims</dt>
              <dd>{segment.claimSupportIds.join(", ")}</dd>
            </div>
            <div>
              <dt>Eval</dt>
              <dd>{segment.evaluationId}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

function transcriptDirection(languageTag: string): "ltr" | "rtl" {
  return ["ar", "arz", "he", "fa", "ur"].includes(languageTag) ? "rtl" : "ltr";
}

function buildStage7MultilingualBundle(multilingual: MultilingualWalkthrough, consent: AvatarConsent) {
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

type ArtifactKind = "script" | "subtitles" | "voiceManifest" | "metadata" | "avatarDemo" | "renderManifest" | "videoPlaceholder";

const allowedArtifactMimeTypes: Record<ArtifactKind, string> = {
  script: "text/markdown",
  subtitles: "application/x-subrip",
  voiceManifest: "application/json",
  metadata: "application/json",
  avatarDemo: "text/html",
  renderManifest: "application/json",
  videoPlaceholder: "application/json",
};

const allowedArtifactExtensions: Record<ArtifactKind, string> = {
  script: ".md",
  subtitles: ".srt",
  voiceManifest: ".json",
  metadata: ".json",
  avatarDemo: ".html",
  renderManifest: ".json",
  videoPlaceholder: ".json",
};

type ArtifactValidationContext = {
  multilingualRun?: MultilingualWalkthrough | null;
  avatarRender?: AvatarRender | null;
};

function renderArtifactAction(
  label: string,
  kind: ArtifactKind,
  artifact?: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
	  const validation = artifactValidation(kind, artifact, context);
  if (!artifact || !validation.href) {
    return (
      <button type="button" disabled>
        {validation.state === "blocked" ? `${label} blocked` : label}
      </button>
    );
  }
  return (
    <a href={validation.href} download={artifact.fileName}>
      {label}
    </a>
  );
}

function renderArtifactRow(
  label: string,
  kind: ArtifactKind,
  artifact?: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
	  const validation = artifactValidation(kind, artifact, context);
  return (
    <div className={styles.artifactRow}>
      <div>
        <strong>{label}</strong>
        <span>{artifact?.fileName ?? "pending"}</span>
        {validation.state === "blocked" ? (
          <small className={styles.artifactReason}>Blocked: {validation.reason}</small>
        ) : null}
      </div>
      {validation.state === "ready" && artifact && validation.href ? (
        <a href={validation.href} download={artifact.fileName} aria-label={`Download export artifact ${label}`}>
          Download
        </a>
      ) : validation.state === "blocked" ? (
        <button type="button" disabled aria-label={`Blocked export artifact ${label}`}>
          Blocked
        </button>
      ) : (
        <button type="button" disabled aria-label={`Download export artifact ${label}`}>
          Pending
        </button>
      )}
    </div>
  );
}

type ArtifactValidation = {
  state: "pending" | "ready" | "blocked";
  href: string;
  reason: string;
};

export function artifactSafetyState(
  kind: ArtifactKind,
  artifact?: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
  return artifactValidation(kind, artifact, context).state;
}

export function artifactBlockReason(
  kind: ArtifactKind,
  artifact?: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
  return artifactValidation(kind, artifact, context).reason;
}

	export function artifactHref(kind: ArtifactKind, artifact?: DownloadableArtifact, context?: ArtifactValidationContext) {
	  return artifactValidation(kind, artifact, context).href;
	}

function artifactValidation(
  kind: ArtifactKind,
  artifact?: DownloadableArtifact,
  context?: ArtifactValidationContext,
): ArtifactValidation {
  if (!artifact) {
    return { state: "pending", href: "", reason: "Artifact has not been produced yet." };
  }
  if (artifact.mimeType !== allowedArtifactMimeTypes[kind]) {
    return { state: "blocked", href: "", reason: "Unexpected MIME type." };
  }
  if (!artifact.fileName.endsWith(allowedArtifactExtensions[kind])) {
    return { state: "blocked", href: "", reason: "Unexpected file extension." };
  }
  if (!safeArtifactFileName(artifact.fileName)) {
    return { state: "blocked", href: "", reason: "Unsafe filename." };
  }
	  if (!languageMatchesArtifactName(kind, artifact.fileName, context)) {
	    return { state: "blocked", href: "", reason: "Artifact language does not match the selected run." };
	  }
	  const decoded = decodeBase64Artifact(artifact.contentBase64);
  if (!decoded) {
    return { state: "blocked", href: "", reason: "Invalid base64 content." };
  }
  if (decoded.bytes.length > 512 * 1024) {
    return { state: "blocked", href: "", reason: "Artifact exceeds local preview limit." };
  }
  if (!artifact.checksum || artifact.checksum !== `sha256:${sha256Hex(decoded.text)}`) {
    return { state: "blocked", href: "", reason: "Checksum mismatch." };
  }
  if (kind === "avatarDemo" && activeHtmlPattern.test(decoded.text)) {
    return { state: "blocked", href: "", reason: "HTML export contains active content." };
  }
	  if (
	    (kind === "voiceManifest" || kind === "metadata" || kind === "renderManifest" || kind === "videoPlaceholder") &&
	    !validJsonArtifact(kind, decoded.text, artifact, context)
	  ) {
	    return { state: "blocked", href: "", reason: "JSON metadata shape is invalid." };
	  }
  return {
    state: "ready",
    href: `data:${artifact.mimeType};base64,${artifact.contentBase64}`,
    reason: "",
  };
}

function safeArtifactFileName(fileName: string) {
  if (!fileName || fileName.includes("/") || fileName.includes("\\")) {
    return false;
  }
  return !/[\u0000-\u001f\u007f]/.test(fileName);
}

const activeHtmlPattern =
  /<script\b|<iframe\b|<form\b|<object\b|<embed\b|<link\b|<base\b|<style\b|<meta\s+http-equiv\b|<[^>]+\s(?:on[a-z]+|src|href|srcset|style)\s*=|<[^>]+javascript:/i;

function decodeBase64Artifact(contentBase64: string) {
  if (!/^[A-Za-z0-9+/]*={0,2}$/.test(contentBase64) || contentBase64.length % 4 !== 0) {
    return null;
  }
  try {
    const binary = atob(contentBase64);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    return { bytes, text };
  } catch {
    return null;
  }
}

function languageMatchesArtifactName(kind: ArtifactKind, fileName: string, context?: ArtifactValidationContext) {
	  const language = context?.multilingualRun?.targetLanguage;
	  if (!language) {
	    return true;
	  }
	  if (kind === "script") {
	    return fileName.endsWith(`-${language}-script.md`);
	  }
	  if (kind === "subtitles") {
	    return fileName.endsWith(`-${language}.srt`);
	  }
	  if (kind === "voiceManifest") {
	    return fileName === `voice-manifest-${language}.json`;
	  }
	  if (kind === "metadata") {
	    return fileName.endsWith(`-${language}-metadata.json`);
	  }
	  return true;
	}

function validJsonArtifact(
  kind: ArtifactKind,
  text: string,
  artifact: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
	  try {
	    const parsed = JSON.parse(text) as Record<string, unknown>;
	    if (!parsed || typeof parsed !== "object") {
	      return false;
	    }
	    if (kind === "renderManifest") {
	      return (
	        parsed.schema === "Stage7AvatarRenderManifest" &&
	        sourceMetadataMatches(parsed["source"], context) &&
	        providerConfigIsLocal(parsed["providerConfig"]) &&
	        multilingualBundleMatches(parsed["multilingualBundle"], context)
	      );
	    }
	    if (kind === "videoPlaceholder") {
	      return (
	        parsed.schema === "Stage7VideoExportPlaceholder" &&
	        parsed.realVideoProduced === false &&
	        sourceMetadataMatches(parsed["source"], context) &&
	        providerConfigIsLocal(parsed["providerConfig"]) &&
	        multilingualBundleMatches(parsed["multilingualBundle"], context)
	      );
	    }
    if (kind === "voiceManifest") {
      return voiceManifestMatches(parsed, artifact, context);
	    }
    if (kind === "metadata") {
      return transcriptMetadataMatches(parsed, context);
	    }
	    return true;
	  } catch {
	    return false;
	  }
	}

function transcriptMetadataMatches(metadata: Record<string, unknown>, context?: ArtifactValidationContext) {
  const multilingual = context?.multilingualRun;
  if (!multilingual) {
    return false;
  }
  const correctness = asRecord(metadata.transcriptCorrectness);
  return (
    metadata.multilingualRunId === multilingual.multilingualRunId &&
    metadata.sourceRunId === multilingual.sourceRunId &&
    metadata.targetLanguage === multilingual.targetLanguage &&
    correctness?.validationStatus === multilingual.transcriptCorrectness.validationStatus &&
    correctness.segmentCount === multilingual.transcriptCorrectness.segmentCount &&
    transcriptSegmentsMatch(metadata.transcriptSegments, multilingual.transcriptSegments) &&
    stringArrayEquals(metadata.sourceContextRefIds, multilingual.trace.sourceContextRefIds) &&
    numberArrayEquals(metadata.sourceCitationIndexes, multilingual.trace.sourceCitationIndexes)
  );
}

function transcriptSegmentsMatch(value: unknown, expected: TranscriptSegment[]) {
  return (
    Array.isArray(value) &&
    value.length === expected.length &&
    value.every((entry, index) => {
      const segment = asRecord(entry);
      const expectedSegment = expected[index];
      return (
        segment?.segmentId === expectedSegment.segmentId &&
        segment.sourceText === expectedSegment.sourceText &&
        segment.targetText === expectedSegment.targetText &&
        segment.englishReferenceText === expectedSegment.englishReferenceText &&
        stringArrayEquals(segment.citationMarkers, expectedSegment.citationMarkers) &&
        numberArrayEquals(segment.citationIndexes, expectedSegment.citationIndexes) &&
        stringArrayEquals(segment.contextRefIds, expectedSegment.contextRefIds) &&
        stringArrayEquals(segment.claimSupportIds, expectedSegment.claimSupportIds)
      );
    })
  );
}

function sourceMetadataMatches(value: unknown, context?: ArtifactValidationContext) {
	  const source = asRecord(value);
	  const render = context?.avatarRender;
	  if (!source || !render) {
	    return false;
	  }
	  return (
	    source.runId === render.sourceRunId &&
	    source.evaluationId === render.trace.sourceEvaluationId &&
	    source.evaluationChecksum === render.trace.sourceEvaluationChecksum &&
	    stringArrayEquals(source.contextRefIds, render.trace.sourceContextRefIds) &&
	    numberArrayEquals(source.citationIndexes, render.trace.sourceCitationIndexes)
	  );
	}

function providerConfigIsLocal(value: unknown) {
	  const providerConfig = asRecord(value);
	  return (
	    providerConfig?.provider === "mock" &&
	    providerConfig.providerMode === "LOCAL" &&
	    providerConfig.allowNetworkEgress === false &&
	    providerConfig.requiresApiKey === false &&
	    providerConfig.supportsRealVideo === false &&
	    providerConfig.supportsClonedIdentity === false
	  );
	}

function multilingualBundleMatches(value: unknown, context?: ArtifactValidationContext) {
	  const bundle = asRecord(value);
	  const multilingual = context?.multilingualRun;
	  const render = context?.avatarRender;
	  if (!bundle || !multilingual || !render) {
	    return false;
	  }
	  const posture = asRecord(bundle.providerPosture);
	  return (
	    bundle.sourceRunId === multilingual.sourceRunId &&
	    bundle.sourceRunId === render.sourceRunId &&
	    bundle.multilingualRunId === multilingual.multilingualRunId &&
	    bundle.multilingualRunId === render.trace.multilingualRunId &&
	    bundle.targetLanguage === multilingual.targetLanguage &&
	    bundle.targetLanguage === render.trace.targetLanguage &&
	    bundle.translatedScriptChecksum === multilingual.artifacts.translatedScript.checksum &&
	    bundle.translatedScriptChecksum === render.trace.translatedScriptChecksum &&
	    bundle.subtitlesChecksum === multilingual.artifacts.subtitles.checksum &&
	    bundle.subtitlesChecksum === render.trace.subtitlesChecksum &&
	    bundle.voiceManifestChecksum === multilingual.artifacts.voiceManifest.checksum &&
	    bundle.voiceManifestChecksum === render.trace.voiceManifestChecksum &&
	    stringArrayEquals(bundle.contextRefIds, multilingual.trace.sourceContextRefIds) &&
	    stringArrayEquals(bundle.contextRefIds, render.trace.sourceContextRefIds) &&
	    numberArrayEquals(bundle.citationIndexes, multilingual.trace.sourceCitationIndexes) &&
	    numberArrayEquals(bundle.citationIndexes, render.trace.sourceCitationIndexes) &&
	    bundle.evaluationId === multilingual.trace.sourceEvaluationId &&
	    bundle.evaluationId === render.trace.sourceEvaluationId &&
	    bundle.evaluationChecksum === multilingual.trace.sourceEvaluationChecksum &&
	    bundle.evaluationChecksum === render.trace.sourceEvaluationChecksum &&
	    posture?.translationProvider === multilingual.translationProvider.provider &&
	    posture.translationProviderMode === multilingual.translationProvider.providerMode &&
	    posture.voiceProvider === multilingual.voice.provider &&
	    posture.voiceProviderMode === multilingual.voice.providerMode
	  );
	}

function voiceManifestMatches(
  manifest: Record<string, unknown>,
  artifact: DownloadableArtifact,
  context?: ArtifactValidationContext,
) {
  const multilingual = context?.multilingualRun;
  const voice = multilingual?.voice;
  if (!multilingual || !voice) {
    return false;
  }
  const manifestKeys = [
    "disclosure",
    "durationSecondsEstimate",
    "language",
    "languageDisplayName",
    "mockAudioProfile",
    "provider",
    "providerMode",
    "textChecksum",
  ];
  const audioProfile = asRecord(manifest.mockAudioProfile);
  return (
    stringArrayEquals(Object.keys(manifest).sort(), manifestKeys) &&
    manifest.provider === voice.provider &&
    manifest.provider === "mock" &&
    manifest.providerMode === voice.providerMode &&
    manifest.providerMode === "LOCAL" &&
    manifest.language === multilingual.targetLanguage &&
    typeof manifest.languageDisplayName === "string" &&
    manifest.languageDisplayName.trim().length > 0 &&
    manifest.textChecksum === `sha256:${sha256Hex(multilingual.translatedScriptText)}` &&
    typeof manifest.durationSecondsEstimate === "number" &&
    manifest.durationSecondsEstimate > 0 &&
    !!audioProfile &&
    stringArrayEquals(Object.keys(audioProfile).sort(), ["channels", "durationMillisecondsEstimate", "sampleRateHz"]) &&
    audioProfile.durationMillisecondsEstimate !== true &&
    typeof audioProfile.durationMillisecondsEstimate === "number" &&
    Number.isInteger(audioProfile.durationMillisecondsEstimate) &&
    audioProfile.durationMillisecondsEstimate > 0 &&
    audioProfile.sampleRateHz === 16000 &&
    audioProfile.channels === 1 &&
    typeof manifest.disclosure === "string" &&
    manifest.disclosure.includes("Mock local TTS placeholder") &&
    artifact.checksum === multilingual.artifacts.voiceManifest.checksum
  );
}

function asRecord(value: unknown) {
	  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
	}

	function stringArrayEquals(value: unknown, expected: string[]) {
	  return Array.isArray(value) && value.length === expected.length && value.every((entry, index) => entry === expected[index]);
	}

	function numberArrayEquals(value: unknown, expected: number[]) {
	  return Array.isArray(value) && value.length === expected.length && value.every((entry, index) => entry === expected[index]);
	}

export function sha256Hex(text: string) {
  const bytes = new TextEncoder().encode(text);
  const bitLength = bytes.length * 8;
  const paddedLength = (((bytes.length + 9 + 63) >> 6) << 6);
  const padded = new Uint8Array(paddedLength);
  padded.set(bytes);
  padded[bytes.length] = 0x80;
  const view = new DataView(padded.buffer);
  view.setUint32(paddedLength - 4, bitLength, false);

  const hash = new Uint32Array([
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
    0x5be0cd19,
  ]);
  const constants = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
    0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
    0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
    0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
    0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
    0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
    0xc67178f2,
  ];
  const words = new Uint32Array(64);

  for (let offset = 0; offset < padded.length; offset += 64) {
    for (let index = 0; index < 16; index += 1) {
      words[index] = view.getUint32(offset + index * 4, false);
    }
    for (let index = 16; index < 64; index += 1) {
      const s0 = rotateRight(words[index - 15], 7) ^ rotateRight(words[index - 15], 18) ^ (words[index - 15] >>> 3);
      const s1 = rotateRight(words[index - 2], 17) ^ rotateRight(words[index - 2], 19) ^ (words[index - 2] >>> 10);
      words[index] = (words[index - 16] + s0 + words[index - 7] + s1) >>> 0;
    }

    let a = hash[0];
    let b = hash[1];
    let c = hash[2];
    let d = hash[3];
    let e = hash[4];
    let f = hash[5];
    let g = hash[6];
    let h = hash[7];

    for (let index = 0; index < 64; index += 1) {
      const s1 = rotateRight(e, 6) ^ rotateRight(e, 11) ^ rotateRight(e, 25);
      const choice = (e & f) ^ (~e & g);
      const temp1 = (h + s1 + choice + constants[index] + words[index]) >>> 0;
      const s0 = rotateRight(a, 2) ^ rotateRight(a, 13) ^ rotateRight(a, 22);
      const majority = (a & b) ^ (a & c) ^ (b & c);
      const temp2 = (s0 + majority) >>> 0;
      h = g;
      g = f;
      f = e;
      e = (d + temp1) >>> 0;
      d = c;
      c = b;
      b = a;
      a = (temp1 + temp2) >>> 0;
    }

    hash[0] = (hash[0] + a) >>> 0;
    hash[1] = (hash[1] + b) >>> 0;
    hash[2] = (hash[2] + c) >>> 0;
    hash[3] = (hash[3] + d) >>> 0;
    hash[4] = (hash[4] + e) >>> 0;
    hash[5] = (hash[5] + f) >>> 0;
    hash[6] = (hash[6] + g) >>> 0;
    hash[7] = (hash[7] + h) >>> 0;
  }

  return Array.from(hash, (word) => word.toString(16).padStart(8, "0")).join("");
}

function rotateRight(value: number, bits: number) {
  return (value >>> bits) | (value << (32 - bits));
}

function checksumSeed(...values: string[]) {
  let hash = 0;
  for (const value of values.join("|")) {
    hash = (hash * 31 + value.charCodeAt(0)) >>> 0;
  }
  return hash.toString(16);
}
