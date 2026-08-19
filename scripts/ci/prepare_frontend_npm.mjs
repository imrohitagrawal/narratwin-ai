import { createHash, timingSafeEqual } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const NPM_ROOT = "/usr/local/lib/node_modules/npm";
const ARCHIVE_ROOT = "/tmp/frontend-npm-archives";

export const ARCHIVES = Object.freeze([
  Object.freeze({ filename: "npm-12.0.2.tgz", package: "npm", version: "12.0.2",
    sha512: "b885e890b9418fa1693544d05f53e64f9a73ec194837d4258b15fecdd692347b1dd2a517b1b0cbaf9d31cd8e92c3b70956bd2ecc72833a57b4b3098f5bfa7943",
    destination: NPM_ROOT }),
  Object.freeze({ filename: "brace-expansion-5.0.9.tgz", package: "brace-expansion", version: "5.0.9",
    sha512: "49c43822ebc8105d533253fb66dfaf8c9ffff7394f6f64837315b13376e4f2ceade8619d27b28ed5d09c4e274e3c929e3d6df42c4ff6713ef00b23e1a3dfd6c6",
    destination: `${NPM_ROOT}/node_modules/brace-expansion` }),
  Object.freeze({ filename: "ip-address-10.3.1.tgz", package: "ip-address", version: "10.3.1",
    sha512: "d5ef5dde46fdecd1c94c8243656f6b2aa5b687af9d15ae740f2d1fa4f48c429d800e37b982f2ac5e67622ba770639b7be93693b79f8fe4dd58fcba13a08c4fea",
    destination: `${NPM_ROOT}/node_modules/ip-address` }),
  Object.freeze({ filename: "tar-7.5.21.tgz", package: "tar", version: "7.5.21",
    sha512: "5dd86d0af94ccb0c31a425bc604ab794e5c126950f4d1d8e1c77302cf3b71f0b09a8e1dad8e93fa09eebb86ce9f89acaa113d50b327001d123a8b5bfbcd44f1c",
    destination: `${NPM_ROOT}/node_modules/tar` }),
  Object.freeze({ filename: "undici-6.28.0.tgz", package: "undici", version: "6.28.0",
    sha512: "2c863dd7483d4c8d77612f7996b305aecf119bfbbf8ab8077935a8282a2d79e274e02509f767847e3d2b567fbb54a30f06950f894a0129f84dc8b236dc413f28",
    destination: `${NPM_ROOT}/node_modules/undici` }),
]);

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

const isMain = process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url;
if (isMain) {
  if (process.argv.length !== 2) throw new Error("prepare_frontend_npm.mjs accepts no arguments.");
  await prepare();
}
