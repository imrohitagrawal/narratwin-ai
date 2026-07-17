import { describe, expect, it } from "vitest";

type LighthouseRunner = {
  lighthouseChromePath(env: Record<string, string | undefined>, fallbackPath: string): string;
};

async function loadRunner(): Promise<LighthouseRunner> {
  return (await import(new URL("../../scripts/run-lighthouse.mjs", import.meta.url).href)) as LighthouseRunner;
}

describe("lighthouse runner", () => {
  it("honors an explicit Chrome path before using the Playwright fallback", async () => {
    const { lighthouseChromePath } = await loadRunner();

    expect(
      lighthouseChromePath(
        { CHROME_PATH: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" },
        "playwright-chromium",
      ),
    ).toBe("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome");
  });

  it("uses Playwright Chromium when Chrome path is not configured", async () => {
    const { lighthouseChromePath } = await loadRunner();

    expect(lighthouseChromePath({}, "playwright-chromium")).toBe("playwright-chromium");
    expect(lighthouseChromePath({ CHROME_PATH: "   " }, "playwright-chromium")).toBe("playwright-chromium");
  });
});
