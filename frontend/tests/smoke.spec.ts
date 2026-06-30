import { expect, test } from "@playwright/test";

test("home page exposes the Stage 3 foundation shell", async ({ page }) => {
  const response = await page.goto("/");

  expect(response?.headers()["content-security-policy"]).toBe(
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'",
  );
  expect(response?.headers()["referrer-policy"]).toBe("no-referrer");
  expect(response?.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");

  await expect(page.getByRole("heading", { name: "Repository foundation" })).toBeVisible();
  await expect(page.getByText("Feature work blocked until Stage 4")).toBeVisible();
});
