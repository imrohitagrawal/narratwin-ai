"""RED: vulnerable current frontend versions and unqualified graph/config changes must fail."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = "2fc1bbd7904421d4a5a2c85995c28dbd9cdf0fce"


def test_frontend_runtime_uses_qualified_available_apk_revisions() -> None:
    """RED: removed APK revisions stop actual native image bootstrap."""
    from scripts.ci.frontend_security_profile import load_profile

    packages = load_profile(ROOT)["runtimePackages"]
    assert packages["alpine-release"] == "3.24.2-r0"
    assert packages["ca-certificates-bundle"] == "20260909-r0"
    docker = (ROOT / "frontend/Dockerfile").read_text()
    for name in ("alpine-release", "ca-certificates-bundle"):
        assert f"{name}={packages[name]}" in docker


def test_current_frontend_security_floor_and_scoped_truthful_alias() -> None:
    package = json.loads((ROOT / "frontend/package.json").read_text())
    assert package["dependencies"]["next"] == "16.3.8"
    assert package["devDependencies"]["eslint-config-next"] == "16.3.8"
    assert package["overrides"]["brace-expansion"] == "5.0.12"
    assert package["overrides"]["sharp"] == "^0.35.5"
    assert package["overrides"]["source-map-js"] == "1.2.2"
    assert package["overrides"]["@next/eslint-plugin-next"] == {
        "fast-glob": "npm:tinyglobby@0.2.17"
    }
    for entry in ("lint", "test", "build"):
        assert package["scripts"][entry].startswith("node scripts/check-next-glob-compat.mjs && ")


def current_pair() -> tuple[str, str]:
    return (
        (ROOT / "frontend/package.json").read_text(),
        (ROOT / "frontend/package-lock.json").read_text(),
    )


def validated_historical_text(path: str) -> str:
    from scripts.ci.frontend_security_profile import historical_text, validate_pair

    validate_pair(*current_pair(), root=ROOT)
    return historical_text(path, BASE, 30, ROOT)


def test_current_frontend_graph_proof_rejects_mutations_before_historical_acquisition() -> None:
    from scripts.ci.frontend_security_profile import ProfileError, load_profile, validate_pair

    package, lock = current_pair()
    validate_pair(package, lock, root=ROOT)
    parsed = json.loads(lock)
    profile = load_profile(ROOT)
    for name in profile["recordHashes"]:
        candidate = copy.deepcopy(parsed)
        candidate["packages"][name]["forged"] = True
        with pytest.raises(ProfileError):
            validate_pair(package, json.dumps(candidate), root=ROOT)
    candidate = copy.deepcopy(parsed)
    candidate["packages"]["node_modules/eslint"]["version"] = "0.0.0"
    with pytest.raises(ProfileError):
        validate_pair(package, json.dumps(candidate), root=ROOT)
    with pytest.raises(ProfileError):
        validate_pair(package + " ", json.dumps({**parsed, "foreign": True}), root=ROOT)


def test_frontend_profile_rejects_missing_duplicate_foreign_and_invalid_policy(
    tmp_path: Path,
) -> None:
    from scripts.ci.frontend_security_profile import ProfileError, load_profile

    profile = load_profile(ROOT)
    target = tmp_path / "docs/security/FRONTEND_DEPENDENCY_REFRESH.json"
    target.parent.mkdir(parents=True)
    for key in profile:
        candidate = {k: v for k, v in profile.items() if k != key}
        target.write_text(json.dumps(candidate))
        with pytest.raises(ProfileError):
            load_profile(tmp_path)
    for key, value in (
        ("foreign", True),
        ("verificationTimeoutSeconds", True),
        ("verificationTimeoutSeconds", 0),
        ("baseSha", "bad"),
    ):
        target.write_text(json.dumps({**profile, key: value}))
        with pytest.raises(ProfileError):
            load_profile(tmp_path)
    target.write_text(json.dumps(profile)[:-1] + ',"schemaVersion":1}')
    with pytest.raises(ProfileError):
        load_profile(tmp_path)


def test_real_node_profile_guard_rejects_duplicate_and_even_rehashed_custom_root_dir(
    tmp_path: Path,
) -> None:
    import subprocess
    from scripts.ci.frontend_security_profile import load_profile

    path = tmp_path / "profile.json"
    profile = load_profile(ROOT)
    path.write_text(json.dumps(profile))
    module = (ROOT / "frontend/scripts/frontend-security-profile.mjs").as_uri()
    code = """import {pathToFileURL} from 'node:url';
import {loadProfile,digest,validateEffectiveConfiguration} from MODULE;
const p=loadProfile(pathToFileURL(process.argv[1]));
const config={rules:{test:[2]},settings:{},languageOptions:{parser:{meta:{name:'test',version:'1'}}}};
p.effectiveConfigHashes.tsx=digest({rules:config.rules,settings:config.settings,parser:config.languageOptions.parser.meta});
validateEffectiveConfiguration(config,'tsx',p);
config.settings={next:{rootDir:'unqualified'}};
p.effectiveConfigHashes.tsx=digest({rules:config.rules,settings:config.settings,parser:config.languageOptions.parser.meta});
let rejected=false;try{validateEffectiveConfiguration(config,'tsx',p)}catch(e){rejected=e.message.includes('rootDir')}
if(!rejected)throw new Error('Coherent rehash bypassed unsupported rootDir gate');
""".replace("MODULE", json.dumps(module))

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["node", "--input-type=module", "--eval", code, "--", str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=profile["verificationTimeoutSeconds"],
        )

    assert run().returncode == 0
    path.write_text(json.dumps(profile)[:-1] + ',"schemaVersion":1}')
    assert run().returncode != 0
    path.write_text(json.dumps({**profile, "verificationTimeoutSeconds": 0}))
    assert run().returncode != 0


def test_coherently_rehashed_foreign_package_does_not_gain_scope(monkeypatch: Any) -> None:
    from scripts.ci import frontend_security_profile as module

    package, text = current_pair()
    lock = json.loads(text)
    profile = module.load_profile(ROOT)
    lock["packages"]["node_modules/eslint"]["version"] = "99.0.0"
    profile["lockHash"] = module.digest(lock)
    profile["recordHashes"]["node_modules/eslint"] = module.digest(
        lock["packages"]["node_modules/eslint"]
    )
    monkeypatch.setattr(module, "load_profile", lambda root: profile)
    with pytest.raises(module.ProfileError, match="Unqualified frontend dependency family"):
        module.validate_pair(package, json.dumps(lock), root=ROOT)


def test_coherently_rehashed_foreign_removal_cannot_normalize(monkeypatch: Any) -> None:
    """RED: a deleted unrelated package must not gain authority from profile rehashing."""
    from scripts.ci import frontend_security_profile as module

    package, text = current_pair()
    module.validate_pair(package, text, root=ROOT)
    lock = json.loads(text)
    profile = module.load_profile(ROOT)
    del lock["packages"]["node_modules/eslint"]
    profile["lockHash"] = module.digest(lock)
    profile["removedRecords"].append("node_modules/eslint")
    monkeypatch.setattr(module, "load_profile", lambda root: profile)
    with pytest.raises(module.ProfileError, match="Unqualified frontend dependency removal"):
        module.validate_pair(package, json.dumps(lock), root=ROOT)


def test_guard_covers_root_configuration_before_running_rules(tmp_path: Path) -> None:
    """RED: root-only unsupported settings survive a subdirectory-only qualification boundary."""
    import subprocess
    from scripts.ci.frontend_security_profile import load_profile

    for name in ("next.config.ts", "src/index.tsx", "ignored.ts", "node_modules/foreign.ts"):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture")
    module = (ROOT / "frontend/scripts/frontend-security-profile.mjs").as_uri()
    profile = load_profile(ROOT)
    code = """import assert from 'node:assert/strict';
import {digest,verifyActualConfigurations} from MODULE;
const root=process.argv[1], seen=[];
const config={rules:{test:[2]},settings:{},languageOptions:{parser:{meta:{name:'test',version:'1'}}}};
const hash=digest({rules:config.rules,settings:config.settings,parser:config.languageOptions.parser.meta});
const p={effectiveConfigHashes:{ts:hash,tsx:hash}};
let bad=false;
const eslint={isPathIgnored:async filename=>filename.endsWith('/ignored.ts'),
 calculateConfigForFile:async filename=>{seen.push(filename);return bad && filename.endsWith('/next.config.ts')
 ? {...config,settings:{next:{rootDir:'unqualified'}}}:config;}};
assert.equal(await verifyActualConfigurations(root,eslint,p),2);
assert(seen.includes(root+'/next.config.ts'));
bad=true;
await assert.rejects(verifyActualConfigurations(root,eslint,p),/rootDir/);
""".replace("MODULE", json.dumps(module))
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", code, "--", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=profile["verificationTimeoutSeconds"],
    )
    assert result.returncode == 0, result.stderr
