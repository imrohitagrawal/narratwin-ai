"""Closed current frontend configuration and graph proof; no acceptance authority."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = "docs/security/FRONTEND_DEPENDENCY_REFRESH.json"
FIELDS = set(
    "schemaVersion baseSha manifestHash lockHash recordHashes removedRecords effectiveConfigHashes baselineConfigsSha256 rootDiscoverySourceSha256 verificationTimeoutSeconds buildArchives sharpVersion libvipsVersion runtimePackages packageVersions".split()
)
ARCHIVE_NAMES = set("npm brace-expansion ip-address tar undici http-cache-semantics".split())
EXTENSIONS = {"ts", "tsx", "js", "jsx", "mjs", "cjs"}


class ProfileError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileError(message)


BOUND_PACKAGES = (
    "next",
    "eslint-config-next",
    "lighthouse",
    "vitest",
    "vite",
    "zod",
    "puppeteer-core",
    "chromium-bidi",
)
PACKAGE_NAMES = {*BOUND_PACKAGES, "brace-expansion", "sharp", "source-map-js", "tinyglobby"}
# The scoped tinyglobby alias is installed at the fast-glob path.
PACKAGE_RECORDS = {"tinyglobby": "node_modules/fast-glob"}


def version_key(value: str) -> tuple[tuple[int, ...], int, tuple[int, ...]]:
    """Order release versions; a prerelease sorts before its release. Malformed fails closed."""
    main, _, pre = value.partition("-")
    require(
        re.fullmatch(r"\d+(?:\.\d+)*", main) is not None
        and re.fullmatch(r"(?:\d+(?:\.\d+)*)?", pre) is not None,
        "Frontend record version invalid.",
    )
    return (
        tuple(int(part) for part in main.split(".")),
        0 if pre else 1,
        tuple(int(part) for part in pre.split(".")) if pre else (),
    )
# Exact records only: a family name must not admit a look-alike or a nested foreign package.
QUALIFIED_RECORDS = {""} | {
    "node_modules/" + name
    for name in """
    @emnapi/runtime @next/env @next/eslint-plugin-next @oxc-project/types
    @puppeteer/browsers @puppeteer/browsers/node_modules/ansi-regex
    @puppeteer/browsers/node_modules/cliui/node_modules/string-width
    @puppeteer/browsers/node_modules/string-width
    @puppeteer/browsers/node_modules/wrap-ansi/node_modules/string-width
    @puppeteer/browsers/node_modules/yargs
    @rolldown/binding-android-arm-eabi @rolldown/binding-android-arm64
    @rolldown/binding-darwin-arm64 @rolldown/binding-darwin-x64 @rolldown/binding-freebsd-x64
    @rolldown/binding-linux-arm-gnueabihf @rolldown/binding-linux-arm64-gnu
    @rolldown/binding-linux-arm64-musl @rolldown/binding-linux-ppc64-gnu
    @rolldown/binding-linux-s390x-gnu @rolldown/binding-linux-x64-gnu
    @rolldown/binding-linux-x64-musl @rolldown/binding-openharmony-arm64
    @rolldown/binding-win32-arm64-msvc @rolldown/binding-win32-x64-msvc
    @vitest/expect @vitest/mocker @vitest/pretty-format @vitest/runner @vitest/snapshot
    @vitest/spy @vitest/utils
    ajv-formats ajv-formats/node_modules/ajv ajv-formats/node_modules/json-schema-traverse
    axe-core brace-expansion chai chromium-bidi devtools-protocol eslint-config-next fast-glob
    fast-uri fdir get-east-asian-width lighthouse lighthouse/node_modules/ajv
    lighthouse/node_modules/json-schema-traverse lightningcss lightningcss-android-arm64
    lightningcss-darwin-arm64 lightningcss-darwin-x64 lightningcss-freebsd-x64
    lightningcss-linux-arm-gnueabihf lightningcss-linux-arm64-gnu lightningcss-linux-arm64-musl
    lightningcss-linux-x64-gnu lightningcss-linux-x64-musl lightningcss-win32-arm64-msvc
    lightningcss-win32-x64-msvc modern-tar next picomatch puppeteer-core
    puppeteer-core/node_modules/devtools-protocol puppeteer-core/node_modules/ws
    require-from-string rolldown sharp source-map-js third-party-web tinyrainbow tldts-core
    tldts-icann typed-query-selector vite vitest web-features webdriver-bidi-protocol zod
    """.split()
}


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "Duplicate frontend profile/input field.")
        result[key] = value
    return result


def parsed(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=unique)
    except (ValueError, TypeError) as error:
        raise ProfileError("Frontend JSON unavailable or malformed.") from error


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def matches(value: Any, pattern: str) -> bool:
    return isinstance(value, str) and re.fullmatch(pattern, value, re.ASCII) is not None


def load_profile(root: Path = ROOT) -> dict[str, Any]:
    try:
        profile = parsed((root / PROFILE_PATH).read_text(encoding="utf-8"))
    except OSError as error:
        raise ProfileError("Frontend profile unavailable.") from error
    require(type(profile) is dict and set(profile) == FIELDS, "Frontend profile schema invalid.")
    require(
        type(profile["schemaVersion"]) is int and profile["schemaVersion"] == 1,
        "Frontend schema version invalid.",
    )
    require(matches(profile["baseSha"], r"[0-9a-f]{40}"), "Frontend base invalid.")
    for key in ("manifestHash", "lockHash", "baselineConfigsSha256", "rootDiscoverySourceSha256"):
        require(matches(profile[key], r"[0-9a-f]{64}"), "Frontend hash invalid.")
    timeout = profile["verificationTimeoutSeconds"]
    require(type(timeout) is int and 0 < timeout <= 2147483, "Frontend timeout invalid.")
    for key in ("sharpVersion", "libvipsVersion"):
        require(matches(profile[key], r"\d+\.\d+\.\d+"), "Frontend native version invalid.")
    versions = profile["packageVersions"]
    require(
        type(versions) is dict
        and set(versions) == PACKAGE_NAMES
        and all(
            matches(value, r"\d+\.\d+\.\d+-\d+" if name == "chromium-bidi" else r"\d+\.\d+\.\d+")
            for name, value in versions.items()
        )
        and versions["sharp"] == profile["sharpVersion"],
        "Frontend package policy invalid.",
    )
    records, removed = profile["recordHashes"], profile["removedRecords"]
    require(
        type(records) is dict
        and bool(records)
        and all(
            isinstance(key, str)
            and (not key or key.startswith("node_modules/"))
            and ".." not in key.split("/")
            and matches(value, r"[0-9a-f]{64}")
            for key, value in records.items()
        ),
        "Frontend graph bindings invalid.",
    )
    require(
        type(removed) is list
        and bool(removed)
        and all(isinstance(key, str) and key.startswith("node_modules/") for key in removed)
        and len(set(removed)) == len(removed)
        and not set(removed) & set(records),
        "Frontend removals invalid.",
    )
    configs = profile["effectiveConfigHashes"]
    require(
        type(configs) is dict
        and set(configs) == EXTENSIONS
        and all(matches(value, r"[0-9a-f]{64}") for value in configs.values()),
        "Frontend configurations invalid.",
    )
    archives = profile["buildArchives"]
    require(type(archives) is dict and set(archives) == ARCHIVE_NAMES, "Frontend archives invalid.")
    for row in archives.values():
        require(
            type(row) is dict
            and set(row) == {"version", "sha256", "sha512"}
            and matches(row["version"], r"\d+\.\d+\.\d+")
            and matches(row["sha256"], r"[0-9a-f]{64}")
            and matches(row["sha512"], r"[0-9a-f]{128}"),
            "Frontend archive identity invalid.",
        )
    packages = profile["runtimePackages"]
    require(
        type(packages) is dict
        and set(packages)
        == {
            "alpine-keys",
            "alpine-release",
            "ca-certificates-bundle",
            "libgcc",
            "libstdc++",
            "musl",
        }
        and all(matches(value, r"[0-9.]+-r\d+") for value in packages.values()),
        "Frontend runtime packages invalid.",
    )
    return cast(dict[str, Any], profile)


def historical_text(path: str, base: str, timeout: int, root: Path = ROOT) -> str:
    require(
        path in {"frontend/package.json", "frontend/package-lock.json"}
        and matches(base, r"[0-9a-f]{40}"),
        "Historical frontend input invalid.",
    )
    try:
        return subprocess.run(
            ["git", "show", f"{base}:{path}"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout,
        ).stdout
    except (OSError, subprocess.SubprocessError) as error:
        raise ProfileError("Historical frontend input unavailable.") from error


def validate_pair(manifest_text: str, lock_text: str, *, root: Path = ROOT) -> None:
    """Only a proved exact current graph may unlock historical mutation fixtures."""
    p = load_profile(root)
    manifest, lock = parsed(manifest_text), parsed(lock_text)
    require(
        digest(manifest) == p["manifestHash"] and digest(lock) == p["lockHash"],
        "Current frontend binding drifted.",
    )
    base, timeout = p["baseSha"], p["verificationTimeoutSeconds"]
    old_manifest = parsed(historical_text("frontend/package.json", base, timeout, root))
    old_lock = parsed(historical_text("frontend/package-lock.json", base, timeout, root))
    expected = json.loads(json.dumps(old_manifest))
    expected["dependencies"]["next"] = p["packageVersions"]["next"]
    expected["devDependencies"]["eslint-config-next"] = p["packageVersions"]["eslint-config-next"]
    versions = p["packageVersions"]
    expected["devDependencies"]["lighthouse"] = versions["lighthouse"]
    expected["devDependencies"]["vitest"] = "^" + versions["vitest"]
    expected["overrides"].update(
        {
            "brace-expansion": versions["brace-expansion"],
            "sharp": "^" + versions["sharp"],
            "source-map-js": versions["source-map-js"],
            "@next/eslint-plugin-next": {"fast-glob": "npm:tinyglobby@" + versions["tinyglobby"]},
        }
    )
    prior_sharp = old_manifest["overrides"]["sharp"].removeprefix("^")
    expected["allowScripts"].pop("sharp@" + prior_sharp)
    expected["allowScripts"]["sharp@" + versions["sharp"]] = True
    for command in ("lint", "test", "build"):
        expected["scripts"][command] = (
            "node scripts/check-next-glob-compat.mjs && " + expected["scripts"][command]
        )
    require(manifest == expected, "Frontend manifest contains unqualified changes.")
    records, originals = lock["packages"], old_lock["packages"]
    changed = {name for name, row in records.items() if originals.get(name) != row}
    require(
        changed == set(p["recordHashes"])
        and set(originals) - set(records) == set(p["removedRecords"]),
        "Frontend graph delta invalid.",
    )
    # Supported package families are the authority boundary, not a profile-owned list.
    require(
        all(
            name in QUALIFIED_RECORDS
            or name.startswith(("node_modules/@img/sharp-", "node_modules/@next/swc-"))
            for name in changed
        ),
        "Unqualified frontend dependency family cannot be approved by rehashing.",
    )
    for name in PACKAGE_NAMES:
        require(
            records.get(PACKAGE_RECORDS.get(name, "node_modules/" + name), {}).get("version")
            == versions[name],
            "Frontend package version binding drifted.",
        )
    for name in changed - {""}:
        old, new = originals.get(name, {}), records[name]
        old_version = old.get("version")
        # Compare like with like: the scoped tinyglobby alias replaced a different package here.
        same_package = old.get("name", name) == new.get("name", name)
        if isinstance(old_version, str) and same_package:
            require(
                version_key(str(records[name].get("version", ""))) >= version_key(old_version),
                "Frontend record is older than its base.",
            )
    # Only the qualified obsolete fast-glob closure may disappear from this base.
    qualified_removals = {
        "node_modules/" + name
        for name in (
            "@nodelib/fs.scandir @nodelib/fs.stat @nodelib/fs.walk braces "
            "fast-glob/node_modules/glob-parent fastq fill-range is-number merge2 "
            "micromatch queue-microtask reusify run-parallel to-regex-range "
            "chromium-bidi/node_modules/zod tinyglobby/node_modules/fdir "
            "tinyglobby/node_modules/picomatch vite/node_modules/picomatch "
            "vitest/node_modules/picomatch @rolldown/binding-wasm32-wasi "
            "@rolldown/binding-wasm32-wasi/node_modules/@emnapi/core "
            "@rolldown/binding-wasm32-wasi/node_modules/@emnapi/wasi-threads"
        ).split()
    }
    require(
        set(p["removedRecords"]) == qualified_removals,
        "Unqualified frontend dependency removal cannot be approved by rehashing.",
    )
    for name, checksum in p["recordHashes"].items():
        require(digest(records[name]) == checksum, "Frontend record identity invalid.")
    require(
        records["node_modules/fast-glob"]["name"]
        == "tinyglobby",
        "Frontend alias identity concealed.",
    )
    normalized = json.loads(json.dumps(lock))
    for name in changed:
        if name in originals:
            normalized["packages"][name] = originals[name]
        else:
            normalized["packages"].pop(name)
    for name in p["removedRecords"]:
        normalized["packages"][name] = originals[name]
    require(normalized == old_lock, "Unrelated frontend graph changes cannot normalize.")
