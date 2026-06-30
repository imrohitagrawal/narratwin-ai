import { expect, test } from "@playwright/test";

test("home page exposes the Stage 4 grounded script workflow", async ({ page }) => {
  // Browser smoke keeps source_chunk citation evidence visible in the result UI.
  const response = await page.goto("/");

  expect(response?.headers()["content-security-policy"]).toBe(
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
  );
  expect(response?.headers()["referrer-policy"]).toBe("no-referrer");
  expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");

  await expect(page.getByRole("heading", { name: "Grounded script generation" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Generate grounded script" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Walkthrough script" })).toBeVisible();
  await expect(page.getByLabel("Trace metadata")).toContainText("trace_stage4_local");
  await expect(page.getByText("0 unsupported claims")).toBeVisible();
  await expect(page.getByText("stage4_project.md").first()).toBeVisible();
});
