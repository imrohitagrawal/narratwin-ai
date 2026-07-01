import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import Home, { artifactBlockReason, artifactHref, artifactSafetyState, sha256Hex } from "./page";

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
    expect(html).toContain("Video placeholder");
    expect(html).toContain("Real video");
    expect(html).toContain("Trace");
    expect(html).toContain("Run");
    expect(html).toContain("Generate a grounded script to display cited output.");
    expect(html).toContain("Citations will appear after generation.");
    expect(html).toContain("0 unsupported claims");
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
});
