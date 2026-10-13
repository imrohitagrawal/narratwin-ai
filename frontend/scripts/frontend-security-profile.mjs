import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { extname, join, relative, sep } from "node:path";

export const profileURL = new URL("../../docs/security/FRONTEND_DEPENDENCY_REFRESH.json", import.meta.url);
const fields = "schemaVersion baseSha manifestHash lockHash recordHashes removedRecords effectiveConfigHashes baselineConfigsSha256 rootDiscoverySourceSha256 verificationTimeoutSeconds buildArchives sharpVersion libvipsVersion runtimePackages packageVersions".split(" ");
const extensions = ["ts", "tsx", "js", "jsx", "mjs", "cjs"];
const packages = ["next", "eslint-config-next", "brace-expansion", "sharp", "source-map-js", "tinyglobby"];
const archives = ["npm", "brace-expansion", "ip-address", "tar", "undici", "http-cache-semantics"];
const runtime = ["alpine-keys", "alpine-release", "ca-certificates-bundle", "libgcc", "libstdc++", "musl"];
export function requireValue(condition, message) {
  if (!condition) throw new Error(message);
}
function keys(value, expected) {
  return value !== null && typeof value === "object" && !Array.isArray(value) &&
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...expected].sort());
}
export function parseStrict(raw) {
  const lexemes = raw.match(/"(?:\\.|[^"\\])*"|[{}\[\]:]/g) ?? [];
  const stack = [];
  for (let i = 0; i < lexemes.length; i++) {
    const lexeme = lexemes[i];
    if (lexeme === "{") stack.push(new Set());
    else if (lexeme === "[") stack.push(null);
    else if (lexeme === "}" || lexeme === "]") stack.pop();
    else if (lexeme.startsWith('"') && lexemes[i + 1] === ":") {
      const key = JSON.parse(lexeme), owner = stack.at(-1);
      requireValue(owner instanceof Set && !owner.has(key), "Duplicate or malformed frontend JSON key.");
      owner.add(key);
    }
  }
  return JSON.parse(raw);
}
export function canonical(value) {
  if (value && typeof value === "object") {
    return Array.isArray(value) ? value.map(canonical) : Object.fromEntries(
      Object.keys(value).sort().map((key) => [key, canonical(value[key])]),
    );
  }
  return value;
}
export const digest = (value) => createHash("sha256").update(JSON.stringify(canonical(value))).digest("hex");
export const byteDigest = (bytes) => createHash("sha256").update(bytes).digest("hex");
export function loadProfile(url = profileURL) {
  const p = parseStrict(readFileSync(url, "utf8"));
  const hash = (value) => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
  const version = (value) => typeof value === "string" && /^[0-9]+\.[0-9]+\.[0-9]+$/.test(value);
  requireValue(keys(p, fields) && p.schemaVersion === 1 && /^[0-9a-f]{40}$/.test(p.baseSha), "Frontend profile schema invalid.");
  for (const key of ["manifestHash", "lockHash", "baselineConfigsSha256", "rootDiscoverySourceSha256"]) requireValue(hash(p[key]), "Frontend hash invalid.");
  requireValue(Number.isSafeInteger(p.verificationTimeoutSeconds) && p.verificationTimeoutSeconds > 0 && p.verificationTimeoutSeconds <= 2147483, "Frontend verification timeout invalid.");
  requireValue(version(p.sharpVersion) && version(p.libvipsVersion), "Frontend native version invalid.");
  requireValue(keys(p.packageVersions, packages) && Object.values(p.packageVersions).every(version) && p.packageVersions.sharp === p.sharpVersion, "Frontend package policy invalid.");
  requireValue(keys(p.effectiveConfigHashes, extensions) && Object.values(p.effectiveConfigHashes).every(hash), "Frontend configuration hashes invalid.");
  requireValue(p.recordHashes && typeof p.recordHashes === "object" && !Array.isArray(p.recordHashes) && Object.keys(p.recordHashes).length > 0 && Object.entries(p.recordHashes).every(([key, value]) => (!key || key.startsWith("node_modules/")) && !key.split("/").includes("..") && hash(value)), "Frontend record policy invalid.");
  requireValue(Array.isArray(p.removedRecords) && p.removedRecords.length > 0 && p.removedRecords.every((key) => typeof key === "string" && key.startsWith("node_modules/")) && new Set(p.removedRecords).size === p.removedRecords.length && p.removedRecords.every((key) => !(key in p.recordHashes)), "Frontend removed records invalid.");
  requireValue(keys(p.buildArchives, archives), "Frontend build archives invalid.");
  for (const row of Object.values(p.buildArchives)) requireValue(keys(row, ["version", "sha256", "sha512"]) && version(row.version) && hash(row.sha256) && typeof row.sha512 === "string" && /^[0-9a-f]{128}$/.test(row.sha512), "Frontend archive identity invalid.");
  requireValue(keys(p.runtimePackages, runtime) && Object.values(p.runtimePackages).every((value) => typeof value === "string" && /^[0-9.]+-r[0-9]+$/.test(value)), "Frontend runtime packages invalid.");
  return p;
}
export function validateEffectiveConfiguration(config, extension, p) {
  requireValue(config && config.rules && config.languageOptions?.parser?.meta, "Effective ESLint configuration missing or ignored.");
  requireValue(config.settings?.next?.rootDir === undefined, "Custom next.rootDir is unqualified; current lint configuration only.");
  const actual = { rules: config.rules, settings: config.settings ?? {}, parser: config.languageOptions.parser.meta };
  requireValue(digest(actual) === p.effectiveConfigHashes[extension], "Effective ESLint rules, options, parser or settings drifted.");
  return actual;
}
export async function verifyActualConfigurations(root, eslint, p) {
  let actualFiles = 0;
  for (const entry of readdirSync(root, { recursive: true, withFileTypes: true })) {
    if (!entry.isFile()) continue;
    const filename = join(entry.parentPath, entry.name);
    const first = relative(root, filename).split(sep)[0];
    // ESLint's built-in exclusions; configured ignores are checked by ESLint below.
    if (first === "node_modules" || first === ".git") continue;
    const extension = extname(filename).slice(1);
    if (!(extension in p.effectiveConfigHashes) || await eslint.isPathIgnored(filename)) continue;
    validateEffectiveConfiguration(await eslint.calculateConfigForFile(filename), extension, p);
    actualFiles++;
  }
  requireValue(actualFiles > 0, "No actual frontend source files were qualified.");
  return actualFiles;
}
