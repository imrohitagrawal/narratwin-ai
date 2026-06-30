import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("renders the Stage 3 foundation shell", () => {
    const html = renderToStaticMarkup(<Home />);

    expect(html).toContain("Repository foundation");
    expect(html).toContain("Next.js TypeScript scaffold");
    expect(html).toContain("Feature work blocked until Stage 4");
  });
});
