import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { ESLint } from "eslint";
import { byteDigest, digest, loadProfile, parseStrict, requireValue, validateEffectiveConfiguration, verifyActualConfigurations } from "./frontend-security-profile.mjs";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const require = createRequire(join(root, "package.json"));
const p = loadProfile();
const deadline = setTimeout(() => { console.error("Frontend qualification timed out."); process.exitCode = 1; process.exit(1); }, p.verificationTimeoutSeconds * 1000);
try {
  requireValue(digest(parseStrict(readFileSync(join(root, "package.json"), "utf8"))) === p.manifestHash, "Frontend manifest drifted.");
  requireValue(digest(parseStrict(readFileSync(join(root, "package-lock.json"), "utf8"))) === p.lockHash, "Frontend lock drifted.");
  const pluginFile = require.resolve("@next/eslint-plugin-next/dist/utils/get-root-dirs.js");
  requireValue(byteDigest(readFileSync(pluginFile)) === p.rootDiscoverySourceSha256, "Published Next consumer was modified.");
  const pluginRequire = createRequire(pluginFile);
  const aliasFile = pluginRequire.resolve("fast-glob/package.json");
  const alias = parseStrict(readFileSync(aliasFile, "utf8"));
  requireValue(alias.name === "tinyglobby" && alias.version === p.packageVersions.tinyglobby, "Scoped glob alias identity invalid.");
  const eslint = new ESLint({ cwd: root });
  const actualFiles = await verifyActualConfigurations(root, eslint, p);
  for (const extension of Object.keys(p.effectiveConfigHashes)) {
    const config = await eslint.calculateConfigForFile(join(root, "src", "qualification." + extension));
    validateEffectiveConfiguration(config, extension, p);
    assert.throws(() => validateEffectiveConfiguration({ ...config, settings: { ...config.settings, next: { rootDir: "unqualified" } } }, extension, p), /rootDir/);
    assert.throws(() => validateEffectiveConfiguration({ ...config, rules: { ...config.rules, "@next/next/no-html-link-for-pages": [0] } }, extension, p), /drifted/);
  }
  const fixture = mkdtempSync(join(tmpdir(), "narratwin-eslint-canary-"));
  mkdirSync(join(fixture, "pages"));
  writeFileSync(join(fixture, "pages", "index.tsx"), "fixture");
  const canary = new ESLint({ cwd: fixture, overrideConfigFile: join(root, "eslint.config.mjs") });
  const bad = await canary.lintText('export default function Page(){return <a href="/">Home</a>}', { filePath: join(fixture, "pages", "index.tsx") });
  const good = await canary.lintText('import Link from "next/link"; export default function Page(){return <Link href="/">Home</Link>}', { filePath: join(fixture, "pages", "index.tsx") });
  requireValue(bad[0].messages.some((m) => m.ruleId === "@next/next/no-html-link-for-pages" && m.severity === 2), "Real Next rule canary did not detect the prohibited anchor.");
  requireValue(good[0].messages.every((m) => m.severity !== 2), "Real Next rule passing canary failed.");
  console.log(JSON.stringify({ outcome: "CURRENT_CONFIGURATION_QUALIFIED", actualFiles, effectiveConfigurationHashes: p.effectiveConfigHashes, rootDir: "UNQUALIFIED_AND_BLOCKED", publishedConsumerSha256: p.rootDiscoverySourceSha256, verificationTimeoutSeconds: p.verificationTimeoutSeconds, canaries: "PASS" }));
} finally {
  clearTimeout(deadline);
}
