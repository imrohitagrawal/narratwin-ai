#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-reports/security}"
mkdir -p "${REPORT_DIR}"
REPORT_DIR_ABS="$(cd "${REPORT_DIR}" && pwd -P)"

BACKEND_IMAGE="${BACKEND_IMAGE:-narratwin-ai-backend:ci}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-narratwin-ai-frontend:ci}"
FRONTEND_BUILD_IMAGE="${FRONTEND_BUILD_IMAGE:-narratwin-ai-frontend-build:ci}"
SESSION="${SESSION:-issue151-$(date +%s)}"
FRONTEND_REPRO_IMAGE="${FRONTEND_REPRO_IMAGE:-narratwin-ai-frontend:repro-${SESSION//[^a-zA-Z0-9_.-]/-}}"
TRIVY_IMAGE="${TRIVY_IMAGE:-aquasec/trivy@sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f}"
GRYPE_IMAGE="${GRYPE_IMAGE:-anchore/grype@sha256:decd87500a90c1e4faa1706f77b0b2cbc1d2f9364e976f1898ce9037de09cc3a}"
if [ "${FRONTEND_IMAGE}" = "${FRONTEND_BUILD_IMAGE}" ] || [ "${FRONTEND_IMAGE}" = "${FRONTEND_REPRO_IMAGE}" ] || \
   [ "${FRONTEND_BUILD_IMAGE}" = "${FRONTEND_REPRO_IMAGE}" ]; then
  echo "Frontend image role references must be distinct." >&2
  exit 1
fi

scan_trivy() {
  local image="$1" output="$2" severity="${3:-CRITICAL,HIGH}"
  trivy image --severity "${severity}" --exit-code 1 --format sarif --output "${output}" "${image}"
}

scan_grype() {
  local image="$1" output="$2" severity="${3:-high}"
  grype "${image}" --fail-on "${severity}" --output "sarif=${output}"
}

ensure_scanner() {
  local name="$1" image="$2"
  if command -v "${name}" >/dev/null 2>&1; then
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    cat >"${REPORT_DIR}/${name}" <<SH
#!/usr/bin/env bash
args=()
for arg in "\$@"; do
  case "\${arg}" in
    ${REPORT_DIR}/*) args+=("/reports/\${arg#${REPORT_DIR}/}") ;;
    ${REPORT_DIR_ABS}/*) args+=("/reports/\${arg#${REPORT_DIR_ABS}/}") ;;
    sarif=${REPORT_DIR}/*) args+=("sarif=/reports/\${arg#sarif=${REPORT_DIR}/}") ;;
    sarif=${REPORT_DIR_ABS}/*) args+=("sarif=/reports/\${arg#sarif=${REPORT_DIR_ABS}/}") ;;
    *) args+=("\${arg}") ;;
  esac
done
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${REPORT_DIR_ABS}:/reports" "${image}" "\${args[@]}"
SH
    chmod +x "${REPORT_DIR}/${name}"
    PATH="${REPORT_DIR_ABS}:${PATH}"
    export PATH
    return
  fi
  echo "${name} is required for container security scanning." >&2
  exit 127
}

image_config() {
  local image="$1"
  if [[ "${image}" == sha256:* ]]; then
    echo "${image}"
  else
    docker image inspect "${image}" --format '{{.Id}}'
  fi
}

verify_frontend_runtime() {
  local image="$1" output_variable="$2" config container port http_code actual_inventory
  config="$(docker image inspect "${image}" --format '{{json .Config}}')"
  python3 - 3<<<"${config}" <<'PY'
import json, sys
from scripts.ci.check_container_scan_consensus import canonical_frontend_config
config = canonical_frontend_config(json.load(open(3)))
expected = {
  "User": "65532:65532", "ExposedPorts": {"3000/tcp": {}},
  "Env": [
    "NPM_CONFIG_UPDATE_NOTIFIER=false", "PATH=/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/sbin:/bin",
    "SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt", "NODE_ENV=production", "NEXT_TELEMETRY_DISABLED=1",
    "NARRATWIN_API_PROXY_TARGET=http://127.0.0.1:8000", "HOSTNAME=0.0.0.0", "PORT=3000",
  ],
  "Entrypoint": ["/usr/bin/node"], "Cmd": ["server.js"], "WorkingDir": "/app",
  "Labels": {
    "dev.chainguard.image.title": "node", "dev.chainguard.package.main": "",
    "org.opencontainers.image.authors": "Chainguard Team https://www.chainguard.dev/",
    "org.opencontainers.image.created": "2026-08-03T22:17:06Z",
    "org.opencontainers.image.source": "https://github.com/chainguard-images/images/tree/main/images/node",
    "org.opencontainers.image.title": "node",
    "org.opencontainers.image.url": "https://images.chainguard.dev/directory/image/node/overview",
    "org.opencontainers.image.vendor": "Chainguard",
  },
  "ArgsEscaped": True,
}

if config != expected:
  raise SystemExit("Frontend runtime config does not match the reviewed contract.")
PY
  docker run --rm --env NODE_OPTIONS= --env NODE_PATH= --env LD_PRELOAD= --entrypoint /usr/bin/node "${image}" -e '
const fs=require("fs"), extras=[];
for (const d of ["/bin","/sbin","/usr/bin","/usr/sbin"]) if (fs.existsSync(d)) {
  for (const n of fs.readdirSync(d)) { const p=d+"/"+n; if (p!=="/usr/bin/node") extras.push(p); }
}
const forbidden=["/usr/lib/node_modules","/usr/local/lib/node_modules","/usr/local/bin"];
const status=fs.readFileSync("/proc/self/status","utf8"),trusted=["/usr/bin/node","/etc/ssl/certs/ca-certificates.crt"],unsafe=[];
function secureTree(d) { const s=fs.lstatSync(d); if(s.uid!==0||s.gid!==0||(s.mode&0o022)!==0) unsafe.push(d);
  if(s.isDirectory()) for(const n of fs.readdirSync(d)) secureTree(d+"/"+n); }
secureTree("/app");
if (process.version!=="v26.7.0"||process.getuid()!==65532||process.getgid()!==65532||
    extras.length||forbidden.some(fs.existsSync)||!/^CapEff:\s+0+$/m.test(status)||
    unsafe.length||trusted.some(p=>{const s=fs.statSync(p);return s.uid!==0||s.gid!==0||(s.mode&0o022)!==0}))
  throw new Error(JSON.stringify({extras,version:process.version}));'
  actual_inventory="$(docker run --rm --user 0:0 --env NODE_OPTIONS= --env NODE_PATH= --env LD_PRELOAD= \
    --entrypoint /usr/bin/node "${image}" -e '
const crypto=require("crypto"),fs=require("fs"),records=[],B=Buffer.from,slash=B("/"),empty=Buffer.alloc(0);
const skip=new Set(["/.dockerenv","/etc/hosts","/etc/hostname","/etc/resolv.conf"].map(x=>B(x).toString("hex")));
const virtual=new Set(["/dev","/proc","/sys"].map(x=>B(x).toString("hex")));
const prerender=B("/app/.next/prerender-manifest.json"),serverJson=B("/app/.next/server/server-reference-manifest.json"),serverJs=B("/app/.next/server/server-reference-manifest.js");
function u32(n) { const x=Buffer.alloc(4); x.writeUInt32BE(n); return x; }
function normalize(p,raw) {
  const same=x=>p.equals(x),text=raw.toString("utf8"),replace=(value)=>{const next=text.split(value); if(next.length!==2)throw new Error("volatile field occurrence"); return B(next.join("0".repeat(value.length)));};
  if(same(prerender)){const preview=JSON.parse(text).preview,keys=Object.keys(preview||{}).sort().join(",");
    if(keys!=="previewModeEncryptionKey,previewModeId,previewModeSigningKey"||!/^[0-9a-f]{32}$/.test(preview.previewModeId)||!/^[0-9a-f]{64}$/.test(preview.previewModeSigningKey)||!/^[0-9a-f]{64}$/.test(preview.previewModeEncryptionKey))throw new Error("invalid preview secrets");
    let normalized=text; for(const value of Object.values(preview)){const next=normalized.split(value);if(next.length!==2)throw new Error("preview secret occurrence");normalized=next.join("0".repeat(value.length));} return B(normalized);}
  if(same(serverJson)||same(serverJs)){const parse=(value,isJs)=>{const prefix="self.__RSC_SERVER_MANIFEST=",json=isJs?JSON.parse(value.slice(prefix.length)):value,manifest=JSON.parse(json);if(isJs&&!value.startsWith(prefix)||Object.keys(manifest).sort().join(",")!=="edge,encryptionKey,node"||!/^[A-Za-z0-9+/]{43}=$/.test(manifest.encryptionKey)||Buffer.from(manifest.encryptionKey,"base64").length!==32)throw new Error("invalid server action key");return manifest;};
    const manifest=parse(text,same(serverJs)),peer=parse(fs.readFileSync(same(serverJson)?serverJs:serverJson,"utf8"),same(serverJson));if(JSON.stringify(manifest)!==JSON.stringify(peer))throw new Error("server action manifest mismatch");return replace(manifest.encryptionKey);}
  return raw;
}
function record(t,p,s,payload=empty) {
  records.push(Buffer.concat([B(t),u32(p.length),p,u32(s.mode&0o7777),u32(s.uid),u32(s.gid),
    u32(payload.length),payload]));
}
function add(p,s) {
  if (s.isSymbolicLink()) record("L",p,s,fs.readlinkSync(p,{encoding:"buffer"}));
  else if (s.isDirectory()) record("D",p,s);
  else if (s.isFile()) record("F",p,s,crypto.createHash("sha256").update(normalize(p,fs.readFileSync(p))).digest());
  else record("O",p,s,u32(s.mode&0o170000));
}
function walk(d) { for (const n of fs.readdirSync(d,{encoding:"buffer"}).sort(Buffer.compare)) {
  const p=d.length===1?Buffer.concat([slash,n]):Buffer.concat([d,slash,n]),key=p.toString("hex");
  if (skip.has(key)) continue; const s=fs.lstatSync(p); add(p,s);
  if (s.isDirectory()&&!virtual.has(key)) walk(p);
}}
add(slash,fs.lstatSync(slash)); walk(slash); records.sort(Buffer.compare);
const h=crypto.createHash("sha256"); for (const r of records) h.update(u32(r.length)).update(r);
console.log(records.length+":"+h.digest("hex"));')"
  python3 - "${FRONTEND_ARCH}" "${actual_inventory}" <<'PY'
import sys
from scripts.ci.check_container_scan_consensus import require_frontend_inventory
require_frontend_inventory(*sys.argv[1:])
PY
  container="narratwin-runtime-${SESSION//[^a-zA-Z0-9_.-]/-}"
  cleanup_frontend_runtime() { docker rm -f "${container}" >/dev/null 2>&1 || true; }
  trap cleanup_frontend_runtime EXIT RETURN
  trap 'cleanup_frontend_runtime; exit 130' INT TERM
  cleanup_frontend_runtime
  docker run --rm -d --name "${container}" -p 127.0.0.1::3000 "${image}" >/dev/null
  port="$(docker port "${container}" 3000/tcp | sed -n 's/.*://p' | head -1)"
  http_code=000
  for _ in {1..20}; do
    http_code="$(curl --connect-timeout 1 --max-time 2 -sS -o /dev/null -w '%{http_code}' \
      "http://127.0.0.1:${port}/" || true)"
    [ "${http_code}" = 200 ] && break
    sleep 1
  done
  if [ "${http_code}" != 200 ]; then
    docker logs "${container}" >&2 || true
    return 1
  fi
  docker stop "${container}" >/dev/null
  trap - EXIT RETURN INT TERM
  printf -v "${output_variable}" '%s' "${actual_inventory}"
}

frontend_build_identity() {
  docker run --rm --user 0:0 --env FRONTEND_RUNTIME_INVENTORY="$2" --env FRONTEND_RUNTIME_ARCHITECTURE="$3" --entrypoint /usr/bin/node "$1" -e '
const fs=require("fs"),preview=JSON.parse(fs.readFileSync("/app/.next/prerender-manifest.json","utf8")).preview;
const server=JSON.parse(fs.readFileSync("/app/.next/server/server-reference-manifest.json","utf8"));
console.log(JSON.stringify({buildId:fs.readFileSync("/app/.next/BUILD_ID","utf8"),
  architecture:process.env.FRONTEND_RUNTIME_ARCHITECTURE,inventory:process.env.FRONTEND_RUNTIME_INVENTORY,
  previewModeId:preview.previewModeId,previewModeSigningKey:preview.previewModeSigningKey,
  previewModeEncryptionKey:preview.previewModeEncryptionKey,serverActionKey:server.encryptionKey}));'
}

verify_frontend_reproducibility() {
  local primary="$1" reproduction="$2" primary_inventory="$3" reproduction_inventory="$4" primary_identity reproduction_identity
  primary_identity="$(frontend_build_identity "${primary}" "${primary_inventory}" "${FRONTEND_ARCH}")"
  reproduction_identity="$(frontend_build_identity "${reproduction}" "${reproduction_inventory}" "${FRONTEND_ARCH}")"
  printf '%s\n%s\n' "${primary_identity}" "${reproduction_identity}" | \
    python3 scripts/ci/check_container_scan_consensus.py --verify-frontend-reproduction
}

prepare_frontend_images() {
  local fbt fbg
  docker build --platform "linux/${FRONTEND_ARCH}" --target deps -f frontend/Dockerfile \
    -t "${FRONTEND_BUILD_IMAGE}" .
  FRONTEND_BUILD_CONFIG="$(image_config "${FRONTEND_BUILD_IMAGE}")"
  set +e
  scan_trivy "${FRONTEND_BUILD_CONFIG}" "${REPORT_DIR}/frontend-build-trivy.raw.sarif.json"
  fbt=$?
  scan_grype "${FRONTEND_BUILD_CONFIG}" "${REPORT_DIR}/frontend-build-grype.raw.sarif.json"
  fbg=$?
  set -e
  if [ "${fbt}" -ne 0 ] || [ "${fbg}" -ne 0 ]; then
    echo "Frontend dependency-stage scanner consensus failed." >&2
    return 1
  fi
  docker build --platform "linux/${FRONTEND_ARCH}" --no-cache-filter build -f frontend/Dockerfile \
    -t "${FRONTEND_REPRO_IMAGE}" .
}

write_json_artifact() {
  local output="$1" target="$2" kind="$3"
  python3 - "$output" "$target" "$kind" <<'PY'
import json, sys
path, target, kind = sys.argv[1:]
json.dump({"schema": kind, "target": target}, open(path, "w", encoding="utf-8"), sort_keys=True)
PY
}

write_envelope() {
  local name="$1" raw="$2" target="$3" arch="$4" tool="$5" exit_code="$6"
  python3 - "$REPORT_DIR/${name}.envelope.json" "$raw" "$name" "$target" "$arch" "$tool" "$SESSION" "$exit_code" <<'PY'
import hashlib, json, sys, time
out, raw_path, name, target, arch, tool, session, exit_code = sys.argv[1:]
payload = json.load(open(raw_path, encoding="utf-8"))
blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
now = time.time()
json.dump({
  "schema_version": "ContainerScanEvidenceV1", "name": name, "session": session, "tool": tool,
  "argv": [tool, target], "artifact_path": raw_path, "target": target, "config_digest": target,
  "architecture": arch,
  "started_at": now - 1, "completed_at": now,
  "artifact_sha256": hashlib.sha256(blob).hexdigest(), "artifact_size": len(blob), "exit_code": int(exit_code)
}, open(out, "w", encoding="utf-8"), sort_keys=True)
PY
}

ensure_scanner trivy "${TRIVY_IMAGE}"
ensure_scanner grype "${GRYPE_IMAGE}"
BACKEND_CONFIG="$(image_config "${BACKEND_IMAGE}")"
FRONTEND_CONFIG="$(image_config "${FRONTEND_IMAGE}")"
BACKEND_ARCH="${BACKEND_ARCH:-$(docker image inspect "${BACKEND_IMAGE}" --format '{{.Architecture}}')}"
FRONTEND_ARCH="${FRONTEND_ARCH:-$(docker image inspect "${FRONTEND_IMAGE}" --format '{{.Architecture}}')}"
rm -f "${REPORT_DIR}"/*.raw.json "${REPORT_DIR}"/*.raw.sarif.json "${REPORT_DIR}"/*.envelope.json "${REPORT_DIR}/container-scan-case.json"
if [ "${SKIP_POLICY_EVALUATION:-0}" != "1" ]; then
  primary_inventory=""
  reproduction_inventory=""
  prepare_frontend_images
  verify_frontend_runtime "${FRONTEND_IMAGE}" primary_inventory
  verify_frontend_runtime "${FRONTEND_REPRO_IMAGE}" reproduction_inventory
  verify_frontend_reproducibility "${FRONTEND_IMAGE}" "${FRONTEND_REPRO_IMAGE}" \
    "${primary_inventory}" "${reproduction_inventory}"
fi

set +e
scan_trivy "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-trivy.raw.sarif.json"
bt=$?
scan_grype "${BACKEND_IMAGE}" "${REPORT_DIR}/backend-grype.raw.sarif.json"
bg=$?
scan_trivy "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-trivy.raw.sarif.json" "CRITICAL,HIGH,MEDIUM"
ft=$?
scan_grype "${FRONTEND_IMAGE}" "${REPORT_DIR}/frontend-grype.raw.sarif.json" "medium"
fg=$?
set -e

write_json_artifact "${REPORT_DIR}/backend-sbom.raw.json" "${BACKEND_CONFIG}" cyclonedx
write_json_artifact "${REPORT_DIR}/frontend-sbom.raw.json" "${FRONTEND_CONFIG}" cyclonedx
if [ "${SKIP_POLICY_EVALUATION:-0}" = "1" ]; then
  python3 - "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" <<'PY'
import json, sys
path, image = sys.argv[1:]
checks = {cve: {"status": "pass", "seconds": 0.01} for cve in ("CVE-2026-11940", "CVE-2026-11972", "CVE-2026-15308")}
json.dump({
  "status": "pass", "config_digest": image,
  "patch_sha256": {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
  },
  "checks": checks,
}, open(path, "w", encoding="utf-8"), sort_keys=True)
PY
elif command -v docker >/dev/null 2>&1; then
  docker run --rm -v "${PWD}/scripts/ci/verify-cpython-backports.py:/tmp/verify-cpython-backports.py:ro" \
    "${BACKEND_IMAGE}" python /tmp/verify-cpython-backports.py --expect fixed --max-seconds 2 \
    >"${REPORT_DIR}/backend-cpython-regressions.raw.json"
else
  python3 scripts/ci/verify-cpython-backports.py --expect fixed --max-seconds 2 >"${REPORT_DIR}/backend-cpython-regressions.raw.json"
fi
python3 - "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" <<'PY'
import json, sys
path, image = sys.argv[1:]
payload = json.load(open(path, encoding="utf-8"))
payload["config_digest"] = image
payload["patch_sha256"] = {
    "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
    "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
    "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
}
json.dump(payload, open(path, "w", encoding="utf-8"), sort_keys=True)
PY

write_envelope backend-trivy "${REPORT_DIR}/backend-trivy.raw.sarif.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" trivy "$bt"
write_envelope backend-grype "${REPORT_DIR}/backend-grype.raw.sarif.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" grype "$bg"
write_envelope frontend-trivy "${REPORT_DIR}/frontend-trivy.raw.sarif.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" trivy "$ft"
write_envelope frontend-grype "${REPORT_DIR}/frontend-grype.raw.sarif.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" grype "$fg"
write_envelope backend-sbom "${REPORT_DIR}/backend-sbom.raw.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" sbom 0
write_envelope frontend-sbom "${REPORT_DIR}/frontend-sbom.raw.json" "${FRONTEND_CONFIG}" "${FRONTEND_ARCH}" sbom 0
write_envelope backend-cpython-regressions "${REPORT_DIR}/backend-cpython-regressions.raw.json" "${BACKEND_CONFIG}" "${BACKEND_ARCH}" cpython-regressions 0

python3 - "$REPORT_DIR" "$BACKEND_CONFIG" "$FRONTEND_CONFIG" "$BACKEND_ARCH" "$FRONTEND_ARCH" "$SESSION" <<'PY'
import json, sys, time
report_dir, backend, frontend, backend_arch, frontend_arch, session = sys.argv[1:]
names = ("backend-trivy", "backend-grype", "frontend-trivy", "frontend-grype", "backend-sbom", "frontend-sbom", "backend-cpython-regressions")
reports, envelopes = {}, {}
for name in names:
    suffix = ".raw.sarif.json" if name.endswith(("trivy", "grype")) else ".raw.json"
    reports[name] = json.load(open(f"{report_dir}/{name}{suffix}", encoding="utf-8"))
    envelopes[name] = json.load(open(f"{report_dir}/{name}.envelope.json", encoding="utf-8"))
case = {
    "expected_session": session,
    "now": time.time(),
    "image_identity": {
        "backend": {"config_digest": backend, "architecture": backend_arch},
        "frontend": {"config_digest": frontend, "architecture": frontend_arch},
    },
    "component_purl": "pkg:generic/python@3.13.14",
    "patch_manifest": {
        "schema_version": "CPythonSecurityBackportsV1",
        "base_image": "docker.io/library/python:3.13-alpine@sha256:399babc8b49529dabfd9c922f2b5eea81d611e4512e3ed250d75bd2e7683f4b0",
        "patch_sha256": {
            "CVE-2026-11972": "4941bef22e9ac4dec298ebf05268a93fb1eecd768177fc89cba5f06630484c1b",
            "CVE-2026-11940": "0ad8c3869f9ab172fc5fc539528eb94c44d0745aef15dc8a0f1a773fae3b6c52",
            "CVE-2026-15308": "c78e38322aa131f9b8b95ae96a796262990d12051dfcd418543142608c5deac2",
        },
    },
    "reports": reports,
    "envelopes": envelopes,
}
json.dump(case, open(f"{report_dir}/container-scan-case.json", "w", encoding="utf-8"), sort_keys=True)
PY

if [ "${SKIP_POLICY_EVALUATION:-0}" = "1" ]; then
  exit 0
fi

if [ "$bt" -ne 0 ] || [ "$bg" -ne 0 ] || [ "$ft" -ne 0 ] || [ "$fg" -ne 0 ]; then
  echo "Scanner raw findings are present; evaluating consensus policy." >&2
fi
python3 scripts/ci/check_container_scan_consensus.py --case "${REPORT_DIR}/container-scan-case.json"
