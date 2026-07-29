import { expect, test, type Page } from "@playwright/test";
import { mkdir, readFile, unlink, writeFile } from "node:fs/promises";
import path from "node:path";

type Handoff = { runId: string; projectId: string; publicIdentity: string[]; exclusionIdentity: string[]; acceptedChunks: string[]; summary: string };
type Net = { method: string; path: string; origin: string; status?: number };
const phase = process.env.NARRATWIN_HEARTBEAT1_PHASE;
const runId = process.env.NARRATWIN_HEARTBEAT1_RUN_ID ?? "";
const handoffPath = process.env.NARRATWIN_HEARTBEAT1_HANDOFF ?? "";
const candidateDir = process.env.NARRATWIN_HEARTBEAT1_CANDIDATE_DIR ?? "";

test.skip(!phase, "dedicated Heartbeat 1 runner only");
test("Heartbeat 1B real browser submit and restart/reopen", async ({ page, context }) => {
  if (!runId || !handoffPath || !candidateDir) fail("H1_ENV_MISSING");
  const net = observeMetadata(page);
  if (phase === "submit") {
    await submitPhase(page, net);
    return;
  }
  if (phase !== "reopen") fail("H1_PHASE_INVALID");
  const handoff = await safeReadHandoff();
  try { await mkdir(candidateDir, { recursive: true }); await context.tracing.start({ screenshots: true, snapshots: true, sources: false }); }
  catch { fail("H1_EVIDENCE_SETUP_FAILED"); }
  let reopenFailed = false;
  try {
    await page.goto("/");
    await page.getByTestId("h1-project-id").fill(handoff.projectId);
    await page.getByTestId("h1-reopen-project").click();
    await expect(page.getByTestId("h1-summary")).toBeVisible();
    const reopenedSummary = await page.getByTestId("h1-summary").innerText();
    expect(reopenedSummary).toBe(handoff.summary);
    const reopenedChunks = await page.getByTestId("h1-accepted-chunk").allInnerTexts();
    if (await page.getByTestId("h1-curated-item").getAttribute("data-identity") !== handoff.publicIdentity.join("|") || await page.getByTestId("h1-excluded-item").getAttribute("data-identity") !== handoff.exclusionIdentity.join("|") || JSON.stringify(reopenedChunks) !== JSON.stringify(handoff.acceptedChunks)) fail("H1_REOPEN_IDENTITY_MISMATCH");
    await writeFile(path.join(candidateDir, "reopen-owner-dom.txt"), await page.locator("body").innerText(), "utf8");
    await page.screenshot({ path: path.join(candidateDir, "reopen-owner.png"), fullPage: true });
    await page.getByTestId("h1-principal").selectOption("other_demo");
    await expect(page.getByTestId("h1-owner-actions")).toBeHidden();
    await expect(page.getByTestId("h1-submit-public")).toBeHidden();
    await expect(page.getByTestId("h1-submit-internal")).toBeHidden();
    await expect(page.getByTestId("h1-create-project")).toBeHidden();
    await page.getByTestId("h1-reopen-project").click();
    await expect(page.getByTestId("h1-safe-error")).toHaveText("FORBIDDEN");
    await expect(page.getByTestId("h1-reopen-project")).toBeHidden();
    await expect(page.getByTestId("h1-summary")).toHaveCount(0);
    if (!net.some((entry) => entry.method === "GET" && entry.path.endsWith("/source-curation-summary") && entry.status === 403)) fail("H1_AUTHZ_RESPONSE_MISSING");
    if (net.some((entry) => entry.origin !== new URL(page.url()).origin)) fail("H1_PROXY_BYPASS");
    const dom = await page.locator("body").innerText();
    await writeFile(path.join(candidateDir, "reopen-dom.txt"), dom, "utf8");
    await page.screenshot({ path: path.join(candidateDir, "reopen.png"), fullPage: true });
    await writeFile(path.join(candidateDir, "browser-result.json"), JSON.stringify({ runId, phase, projectId: handoff.projectId, net }) + "\n", "utf8");
  } catch { reopenFailed = true; } finally {
    try { await context.tracing.stop({ path: path.join(candidateDir, "reopen-trace.zip") }); }
    catch { fail("H1_TRACE_STOP_FAILED"); }
  }
  if (reopenFailed) fail("H1_REOPEN_PHASE_FAILED");
});

async function submitPhase(page: Page, net: Net[]) {
  const publicFile = required(process.env.NARRATWIN_HEARTBEAT1_PUBLIC_FILE);
  const internalFile = required(process.env.NARRATWIN_HEARTBEAT1_INTERNAL_FILE);
  await page.goto("/");
  await page.getByTestId("h1-create-project").click();
  await expect(page.getByTestId("h1-project-id")).not.toHaveValue("");
  let submissionFailed = false;
  try {
    await page.getByTestId("h1-public-file").setInputFiles(publicFile);
    const publicResponse = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/knowledge-documents"));
    await page.getByTestId("h1-submit-public").click();
    if ((await publicResponse).status() !== 201) submissionFailed = true;
    await page.getByTestId("h1-internal-file").setInputFiles(internalFile);
    const internalResponse = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname.endsWith("/knowledge-documents"));
    await page.getByTestId("h1-submit-internal").click();
    if ((await internalResponse).status() !== 201) submissionFailed = true;
  } catch { submissionFailed = true; }
  try { await Promise.all([unlink(publicFile), unlink(internalFile)]); } catch { fail("H1_FIXTURE_DELETE_FAILED"); }
  if (submissionFailed) fail("H1_CONTROLLED_SUBMISSION_FAILED");
  await expect(page.getByTestId("h1-public-status")).toContainText("SOURCE_PENDING_REVIEW");
  await expect(page.getByTestId("h1-exclusion-status")).toContainText("SOURCE_EXCLUDED EXCLUDED retained=false");
  const submits = net.filter((entry) => entry.method === "POST" && entry.path.endsWith("/knowledge-documents"));
  if (submits.length !== 2 || submits.some((entry) => entry.status !== 201)) fail("H1_SUBMISSION_COUNT_INVALID");
  if (net.filter((entry) => entry.method === "POST" && entry.path === "/api/v1/projects").length !== 1) fail("H1_PROJECT_COUNT_INVALID");
  await page.getByTestId("h1-approve-source").click();
  await expect(page.getByTestId("h1-public-status")).toContainText("SOURCE_APPROVED");
  await page.getByTestId("h1-ingest-source").click();
  await expect(page.getByTestId("h1-summary")).toBeVisible();
  await expect(page.getByTestId("h1-curated-item")).toHaveCount(1);
  await expect(page.getByTestId("h1-excluded-item")).toHaveCount(1);
  expect(await page.getByTestId("h1-accepted-chunk").count()).toBeGreaterThan(0);
  const publicIdentity = await Promise.all(["h1-public-source-id", "h1-public-checksum", "h1-public-version"].map((id) => page.getByTestId(id).innerText()));
  const exclusionIdentity = await Promise.all(["h1-exclusion-decision-id", "h1-exclusion-checksum"].map((id) => page.getByTestId(id).innerText()));
  const acceptedChunks = await page.getByTestId("h1-accepted-chunk").allInnerTexts();
  const summary = await page.getByTestId("h1-summary").innerText();
  if (await page.getByTestId("h1-curated-item").getAttribute("data-identity") !== publicIdentity.join("|") || await page.getByTestId("h1-excluded-item").getAttribute("data-identity") !== exclusionIdentity.join("|") || !acceptedChunks.length) fail("H1_SUBMIT_IDENTITY_MISMATCH");
  if (net.some((entry) => entry.origin !== new URL(page.url()).origin)) fail("H1_PROXY_BYPASS");
  const handoff: Handoff = {
    runId, projectId: await page.getByTestId("h1-project-id").inputValue(),
    publicIdentity, exclusionIdentity, acceptedChunks, summary,
  };
  try {
    await writeFile(handoffPath, JSON.stringify(handoff) + "\n", { encoding: "utf8", mode: 0o600 });
    await writeFile(path.join(candidateDir, "submit-result.json"), JSON.stringify({
      runId, phase, projectId: handoff.projectId, controlledSubmissionCount: submits.length,
      projectCreateCount: net.filter((entry) => entry.method === "POST" && entry.path === "/api/v1/projects").length, net,
    }) + "\n", { encoding: "utf8", mode: 0o600 });
  } catch { fail("H1_SUBMIT_EVIDENCE_WRITE_FAILED"); }
}

function observeMetadata(page: Page) {
  const entries: Net[] = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname.startsWith("/api/v1/")) entries.push({ method: request.method(), path: url.pathname, origin: url.origin });
  });
  page.on("response", (response) => {
    const url = new URL(response.url());
    const entry = [...entries].reverse().find((value) => value.path === url.pathname && value.status === undefined);
    if (entry) entry.status = response.status();
  });
  return entries;
}

async function safeReadHandoff() {
  try {
    const value = JSON.parse(await readFile(handoffPath, "utf8")) as Handoff;
    if (value.runId !== runId || !/^proj_[0-9]{6}$/.test(value.projectId) || value.publicIdentity.length !== 3 || !/^source_[0-9]{6}$/.test(value.publicIdentity[0]) || !/^[0-9a-f]{64}$/.test(value.publicIdentity[1]) || value.publicIdentity[2] !== "heartbeat1-public-v1" || value.exclusionIdentity.length !== 2 || !/^decision_[0-9]{6}$/.test(value.exclusionIdentity[0]) || !/^[0-9a-f]{64}$/.test(value.exclusionIdentity[1]) || !value.acceptedChunks.length || value.acceptedChunks.some((item) => !/^chunk_[0-9a-f]{16}:sha256:[0-9a-f]{64}$/.test(item)) || !value.summary) fail("H1_HANDOFF_INVALID");
    return value;
  } catch { fail("H1_HANDOFF_INVALID"); }
}

function required(value: string | undefined) { if (!value) fail("H1_ENV_MISSING"); return value; }
function fail(code: string): never { throw new Error(code); }
