import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import QuietPresenceDemo from "./page";

describe("Quiet Presence demo", () => {
  it("renders the host project as the primary surface and NarraTwin as a truthful companion", () => {
    const html = renderToStaticMarkup(<QuietPresenceDemo />);

    expect(html).toContain("Release 2.4.0");
    expect(html).toContain("Security review");
    expect(html).toContain("NarraTwin");
    expect(html).toContain("AI project guide");
    expect(html).toContain("Run grounded demo");
    expect(html).toContain("Local mock");
    expect(html).toContain("Verified sources");
    expect(html).toContain("Synthetic presenter preview");
  });

  it("exposes theme and accessibility controls without claiming future capabilities", () => {
    const html = renderToStaticMarkup(<QuietPresenceDemo />);

    expect(html).toContain('aria-label="Switch to dark theme"');
    expect(html).toContain('aria-live="polite"');
    expect(html).toContain("Q&amp;A and governed web search are not enabled in this Cut 1");
    expect(html).not.toContain("Production ready");
    expect(html).not.toContain("Real avatar video");
    expect(html).not.toContain("Web search active");
  });
});
