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

const failures = Object.entries(thresholds).filter(([category, threshold]) => {
  const score = report.categories?.[category]?.score;
  return typeof score !== "number" || score < threshold;
});

if (failures.length > 0) {
  for (const [category, threshold] of failures) {
    const score = report.categories?.[category]?.score;
    console.error(`Lighthouse ${category} score ${score} is below ${threshold}.`);
  }
  process.exit(1);
}
