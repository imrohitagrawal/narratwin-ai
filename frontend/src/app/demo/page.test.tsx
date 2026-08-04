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
    expect(html).toContain("create a local synthetic presenter preview");
    expect(html).toContain('data-hydrated="false"');
    expect(html).toContain('<input type="checkbox" disabled=""');
    expect(html).toContain("Simulated host context");
    expect(html).toContain("narratwin-synthetic-presenter.webp");
    expect(html).toContain('role="img"');
    expect(html).toContain('aria-label="Search Northwind preview"');
    expect(html).not.toContain('<input placeholder="Search Northwind"');
    expect(html).not.toContain('style="color:transparent"');
  });

  it("exposes theme and accessibility controls without claiming future capabilities", () => {
    const html = renderToStaticMarkup(<QuietPresenceDemo />);

    expect(html).toContain('aria-label="Switch to dark theme"');
    expect(html).toContain('aria-label="Minimize guide"');
    expect(html).toContain('aria-label="Expand focus"');
    expect(html).toContain("Back to project");
    expect(html).toContain("External web disabled by policy");
    expect(html).toContain("Ask next · planned");
    expect(html).toContain('aria-live="polite"');
    expect(html).toContain("Captions on");
    expect(html).toContain("Q&amp;A and governed web search are not enabled in this Cut 1");
    expect(html).toContain("no external provider calls");
    expect(html).not.toContain("No network egress");
    expect(html).not.toContain("Production ready");
    expect(html).not.toContain("Real avatar video");
    expect(html).not.toContain("Web search active");
    expect(html).not.toContain(">Pause<");
  });

  it("ships one shared ribbon, focus-stage, and mobile-guide content model", () => {
    const html = renderToStaticMarkup(<QuietPresenceDemo />);

    expect(html).toContain('data-guide-state="expanded"');
    expect(html).toContain('data-mobile-guide="open"');
    expect(html).toContain("Simulated host context");
    expect(html).toContain("Synthetic presenter preview · still image");
    expect(html).not.toContain("speaking avatar");
  });
});
