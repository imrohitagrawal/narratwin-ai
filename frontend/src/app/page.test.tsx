import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("renders the Stage 4 grounded script workflow", () => {
    // The UI must expose source_chunk citation evidence for generated script claims.
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("Grounded script generation");
    expect(html).toContain("Generate grounded script");
    expect(html).toContain("Walkthrough script");
    expect(html).toContain("trace_stage4_local");
    expect(html).toContain("0 unsupported claims");
    expect(html).toContain("stage4_project.md");
  });
});
