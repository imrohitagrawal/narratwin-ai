import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import Home, {
  artifactBlockReason,
  artifactHref,
  artifactSafetyState,
  evaluationBadgeLabel,
  readJson,
  sha256Hex,
} from "./page";

describe("Home", () => {
  it("renders the Stage 7 avatar export workflow", () => {
    // The UI must expose trace/run_id metadata and source_chunk citation evidence
    // for generated script claims.
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("Avatar demo export");
    expect(html).toContain("Generate avatar demo export");
    expect(html).toContain("Target language");
    expect(html).toContain("Download script");
    expect(html).toContain("Download subtitles");
    expect(html).toContain("Download voice manifest");
    expect(html).toContain("Download avatar demo");
    expect(html).toContain("Download render manifest");
    expect(html).toContain("Download video placeholder");
    expect(html).toContain("Synthetic avatar consent: local AI presenter, no cloned face or voice");
    expect(html).toContain("aria-busy=\"false\"");
    expect(html).not.toContain("checked=\"\"");
    expect(html).toContain("disabled=\"\"");
    expect(html).toContain("aria-label=\"Download export artifact Video placeholder\"");
    expect(html).not.toContain("href=\"#\"");
    expect(html).toContain("Walkthrough script");
    expect(html).toContain("Demo preview");
    expect(html).toContain("Export artifacts");
    expect(html).toContain("Voice manifest");
    expect(html).toContain("Video placeholder");
    expect(html).toContain("Real video");
    expect(html).toContain("Trace");
    expect(html).toContain("Run");
    expect(html).toContain("Generate a grounded script to display cited output.");
    expect(html).toContain("Citations will appear after generation.");
    expect(html).toContain("Evaluation pending");
    expect(html).not.toContain("0 unsupported claims");
  });

  it("shows unsupported claim counts only after evaluation evidence exists", () => {
    expect(evaluationBadgeLabel(null)).toBe("Evaluation pending");
    expect(
      evaluationBadgeLabel({
        runId: "run_001",
        status: "COMPLETED",
        acceptedScriptText: "Grounded script",
        contextRefs: [],
        trace: { traceId: "trace_001" },
        evaluation: {
          unsupportedClaimCount: 0,
          claimSupports: [],
        },
      }),
    ).toBe("0 unsupported claims");
  });

  it("does not echo unsafe API error messages even for allowlisted codes", async () => {
    const response = new Response(
      JSON.stringify({
        error: {
          code: "UNSAFE_URL",
          message: "raw script canary session_001 idem_001 contentBase64 provider payload",
        },
      }),
      { status: 422 },
    );

    await expect(readJson(response)).rejects.toThrow("NarraTwin API request failed with 422");
  });

  it("rejects unsafe artifact filenames before enabling downloads", () => {
    const href = artifactHref("script", {
      fileName: "../run-es-script.md",
      mimeType: "text/markdown",
      contentBase64: "U3RhZ2UgNiBzY3JpcHQ=",
      checksum: `sha256:${sha256Hex("Stage 6 script")}`,
    });

    expect(href).toBe("");
  });

  it("distinguishes blocked artifacts from pending artifacts", () => {
    expect(artifactSafetyState("script")).toBe("pending");
    expect(
      artifactSafetyState("script", {
        fileName: "../run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: "U3RhZ2UgNiBzY3JpcHQ=",
        checksum: `sha256:${sha256Hex("Stage 6 script")}`,
      }),
    ).toBe("blocked");
    expect(
      artifactBlockReason("script", {
        fileName: "../run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: "U3RhZ2UgNiBzY3JpcHQ=",
        checksum: `sha256:${sha256Hex("Stage 6 script")}`,
      }),
    ).toBe("Unsafe filename.");
  });

  it("enables downloads only after checksum and content validation pass", () => {
    const text = "Stage 6 script";
    expect(
      artifactHref("script", {
        fileName: "run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: btoa(text),
        checksum: `sha256:${sha256Hex(text)}`,
      }),
    ).toContain("data:text/markdown;base64,");
    expect(
      artifactSafetyState("script", {
        fileName: "run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: btoa(text),
        checksum: "sha256:wrong",
      }),
    ).toBe("blocked");
    expect(
      artifactBlockReason("script", {
        fileName: "run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: btoa(text),
        checksum: "sha256:wrong",
      }),
    ).toBe("Checksum mismatch.");
  });

  it("blocks artifact MIME type and extension mismatches", () => {
    const text = "Stage 6 script";

    expect(
      artifactBlockReason("script", {
        fileName: "run-es-script.md",
        mimeType: "text/plain",
        contentBase64: btoa(text),
        checksum: `sha256:${sha256Hex(text)}`,
      }),
    ).toBe("Unexpected MIME type.");
    expect(
      artifactBlockReason("script", {
        fileName: "run-es-script.txt",
        mimeType: "text/markdown",
        contentBase64: btoa(text),
        checksum: `sha256:${sha256Hex(text)}`,
      }),
    ).toBe("Unexpected file extension.");
  });

  it("does not block inert web terms inside escaped avatar demo text", () => {
    const html =
      "<!doctype html><html><body><article>CSS modules, src=, href=, and url() are project prose.</article></body></html>";

    expect(
      artifactSafetyState("avatarDemo", {
        fileName: "run-avatar-demo.html",
        mimeType: "text/html",
        contentBase64: btoa(html),
        checksum: `sha256:${sha256Hex(html)}`,
      }),
    ).toBe("ready");
  });

  it("blocks malformed, active, invalid JSON, and oversized artifacts", () => {
    const html = "<html><body><script>alert('x')</script></body></html>";
    expect(
      artifactBlockReason("avatarDemo", {
        fileName: "run-avatar-demo.html",
        mimeType: "text/html",
        contentBase64: btoa(html),
        checksum: `sha256:${sha256Hex(html)}`,
      }),
    ).toBe("HTML export contains active content.");
    const json = "{}";
    expect(
      artifactBlockReason("renderManifest", {
        fileName: "run-avatar-render-manifest.json",
        mimeType: "application/json",
        contentBase64: btoa(json),
        checksum: `sha256:${sha256Hex(json)}`,
      }),
    ).toBe("JSON metadata shape is invalid.");
    expect(
      artifactBlockReason("script", {
        fileName: "run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: "not base64?",
        checksum: "sha256:wrong",
      }),
    ).toBe("Invalid base64 content.");
    const oversized = "x".repeat(512 * 1024 + 1);
    expect(
      artifactBlockReason("script", {
        fileName: "run-es-script.md",
        mimeType: "text/markdown",
        contentBase64: btoa(oversized),
        checksum: `sha256:${sha256Hex(oversized)}`,
      }),
    ).toBe("Artifact exceeds local preview limit.");
  });

  it("blocks JSON artifacts when language or provenance does not match the current run", () => {
    const context = artifactValidationContext();
    const renderManifest = jsonArtifact(
      "run-avatar-render-manifest.json",
      "renderManifest",
      manifestJson(context, { targetLanguage: "fr" }),
    );
    const videoPlaceholder = jsonArtifact(
      "run-video-export-placeholder.json",
      "videoPlaceholder",
      placeholderJson(context, { sourceRunId: "run_replayed" }),
    );
    const voiceManifest = jsonArtifact(
      "voice-manifest-es.json",
      "voiceManifest",
      voiceManifestJson(context, {
        textChecksum: "sha256:tampered",
      }),
    );

    expect(artifactBlockReason("renderManifest", renderManifest, context)).toBe("JSON metadata shape is invalid.");
    expect(artifactBlockReason("videoPlaceholder", videoPlaceholder, context)).toBe("JSON metadata shape is invalid.");
    expect(artifactBlockReason("voiceManifest", voiceManifest, context)).toBe(
      "JSON metadata shape is invalid.",
    );
  });

  it("blocks voice manifests that omit required local schema fields", () => {
    const context = artifactValidationContext();
    const voiceManifest = jsonArtifact("voice-manifest-es.json", "voiceManifest", {
      provider: "mock",
      providerMode: "LOCAL",
      language: "es",
    });

    expect(artifactBlockReason("voiceManifest", voiceManifest, context)).toBe("JSON metadata shape is invalid.");
  });

  it("enables JSON artifact downloads only when language and provenance match the current run", () => {
	    const context = artifactValidationContext();
	    const renderManifest = jsonArtifact("run-avatar-render-manifest.json", "renderManifest", manifestJson(context));
	    const videoPlaceholder = jsonArtifact(
	      "run-video-export-placeholder.json",
	      "videoPlaceholder",
	      placeholderJson(context),
	    );
    const voiceManifest = jsonArtifact("voice-manifest-es.json", "voiceManifest", voiceManifestJson(context));

	    expect(artifactSafetyState("renderManifest", renderManifest, context)).toBe("ready");
	    expect(artifactSafetyState("videoPlaceholder", videoPlaceholder, context)).toBe("ready");
	    expect(artifactSafetyState("voiceManifest", voiceManifest, context)).toBe("ready");
	  });
	});

function artifactValidationContext(): NonNullable<Parameters<typeof artifactSafetyState>[2]> {
  const translatedScriptText = "Guion traducido. [1]";
  const subtitlesText = "1\n00:00:00,000 --> 00:00:02,000\nGuion traducido. [1]\n";
  const voiceManifestText = JSON.stringify({
    provider: "mock",
    providerMode: "LOCAL",
    language: "es",
    languageDisplayName: "Spanish",
    textChecksum: `sha256:${sha256Hex(translatedScriptText)}`,
    durationSecondsEstimate: 2,
    mockAudioProfile: {
      durationMillisecondsEstimate: 2000,
      sampleRateHz: 16000,
      channels: 1,
    },
    disclosure: "Mock local TTS placeholder. No cloned voice or paid provider was used.",
  });
  return {
    multilingualRun: {
	      multilingualRunId: "mlrun_test",
	      status: "COMPLETED",
	      sourceRunId: "run_test",
	      sourceLanguage: "en",
	      targetLanguage: "es",
      translatedScriptText,
      subtitlesText,
	      preservedTerms: ["NarraTwin AI"],
	      voice: { provider: "mock", providerMode: "LOCAL", requestedProvider: "mock" },
	      translationProvider: { provider: "mock", providerMode: "LOCAL" },
	      artifacts: {
        translatedScript: artifactFromText("run_test-es-script.md", "text/markdown", translatedScriptText),
        subtitles: artifactFromText(
          "run_test-es.srt",
          "application/x-subrip",
          subtitlesText,
        ),
        voiceManifest: artifactFromText(
          "voice-manifest-es.json",
          "application/json",
          voiceManifestText,
        ),
	      },
	      trace: {
	        sourceContextRefIds: ["ctx_001"],
	        sourceCitationIndexes: [1],
	        sourceEvaluationId: "eval_001",
	        sourceEvaluationChecksum: "sha256:evaluation",
	      },
	    },
	    avatarRender: {
	      avatarRenderId: "avatar_001",
	      consentRecordId: "consent_001",
	      sourceRunId: "run_test",
	      status: "COMPLETED",
	      renderJobStatus: "COMPLETED",
	      renderJobStatusHistory: [{ status: "COMPLETED", message: "Complete." }],
	      sourceScriptText: "Guion traducido. [1]",
	      avatarProvider: { provider: "mock", providerMode: "LOCAL", requestedProvider: "mock" },
	      providerConfig: {
	        provider: "mock",
	        providerMode: "LOCAL",
	        adapterKind: "MOCK_LOCAL",
	        allowNetworkEgress: false,
	        requiresApiKey: false,
	        supportsRealVideo: false,
	        supportsClonedIdentity: false,
	      },
	      videoRenderer: { renderer: "local-html", exportFormat: "html" },
	      disclosure: {
	        aiGenerated: true,
	        clonedIdentity: false,
	        consentStatus: "CONFIRMED",
	        message: "Synthetic local avatar demo.",
	      },
	      artifacts: {
	        demoExport: artifactFromText("run_test-avatar-demo.html", "text/html", "<!doctype html><html><body></body></html>"),
	        renderManifest: artifactFromText("run_test-avatar-render-manifest.json", "application/json", "{}"),
	        videoExportPlaceholder: artifactFromText("run_test-video-export-placeholder.json", "application/json", "{}"),
	      },
	      trace: {
	        traceId: "trace_001",
	        sourceCitationCount: 1,
	        sourceContextRefIds: ["ctx_001"],
	        sourceCitationIndexes: [1],
	        sourceEvaluationId: "eval_001",
	        sourceEvaluationChecksum: "sha256:evaluation",
	        evaluationStatus: "PASSED",
	        multilingualRunId: "mlrun_test",
	        targetLanguage: "es",
        translatedScriptChecksum: `sha256:${sha256Hex(translatedScriptText)}`,
        subtitlesChecksum: `sha256:${sha256Hex(subtitlesText)}`,
        voiceManifestChecksum: `sha256:${sha256Hex(voiceManifestText)}`,
	      },
	    },
	  };
	}

	function artifactFromText(fileName: string, mimeType: string, text: string) {
	  return {
	    fileName,
	    mimeType,
	    contentBase64: btoa(text),
	    checksum: `sha256:${sha256Hex(text)}`,
	  };
	}

	function jsonArtifact(fileName: string, kind: "renderManifest" | "videoPlaceholder" | "voiceManifest", value: object) {
	  return artifactFromText(fileName, "application/json", JSON.stringify(value));
	}

	function manifestJson(
	  context: NonNullable<Parameters<typeof artifactSafetyState>[2]>,
	  bundleOverride: Record<string, unknown> = {},
	) {
	  return {
	    schema: "Stage7AvatarRenderManifest",
	    providerConfig: providerConfigJson(),
	    source: sourceJson(context),
	    multilingualBundle: bundleJson(context, bundleOverride),
	  };
	}

function placeholderJson(
	  context: NonNullable<Parameters<typeof artifactSafetyState>[2]>,
	  bundleOverride: Record<string, unknown> = {},
	) {
	  return {
	    schema: "Stage7VideoExportPlaceholder",
	    realVideoProduced: false,
	    providerConfig: providerConfigJson(),
	    source: sourceJson(context),
	    multilingualBundle: bundleJson(context, bundleOverride),
	  };
}

function voiceManifestJson(
  context: NonNullable<Parameters<typeof artifactSafetyState>[2]>,
  override: Record<string, unknown> = {},
) {
  return {
    provider: "mock",
    providerMode: "LOCAL",
    language: context.multilingualRun?.targetLanguage,
    languageDisplayName: "Spanish",
    textChecksum: context.multilingualRun?.artifacts.translatedScript.checksum,
    durationSecondsEstimate: 2,
    mockAudioProfile: {
      durationMillisecondsEstimate: 2000,
      sampleRateHz: 16000,
      channels: 1,
    },
    disclosure: "Mock local TTS placeholder. No cloned voice or paid provider was used.",
    ...override,
  };
}

	function providerConfigJson() {
	  return {
	    provider: "mock",
	    providerMode: "LOCAL",
	    allowNetworkEgress: false,
	    requiresApiKey: false,
	    supportsRealVideo: false,
	    supportsClonedIdentity: false,
	  };
	}

	function sourceJson(context: NonNullable<Parameters<typeof artifactSafetyState>[2]>) {
	  return {
	    runId: context.avatarRender?.sourceRunId,
	    contextRefIds: context.avatarRender?.trace.sourceContextRefIds,
	    citationIndexes: context.avatarRender?.trace.sourceCitationIndexes,
	    evaluationId: context.avatarRender?.trace.sourceEvaluationId,
	    evaluationChecksum: context.avatarRender?.trace.sourceEvaluationChecksum,
	  };
	}

	function bundleJson(
	  context: NonNullable<Parameters<typeof artifactSafetyState>[2]>,
	  override: Record<string, unknown> = {},
	) {
	  const multilingual = context.multilingualRun;
	  return {
	    sourceRunId: multilingual?.sourceRunId,
	    multilingualRunId: multilingual?.multilingualRunId,
	    targetLanguage: multilingual?.targetLanguage,
	    translatedScriptChecksum: multilingual?.artifacts.translatedScript.checksum,
	    subtitlesChecksum: multilingual?.artifacts.subtitles.checksum,
	    voiceManifestChecksum: multilingual?.artifacts.voiceManifest.checksum,
	    contextRefIds: multilingual?.trace.sourceContextRefIds,
	    citationIndexes: multilingual?.trace.sourceCitationIndexes,
	    evaluationId: multilingual?.trace.sourceEvaluationId,
	    evaluationChecksum: multilingual?.trace.sourceEvaluationChecksum,
	    providerPosture: {
	      translationProvider: multilingual?.translationProvider.provider,
	      translationProviderMode: multilingual?.translationProvider.providerMode,
	      voiceProvider: multilingual?.voice.provider,
	      voiceProviderMode: multilingual?.voice.providerMode,
	    },
	    ...override,
	  };
	}
