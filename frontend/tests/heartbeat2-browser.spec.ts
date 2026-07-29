import { test, expect, type Request } from "@playwright/test";

test("Heartbeat 2 local reviewer demo", async ({ page }) => {
  const requestIds = new WeakMap<Request, string>();
  page.on("request", (request) => {
    requestIds.set(request, request.url());
    requests.push({ method: request.method(), body: request.postDataBuffer() });
  });
  page.on("response", async (response) => {
    const request = response.request();
    responses.push({ requestId: requestIds.get(request), status: response.status(), body: await response.body() });
  });
  const requests: Array<{ method: string; body: Buffer | null }> = [];
  const responses: Array<{ requestId: string | undefined; status: number; body: Buffer }> = [];
  await page.goto("/");
  await expect(page.getByTestId("h2-curation-panel")).toBeVisible();
  await expect(page.getByTestId("h2-generate-demo")).toBeDisabled();
  expect(requests.length).toBeGreaterThanOrEqual(1);
  expect(responses.length).toBeGreaterThanOrEqual(1);
});
