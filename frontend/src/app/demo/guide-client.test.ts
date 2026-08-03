import { describe, expect, it } from "vitest";

import {
  GuideWorkflowError,
  runQuietPresenceDemo,
  type GuideDemoInput,
} from "./guide-client";

const input: GuideDemoInput = {
  projectName: "Northwind release workspace",
  knowledgeDocument: "# Release 2.4.0\nSecurity review must pass before deployment.",
  audience: "PRODUCT_LEADER",
  depth: "CONCISE",
  targetLanguage: "es",
  glossaryTerms: ["Northwind", "Release 2.4.0"],
};

function jsonResponse(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function successfulFetch() {
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
            { contextRefId: "context_001", citationIndex: 1 },
          ],
        },
        trace: { traceId: "trace_001" },
      },
      6: {
        multilingualRunId: "multilingual_001",
        sourceRunId: "run_001",
        targetLanguage: "es",
        translatedScriptText: "La revisión de seguridad sigue en curso. [1]",
        artifacts: {
          translatedScript: { checksum: "sha256:script" },
          subtitles: { checksum: "sha256:subtitles" },
          voiceManifest: { checksum: "sha256:voice" },
        },
        translationProvider: { provider: "mock", providerMode: "LOCAL" },
        voice: { provider: "mock", providerMode: "LOCAL" },
        trace: {
          sourceContextRefIds: ["context_001"],
          sourceCitationIndexes: [1],
          sourceEvaluationId: "evaluation_001",
          sourceEvaluationChecksum: "sha256:evaluation",
        },
      },
      7: {
        consentRecordId: "consent_001",
        consentStatementVersion: "stage7-synthetic-avatar-consent-v1",
        consentStatementText: "Synthetic presenter approved for this local demo.",
      },
      8: {
        avatarRenderId: "render_001",
        status: "COMPLETED",
        renderJobStatus: "COMPLETED",
        sourceScriptText: "The security review is still in progress. [1]",
        avatarProvider: { provider: "mock", providerMode: "LOCAL" },
        providerConfig: {
          providerMode: "LOCAL",
          allowNetworkEgress: false,
          supportsRealVideo: false,
        },
        disclosure: {
          consentStatus: "CONFIRMED",
          clonedIdentity: false,
          message: "Synthetic local presenter. No cloned identity.",
        },
      },
    };
    return jsonResponse(responses[position]);
  };
  return { calls, fetcher };
}

describe("runQuietPresenceDemo", () => {
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
      translation: "mock",
      voice: "mock",
      networkEgress: false,
      realMedia: false,
      clonedIdentity: false,
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
          message: "token=secret-value /private/customer/source.md",
        },
        500,
      );

    try {
      await runQuietPresenceDemo(input, fetcher);
      throw new Error("Expected the workflow to fail.");
    } catch (error) {
      expect(error).toBeInstanceOf(GuideWorkflowError);
      expect(error).toMatchObject({ code: "REQUEST_FAILED" });
      expect(String(error)).not.toContain("secret-value");
      expect(String(error)).not.toContain("/private/customer/source.md");
    }
  });
});
