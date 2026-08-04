import { describe, expect, it } from "vitest";

import {
  GuideWorkflowError,
  runQuietPresenceDemo,
  type GuideDemoInput,
} from "./guide-client";

const checksums = {
  evaluation: `sha256:${"a".repeat(64)}`,
  script: `sha256:${"b".repeat(64)}`,
  subtitles: `sha256:${"c".repeat(64)}`,
  voice: `sha256:${"d".repeat(64)}`,
};

const input: GuideDemoInput = {
  projectName: "Northwind release workspace",
  knowledgeDocument: "# Release 2.4.0\nSecurity review must pass before deployment.",
  audience: "PRODUCT_LEADER",
  depth: "CONCISE",
  targetLanguage: "es",
  glossaryTerms: ["Northwind", "Release 2.4.0"],
  syntheticAvatarConsent: true,
};

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function successfulFetch(overrides: Partial<Record<number, unknown>> = {}) {
  const calls: Array<{ url: string; init?: RequestInit }> = [];
  const fetcher = async (request: RequestInfo | URL, init?: RequestInit) => {
    const url = String(request);
    calls.push({ url, init });
    const position = calls.length;
    const responses: Record<number, unknown> = {
      1: { projectId: "project_001" },
      2: { documentId: "document_001" },
      3: { documentId: "document_001", approvalStatus: "APPROVED" },
      4: { ingestionRunId: "ingestion_001", status: "COMPLETED" },
      5: {
        runId: "run_001",
        status: "COMPLETED",
        evaluationStatus: "PASSED",
        acceptedScriptText: "The security review is still in progress. [1]",
        contextRefs: [
          {
            contextRefId: "context_001",
            chunkId: "chunk_001",
            documentId: "document_001",
            sourceFilename: "northwind-release.md",
            evidenceSnapshot: {
              redactedExcerpt: "Security review must pass before deployment.",
            },
          },
        ],
        evaluation: {
          evaluationId: "evaluation_001",
          evaluationStatus: "PASSED",
          unsupportedClaimCount: 0,
          claimSupports: [
            {
              claimSupportId: "support_001",
              contextRefId: "context_001",
              chunkId: "chunk_001",
              documentId: "document_001",
              citationIndex: 1,
            },
          ],
        },
        trace: { traceId: "trace_001" },
      },
      6: {
        multilingualRunId: "multilingual_001",
        sourceRunId: "run_001",
        targetLanguage: "es",
        status: "COMPLETED",
        sourceScriptText: "The security review is still in progress. [1]",
        translatedScriptText: "La revisión de seguridad sigue en curso. [1]",
        artifacts: {
          translatedScript: { checksum: checksums.script },
          subtitles: { checksum: checksums.subtitles },
          voiceManifest: { checksum: checksums.voice },
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
          sourceEvaluationChecksum: checksums.evaluation,
          evaluationStatus: "PASSED",
        },
      },
      7: {
        consentRecordId: "consent_001",
        sourceRunId: "run_001",
        sourceContextRefIds: ["context_001"],
        sourceCitationIndexes: [1],
        sourceEvaluationId: "evaluation_001",
        sourceEvaluationChecksum: checksums.evaluation,
        evaluationStatus: "PASSED",
        consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
        consentStatementText: "Synthetic presenter approved for this local demo.",
      },
      8: {
        avatarRenderId: "render_001",
        status: "COMPLETED",
        renderJobStatus: "COMPLETED",
        sourceRunId: "run_001",
        sourceScriptText: "La revisión de seguridad sigue en curso. [1]",
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
          sourceEvaluationChecksum: checksums.evaluation,
          evaluationStatus: "PASSED",
          multilingualRunId: "multilingual_001",
          targetLanguage: "es",
          translatedScriptChecksum: checksums.script,
          subtitlesChecksum: checksums.subtitles,
          voiceManifestChecksum: checksums.voice,
        },
      },
    };
    return jsonResponse(overrides[position] ?? responses[position]);
  };
  return { calls, fetcher };
}

describe("runQuietPresenceDemo", () => {
  it("requires explicit synthetic-presenter consent before the first request", async () => {
    const { calls, fetcher } = successfulFetch();

    await expect(runQuietPresenceDemo({ ...input, syntheticAvatarConsent: false }, fetcher)).rejects.toMatchObject({
      code: "CONSENT_REQUIRED",
    });
    expect(calls).toHaveLength(0);
  });

  it("propagates cancellation and returns a bounded aborted result", async () => {
    const controller = new AbortController();
    const fetcher = (_request: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        expect(init?.signal).toBe(controller.signal);
        init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
      });

    const run = runQuietPresenceDemo(input, fetcher, controller.signal);
    controller.abort();
    await expect(run).rejects.toMatchObject({ code: "REQUEST_ABORTED" });
  });

  it("uses the existing local pipeline in the required order and returns inspectable evidence", async () => {
    const { calls, fetcher } = successfulFetch();

    const result = await runQuietPresenceDemo(input, fetcher);

    expect(calls.map((call) => call.url)).toEqual([
      "/api/v1/projects",
      "/api/v1/projects/project_001/knowledge-documents",
      "/api/v1/projects/project_001/knowledge-documents/document_001/approval",
      "/api/v1/projects/project_001/ingestion-runs",
      "/api/v1/projects/project_001/walkthrough-runs",
      "/api/v1/projects/project_001/walkthrough-runs/run_001/multilingual-runs",
      "/api/v1/projects/project_001/walkthrough-runs/run_001/avatar-consents",
      "/api/v1/projects/project_001/walkthrough-runs/run_001/avatar-renders",
    ]);
    expect(result.explanation).toContain("security review");
    expect(result.sources).toEqual([
      {
        citationIndex: 1,
        filename: "northwind-release.md",
        excerpt: "Security review must pass before deployment.",
        contextRefId: "context_001",
      },
    ]);
    expect(result.evaluation).toEqual({ status: "PASSED", unsupportedClaimCount: 0 });
    expect(result.providerPosture).toEqual({
      avatar: "mock",
      avatarMode: "LOCAL",
      translation: "mock",
      translationMode: "LOCAL",
      voice: "mock",
      voiceMode: "LOCAL",
      networkEgress: false,
      realMedia: false,
      clonedIdentity: false,
      consent: "CONFIRMED",
    });
    expect(JSON.parse(String(calls[7].init?.body))).toMatchObject({
      consentToUseSyntheticAvatar: true,
      consentRecordId: "consent_001",
      clonedIdentityRequested: false,
      multilingualBundle: {
        sourceRunId: "run_001",
        multilingualRunId: "multilingual_001",
        evaluationId: "evaluation_001",
      },
    });
  });

  it("fails before multilingual, consent, or render work when grounding refuses", async () => {
    const { calls, fetcher: baseFetcher } = successfulFetch();
    const fetcher = async (request: RequestInfo | URL, init?: RequestInit) => {
      if (calls.length === 4) {
        calls.push({ url: String(request), init });
        return jsonResponse({
          runId: "run_refused",
          status: "REFUSED",
          acceptedScriptText: null,
          contextRefs: [],
          failure: { reasonCode: "LOW_RETRIEVAL_CONFIDENCE" },
        });
      }
      return baseFetcher(request, init);
    };

    await expect(runQuietPresenceDemo(input, fetcher)).rejects.toMatchObject({
      name: "GuideWorkflowError",
      code: "GROUNDING_REFUSED",
    });
    expect(calls).toHaveLength(5);
  });

  it("turns untrusted API failures into a bounded user-safe error", async () => {
    const fetcher = async () =>
      jsonResponse(
        {
          code: "INTERNAL_ERROR",
          message: "sensitivity-canary must stay private from the interface",
        },
        500,
      );

    try {
      await runQuietPresenceDemo(input, fetcher);
      throw new Error("Expected the workflow to fail.");
    } catch (error) {
      expect(error).toBeInstanceOf(GuideWorkflowError);
      expect(error).toMatchObject({ code: "REQUEST_FAILED" });
      expect(String(error)).not.toContain("sensitivity-canary");
    }
  });

  it.each([
    ["numeric evaluation counts", 5, { evaluation: { evaluationId: "evaluation_001", evaluationStatus: "PASSED", unsupportedClaimCount: "0", claimSupports: [] } }],
    ["missing source mapping", 5, { evaluation: { evaluationId: "evaluation_001", evaluationStatus: "PASSED", unsupportedClaimCount: 0, claimSupports: [] } }],
    ["external translation mode", 6, { translationProvider: { provider: "external", providerMode: "OPTIONAL_EXTERNAL" } }],
    ["missing Stage 6 lineage", 6, { trace: { sourceContextRefIds: [] } }],
    ["blank run identity", 5, { runId: "" }],
    ["blank evaluation identity", 5, { evaluation: { evaluationId: "" } }],
    ["malformed evaluation digest", 6, { trace: { sourceEvaluationChecksum: "sha256:fake" } }],
    ["malformed translated artifact digest", 6, { artifacts: { translatedScript: { checksum: "sha256:fake" } } }],
    ["blank multilingual identity", 6, { multilingualRunId: "" }],
    ["unconfirmed consent", 8, { disclosure: { consentStatus: "NOT_REQUIRED", clonedIdentity: false, message: "invalid" } }],
    ["real-video capability", 8, { providerConfig: { provider: "mock", providerMode: "LOCAL", adapterKind: "MOCK_LOCAL", allowNetworkEgress: false, requiresApiKey: false, supportsRealVideo: true, supportsClonedIdentity: false } }],
    ["mismatched Stage 7 script", 8, { sourceScriptText: "Different translated script" }],
  ])("fails closed on %s before presenting success", async (_label, position, mutation) => {
    const baseline = successfulResponses();
    const changed = { ...baseline[position], ...mutation };
    const { fetcher } = successfulFetch({ [position]: changed });

    await expect(runQuietPresenceDemo(input, fetcher)).rejects.toBeInstanceOf(GuideWorkflowError);
  });
});

function successfulResponses(): Record<number, Record<string, unknown>> {
  return fixtureResponses();
}

function fixtureResponses(): Record<number, Record<string, unknown>> {
  return {
    5: {
      runId: "run_001", status: "COMPLETED", evaluationStatus: "PASSED",
      acceptedScriptText: "The security review is still in progress. [1]",
      contextRefs: [{ contextRefId: "context_001", chunkId: "chunk_001", documentId: "document_001", sourceFilename: "northwind-release.md", evidenceSnapshot: { redactedExcerpt: "Security review must pass before deployment." } }],
      evaluation: { evaluationId: "evaluation_001", evaluationStatus: "PASSED", unsupportedClaimCount: 0, claimSupports: [{ claimSupportId: "support_001", contextRefId: "context_001", chunkId: "chunk_001", documentId: "document_001", citationIndex: 1 }] },
      trace: { traceId: "trace_001" },
    },
    6: {
      multilingualRunId: "multilingual_001", sourceRunId: "run_001", targetLanguage: "es", status: "COMPLETED",
      sourceScriptText: "The security review is still in progress. [1]", translatedScriptText: "La revisión de seguridad sigue en curso. [1]",
      artifacts: { translatedScript: { checksum: checksums.script }, subtitles: { checksum: checksums.subtitles }, voiceManifest: { checksum: checksums.voice } },
      translationProvider: { provider: "mock", providerMode: "LOCAL" }, voice: { provider: "mock", providerMode: "LOCAL" },
      trace: { sourceContextRefCount: 1, sourceCitationCount: 1, sourceContextRefIds: ["context_001"], sourceCitationIndexes: [1], sourceClaimSupportIds: ["support_001"], sourceEvaluationId: "evaluation_001", sourceEvaluationChecksum: checksums.evaluation, evaluationStatus: "PASSED" },
    },
    8: {
      avatarRenderId: "render_001", status: "COMPLETED", renderJobStatus: "COMPLETED", sourceRunId: "run_001", sourceScriptText: "La revisión de seguridad sigue en curso. [1]",
      avatarProvider: { provider: "mock", providerMode: "LOCAL" }, providerConfig: { provider: "mock", providerMode: "LOCAL", adapterKind: "MOCK_LOCAL", allowNetworkEgress: false, requiresApiKey: false, supportsRealVideo: false, supportsClonedIdentity: false },
      disclosure: { consentStatus: "CONFIRMED", clonedIdentity: false, message: "Synthetic local presenter. No cloned identity." },
      trace: { sourceContextRefCount: 1, sourceCitationCount: 1, sourceContextRefIds: ["context_001"], sourceCitationIndexes: [1], sourceEvaluationId: "evaluation_001", sourceEvaluationChecksum: checksums.evaluation, evaluationStatus: "PASSED", multilingualRunId: "multilingual_001", targetLanguage: "es", translatedScriptChecksum: checksums.script, subtitlesChecksum: checksums.subtitles, voiceManifestChecksum: checksums.voice },
    },
  };
}
