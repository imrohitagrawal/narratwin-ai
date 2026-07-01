import { mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { chromium } from "playwright";

const targetUrl = process.argv[2] ?? "http://127.0.0.1:3000";
const reportPath = resolve(process.cwd(), "../reports/lighthouse/stage8-lighthouse.json");
mkdirSync(dirname(reportPath), { recursive: true });

const result = spawnSync(
  "npx",
  [
    "lighthouse",
    targetUrl,
    "--quiet",
    "--output=json",
    `--output-path=${reportPath}`,
    "--only-categories=performance,accessibility,best-practices,seo",
    "--chrome-flags=--headless=new --no-sandbox --disable-gpu",
  ],
  {
    cwd: process.cwd(),
    env: { ...process.env, CHROME_PATH: chromium.executablePath() },
    stdio: "inherit",
  },
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

const report = JSON.parse(readFileSync(reportPath, "utf8"));
const thresholds = {
  performance: 0.8,
  accessibility: 0.9,
  "best-practices": 0.9,
  seo: 0.8,
};
const auditThresholds = {
  "largest-contentful-paint": 2500,
  "cumulative-layout-shift": 0.1,
  "total-blocking-time": 300,
  "interactive": 3500,
  "total-byte-weight": 750_000,
  "network-requests": 80,
};

const categoryFailures = Object.entries(thresholds).filter(([category, threshold]) => {
  const score = report.categories?.[category]?.score;
  return typeof score !== "number" || score < threshold;
});

function auditBudgetValue(auditId) {
  const audit = report.audits?.[auditId];
  if (auditId === "network-requests") {
    return audit?.details?.items?.length;
  }
  return audit?.numericValue;
}

const auditFailures = Object.entries(auditThresholds).filter(([auditId, threshold]) => {
  const value = auditBudgetValue(auditId);
  return typeof value !== "number" || value > threshold;
});

if (categoryFailures.length > 0 || auditFailures.length > 0) {
  for (const [category, threshold] of categoryFailures) {
    const score = report.categories?.[category]?.score;
    console.error(`Lighthouse ${category} score ${score} is below ${threshold}.`);
  }
  for (const [auditId, threshold] of auditFailures) {
    const value = auditBudgetValue(auditId);
    console.error(`Lighthouse ${auditId} value ${value} exceeds ${threshold}.`);
  }
  process.exit(1);
}
