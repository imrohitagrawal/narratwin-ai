import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import Home, { artifactHref } from "./page";

describe("Home", () => {
  it("renders the Stage 6 multilingual walkthrough workflow", () => {
    // The UI must expose trace/run_id metadata and source_chunk citation evidence
    // for generated script claims.
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("Multilingual walkthrough generation");
    expect(html).toContain("Generate multilingual walkthrough");
    expect(html).toContain("Target language");
    expect(html).toContain("Download script");
    expect(html).toContain("Download subtitles");
    expect(html).toContain("disabled=\"\"");
    expect(html).not.toContain("href=\"#\"");
    expect(html).toContain("Walkthrough script");
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
    });

    expect(href).toBe("");
  });
});
