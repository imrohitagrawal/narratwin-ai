import { loadProfile } from "../../frontend/scripts/frontend-security-profile.mjs";
import { createHash, timingSafeEqual } from "node:crypto";
import { spawnSync } from "node:child_process";
import {
  chmodSync, chownSync, copyFileSync, cpSync, existsSync, lchownSync, lstatSync, mkdirSync,
  readFileSync, readdirSync, renameSync, rmSync,
} from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const NPM_ROOT = "/usr/local/lib/node_modules/npm";
const ARCHIVE_ROOT = "/tmp/frontend-npm-archives";
const FRONTEND_BUILD_ROOT = "/tmp/frontend-build";
const FRONTEND_DEPS_ROOT = "/mnt/deps";
const FRONTEND_SOURCE_ROOT = "/mnt/frontend";
const FRONTEND_RUNTIME_ROOT = "/app";

const archiveProfile = loadProfile().buildArchives;
export const ARCHIVES = Object.freeze(
  ["npm", "brace-expansion", "ip-address", "tar", "undici"].map((name) => {
    const { version, sha512 } = archiveProfile[name];
    return Object.freeze({ filename: `${name}-${version}.tgz`, package: name, version,
      sha512, destination: name === "npm" ? NPM_ROOT : `${NPM_ROOT}/node_modules/${name}` });
  }),
);

export function verifyArchiveChecksum(filename, expectedHex) {
  if (!/^[0-9a-f]{128}$/.test(expectedHex)) throw new Error("Invalid expected archive checksum.");
  const actual = createHash("sha512").update(readFileSync(filename)).digest();
  const expected = Buffer.from(expectedHex, "hex");
  if (!timingSafeEqual(actual, expected)) throw new Error(`Archive checksum mismatch: ${filename}`);
}

export function assertSafeDestination(root, destination) {
  const canonicalRoot = resolve(root);
  const canonicalDestination = resolve(destination);
  const child = relative(canonicalRoot, canonicalDestination);
  if (!child || child === ".." || child.startsWith(`..${sep}`)) {
    throw new Error(`Unsafe package destination: ${destination}`);
  }
}

function verifyPackage(destination, spec) {
  const manifestPath = join(destination, "package.json");
  if (!existsSync(manifestPath)) throw new Error(`Missing package manifest: ${spec.package}`);
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  if (manifest.name !== spec.package || manifest.version !== spec.version) {
    throw new Error(`Extracted package identity mismatch: ${spec.package}`);
  }
}

async function extract(tar, archive, destination) {
  rmSync(destination, { recursive: true, force: true });
  mkdirSync(destination, { recursive: true, mode: 0o755 });
  await tar.x({ file: archive, cwd: destination, strip: 1, strict: true, preserveOwner: false });
}

async function prepare() {
  for (const spec of ARCHIVES) verifyArchiveChecksum(join(ARCHIVE_ROOT, spec.filename), spec.sha512);
  const require = createRequire(import.meta.url);
  const bootstrapTar = require(join(NPM_ROOT, "node_modules/tar"));
  const npmSpec = ARCHIVES[0];
  const stagedNpm = `${NPM_ROOT}.staged`;
  await extract(bootstrapTar, join(ARCHIVE_ROOT, npmSpec.filename), stagedNpm);
  verifyPackage(stagedNpm, npmSpec);
  rmSync(NPM_ROOT, { recursive: true, force: true });
  renameSync(stagedNpm, NPM_ROOT);

  const hardenedTar = require(join(NPM_ROOT, "node_modules/tar"));
  for (const spec of ARCHIVES.slice(1)) {
    assertSafeDestination(NPM_ROOT, spec.destination);
    const staged = `${spec.destination}.staged`;
    await extract(hardenedTar, join(ARCHIVE_ROOT, spec.filename), staged);
    verifyPackage(staged, spec);
    rmSync(spec.destination, { recursive: true, force: true });
    mkdirSync(dirname(spec.destination), { recursive: true, mode: 0o755 });
    renameSync(staged, spec.destination);
  }
  rmSync(ARCHIVE_ROOT, { recursive: true, force: true });
  rmSync(fileURLToPath(import.meta.url), { force: true });
}

function secureTree(path) {
  const stat = lstatSync(path);
  if (stat.isSymbolicLink()) {
    lchownSync(path, 0, 0);
    return;
  }
  chownSync(path, 0, 0);
  chmodSync(path, stat.isDirectory() ? 0o755 : (stat.mode & 0o111) ? 0o755 : 0o644);
  if (stat.isDirectory()) for (const name of readdirSync(path)) secureTree(join(path, name));
}

export function copySharpLibvips(dependenciesRoot, runtimeRoot, architecture) {
  if (![dependenciesRoot, runtimeRoot].every((value) => typeof value === "string" && value)) {
    throw new Error("Sharp libvips roots must be non-empty strings.");
  }
  if (!Object.hasOwn({ x64: true, arm64: true }, architecture)) {
    throw new Error(`Unsupported Sharp libvips architecture: ${architecture}`);
  }
  const packagePath = join("node_modules", "@img", `sharp-libvips-linuxmusl-${architecture}`);
  const sourceDirectory = join(resolve(dependenciesRoot), packagePath, "lib");
  const prefixed = readdirSync(sourceDirectory).filter((name) => name.startsWith("libvips-cpp.so."));
  const candidates = prefixed.filter((name) => /^libvips-cpp\.so\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$/.test(name));
  if (prefixed.length !== 1 || candidates.length !== 1) {
    throw new Error("Expected exactly one canonical Sharp libvips shared object.");
  }
  const source = join(sourceDirectory, candidates[0]);
  const sourceStat = lstatSync(source);
  if (!sourceStat.isFile() || sourceStat.isSymbolicLink()) {
    throw new Error("Sharp libvips shared object must be a regular non-symlink file.");
  }
  const destinationDirectory = join(resolve(runtimeRoot), packagePath, "lib");
  mkdirSync(destinationDirectory, { recursive: true, mode: 0o755 });
  const destination = join(destinationDirectory, candidates[0]);
  copyFileSync(source, destination);
  chmodSync(destination, 0o644);
  return candidates[0];
}

export function assembleFrontendRuntime() {
  if (!existsSync(join(FRONTEND_DEPS_ROOT, "node_modules", "next", "dist", "bin", "next"))) {
    throw new Error("Mounted frontend dependencies are incomplete.");
  }
  if (!existsSync(join(FRONTEND_SOURCE_ROOT, "package.json"))) {
    throw new Error("Mounted frontend source is incomplete.");
  }
  rmSync(FRONTEND_BUILD_ROOT, { recursive: true, force: true });
  rmSync(FRONTEND_RUNTIME_ROOT, { recursive: true, force: true });
  try {
    cpSync(FRONTEND_SOURCE_ROOT, FRONTEND_BUILD_ROOT, {
      recursive: true,
      filter: (source) => ![".next", "node_modules"].includes(relative(FRONTEND_SOURCE_ROOT, source).split(sep)[0]),
    });
    cpSync(join(FRONTEND_DEPS_ROOT, "node_modules"), join(FRONTEND_BUILD_ROOT, "node_modules"), { recursive: true });
    const next = join(FRONTEND_BUILD_ROOT, "node_modules", "next", "dist", "bin", "next");
    const result = spawnSync("/usr/bin/node", [next, "build"], {
      cwd: FRONTEND_BUILD_ROOT,
      env: process.env,
      stdio: "inherit",
    });
    if (result.error || result.signal || result.status !== 0) {
      throw new Error(`Frontend build failed: ${result.error?.message ?? result.signal ?? result.status}`);
    }
    mkdirSync(FRONTEND_RUNTIME_ROOT, { recursive: true, mode: 0o755 });
    cpSync(join(FRONTEND_BUILD_ROOT, ".next", "standalone"), FRONTEND_RUNTIME_ROOT, { recursive: true });
    cpSync(join(FRONTEND_BUILD_ROOT, ".next", "static"), join(FRONTEND_RUNTIME_ROOT, ".next", "static"), {
      recursive: true,
    });
    secureTree(FRONTEND_RUNTIME_ROOT);
  } finally {
    rmSync(FRONTEND_BUILD_ROOT, { recursive: true, force: true });
  }
}

const isMain = process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url;
if (isMain) {
  if (process.argv.length !== 2) throw new Error("prepare_frontend_npm.mjs accepts no arguments.");
  await prepare();
}
