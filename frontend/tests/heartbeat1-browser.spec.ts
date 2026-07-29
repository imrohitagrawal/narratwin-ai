import { expect, test } from "@playwright/test";

test("H1-OUTCOME-01 exposes the owner-curation browser path", async ({ page }) => {
  const response = await page.goto("/");

  expect(response?.status()).toBe(200);
  await expect(page.getByRole("heading", { name: "Heartbeat 1 source curation" })).toBeVisible();
  await expect(page.getByTestId("h1-curation-panel")).toContainText("curator_demo");
  await expect(page.getByTestId("h1-public-file")).toHaveAttribute("type", "file");
  await expect(page.getByTestId("h1-internal-file")).toHaveAttribute("type", "file");
  await expect(page.getByTestId("h1-owner-actions")).toBeHidden();
});
