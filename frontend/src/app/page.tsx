"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import styles from "./page.module.css";

type ClaimSupport = {
  claimId: string;
  contextRefId: string;
  citationIndex: number;
};

type ContextRef = {
  contextRefId: string;
  sourceFilename: string;
  chunkId: string;
  evidenceSnapshot: {
    redactedExcerpt: string;
  };
};

type WalkthroughRun = {
  runId: string;
  status: string;
  acceptedScriptText?: string;
  evaluation?: {
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
  };
  trace: {
    sourceContextRefIds: string[];
    sourceCitationIndexes: number[];
    sourceEvaluationId: string;
    sourceEvaluationChecksum: string;
  };
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

type DocumentResponse = {
  documentId: string;
};

type ApiErrorPayload = {
  error?: {
    code?: unknown;
    message?: unknown;
  };
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
export const defaultKnowledge = `# NarraTwin AI

NarraTwin AI turns approved project knowledge into grounded walkthrough scripts.

It supports recruiter and engineering audiences with audience-aware explanations.

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
  "UNSAFE_DISPLAY_TEXT",
  "UNSAFE_URL",
]);

const unsafeApiErrorMessagePattern =
  /contentBase64|fake-invite-input|fake-session-input|idem_[A-Za-z0-9_.:-]*|session_[A-Za-z0-9_.:-]*|inviteSecret|sessionSecret|auth token|bearer token|cookie|raw prompt|raw script|provider payload/i;

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

export function evaluationBadgeLabel(run: WalkthroughRun | null): string {
  if (!run?.evaluation) {
    return "Evaluation pending";
  }
  return `${run.evaluation.unsupportedClaimCount} unsupported claims`;
}

const safeWalkthroughFailureReasons = new Set([
  "LOW_RETRIEVAL_CONFIDENCE",
  "PROMPT_INJECTION_DETECTED",
  "UNSAFE_RETRIEVED_CONTEXT",
  "UNSUPPORTED_PROJECT_FACT",
]);

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
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState("");

  async function generateWalkthrough(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const projectName = String(form.get("projectName") ?? "NarraTwin AI").trim();
    const knowledgeDocument = String(form.get("knowledgeDocument") ?? "").trim();
    const audience = String(form.get("audience") ?? "RECRUITER");
    const depth = String(form.get("depth") ?? "CONCISE");
    const targetLanguage = String(form.get("targetLanguage") ?? "es");
    const consentToUseSyntheticAvatar = syntheticAvatarConsent;
    const glossaryTerms = String(form.get("glossaryTerms") ?? "")
      .split("\n")
      .map((term) => term.trim())
      .filter(Boolean);
    const requestSeed = checksumSeed(projectName, knowledgeDocument, audience, depth, targetLanguage);
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
          prompt: "Create a concise grounded walkthrough for a recruiter.",
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
          targetLanguage,
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
      setError(caught instanceof Error ? caught.message : "Stage 7 API request failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  const supports = run?.evaluation?.claimSupports ?? [];
  const previewScript =
    multilingualRun?.translatedScriptText ??
    run?.acceptedScriptText ??
    "Generate a grounded script to display cited output.";
	  const avatarPreviewScript =
	    avatarRender?.sourceScriptText ?? run?.acceptedScriptText ?? "Generate a grounded script to display cited output.";
	  const artifactContext = { multilingualRun, avatarRender };

  return (
    <main className={styles.page} aria-busy={isGenerating}>
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
                <option value="RECRUITER">Recruiter</option>
                <option value="ENGINEER">Engineer</option>
              </select>
            </label>

            <label className={styles.field}>
              <span>Depth</span>
              <select name="depth" defaultValue="CONCISE">
                <option value="CONCISE">Concise</option>
                <option value="STANDARD">Standard</option>
              </select>
            </label>
          </div>

          <div className={styles.controls}>
            <label className={styles.field}>
              <span>Target language</span>
              <select name="targetLanguage" defaultValue="es">
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="hi">Hindi</option>
              </select>
            </label>

            <label className={styles.field}>
              <span>Glossary terms</span>
              <textarea
                name="glossaryTerms"
                defaultValue={"NarraTwin AI\nproject knowledge\nsource chunks"}
                rows={4}
              />
            </label>
          </div>

          <label className={styles.checkboxField}>
            <input
              name="syntheticAvatarConsent"
              type="checkbox"
              checked={syntheticAvatarConsent}
              onChange={(event) => setSyntheticAvatarConsent(event.currentTarget.checked)}
            />
            <span>Synthetic avatar consent: local AI presenter, no cloned face or voice</span>
          </label>

          <button className={styles.primaryAction} type="submit" disabled={isGenerating || !syntheticAvatarConsent}>
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
          <p>
            {previewScript}
          </p>
          <div className={styles.artifactActions} aria-label="Downloadable artifacts">
	            {renderArtifactAction("Download script", "script", multilingualRun?.artifacts.translatedScript, artifactContext)}
	            {renderArtifactAction("Download subtitles", "subtitles", multilingualRun?.artifacts.subtitles, artifactContext)}
	            {renderArtifactAction(
	              "Download voice manifest",
	              "voiceManifest",
	              multilingualRun?.artifacts.voiceManifest,
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
            <h2 id="preview-title">Demo preview</h2>
            <span className={styles.badge}>{avatarRender?.renderJobStatus ?? "READY"}</span>
          </div>
          <div className={styles.previewFrame} aria-label="Avatar demo preview">
            <div className={styles.previewScreen}>
              <div className={styles.previewPresenter} aria-hidden="true">
                AI
              </div>
              <div className={styles.previewCopy}>
                <strong>{avatarRender?.videoRenderer.renderer ?? "local-html"}</strong>
                <p>{avatarPreviewScript}</p>
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
            <span className={styles.badge}>{avatarRender ? "6 artifacts" : "READY"}</span>
          </div>
          <div className={styles.artifactList} aria-label="Export artifact list">
	            {renderArtifactRow("Translated script", "script", multilingualRun?.artifacts.translatedScript, artifactContext)}
	            {renderArtifactRow("Subtitles", "subtitles", multilingualRun?.artifacts.subtitles, artifactContext)}
	            {renderArtifactRow("Voice manifest", "voiceManifest", multilingualRun?.artifacts.voiceManifest, artifactContext)}
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
      </section>
    </main>
  );
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

type ArtifactKind = "script" | "subtitles" | "voiceManifest" | "avatarDemo" | "renderManifest" | "videoPlaceholder";

const allowedArtifactMimeTypes: Record<ArtifactKind, string> = {
  script: "text/markdown",
  subtitles: "application/x-subrip",
  voiceManifest: "application/json",
  avatarDemo: "text/html",
  renderManifest: "application/json",
  videoPlaceholder: "application/json",
};

const allowedArtifactExtensions: Record<ArtifactKind, string> = {
  script: ".md",
  subtitles: ".srt",
  voiceManifest: ".json",
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
	    (kind === "voiceManifest" || kind === "renderManifest" || kind === "videoPlaceholder") &&
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
	    return true;
	  } catch {
	    return false;
	  }
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
    manifest.textChecksum === multilingual.artifacts.translatedScript.checksum &&
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
