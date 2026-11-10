import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import NotFound, { metadata } from "./not-found";

// Turns red: this page is removed, or it renders its own <title> element, which brings back issue #576's race.
describe("NotFound", () => {
  it("sets the 404 title only through metadata", () => {
    expect(metadata.title).toBe("404: This page could not be found.");
    const html = renderToStaticMarkup(<NotFound />);
    expect(html).not.toContain("<title");
    expect(html).toContain("404");
    expect(html).toContain("This page could not be found.");
  });
});
