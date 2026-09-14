"""Offline work navigation and evidence integrity; no acceptance or private-access grant."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any

from scripts import work_archive as archive

REGISTRY = 'docs/work/registry.json'
SCHEMA = 'docs/work/templates/registry.schema.json'


class RecordError(ValueError):
    """Fixed diagnostics never echo source content or private paths."""


def need(condition: bool, code: str) -> None:
    if not condition:
        raise RecordError(code)


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(
        c in value for c in ('\n', '\r', '\x00', '|', '<', '>'))


def file_bytes(root: Path, path: Any, private_roots: list[str] | None = None) -> bytes:
    try:
        name = archive.relative(path)
        need(not ('.restricted' in name.split('/') or name.startswith('.evidence/')
                  or name == '.evidence' or name.split('/')[-1] == 'PRIVATE_INVENTORY.json'
                  or any(name == p or name.startswith(p + '/') for p in (private_roots or []))),
             'PRIVATE_REFERENCE')
        return archive.read(root, name)
    except archive.ArchiveError as exc:
        raise RecordError('UNSAFE_PATH') from exc
    except FileNotFoundError as exc:
        raise RecordError('FILE_UNAVAILABLE') from exc
    except OSError as exc:
        raise RecordError('UNSAFE_PATH') from exc


def document(root: Path, path: str, private_roots: list[str] | None = None) -> Any:
    try:
        return archive.decoded(file_bytes(root, path, private_roots))
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, RecordError):
            raise
        raise RecordError('JSON_INVALID') from exc


def exact(value: Any, keys: list[str]) -> None:
    need(isinstance(value, dict) and set(value) == set(keys), 'SHAPE_INVALID')


def descriptor(root: Path, item: Any, extra: set[str] | None = None,
               private_roots: list[str] | None = None) -> bytes:
    exact(item, list({'path', 'sha256', 'bytes'} | (extra or set())))
    need(type(item['bytes']) is int and item['bytes'] >= 0 and isinstance(item['sha256'], str)
         and re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None, 'DESCRIPTOR_INVALID')
    data = file_bytes(root, item['path'], private_roots)
    need(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'],
         'CONTENT_DRIFT')
    return data


def handoff_binding(work: dict[str, Any], evidence: bytes) -> str:
    return (f"PLAN_SHA256: {work['plan']['sha256']}\n"
            f"EVIDENCE_SHA256: {hashlib.sha256(evidence).hexdigest()}\n")


def render_index(data: dict[str, Any]) -> str:
    def rel(path: str) -> str:
        return '../../' + path

    lines = ['# Work index', '',
             'Generated from [registry.json](registry.json); edit the registry and regenerate.',
             'Start with [STATUS](../STATUS.md) and its current accepted contracts, then the',
             '[PRD](../PRD.md) and applicable amendments. [Process](PROCESS.md) defines handoffs.',
             'These are navigation records. Review state and folder location grant no authority.', '',
             '| Work | Kind | Current plan / source | State and next action |',
             '|---|---|---|---|']
    for work in data['works']:
        lines.append(f"| [{work['title']}]({rel(work['path'] + '/README.md')}) | {work['kind']} | "
                     f"[{work['plan']['role']}]({rel(work['plan']['path'])}) | "
                     f"[STATUS]({rel(work['statusRef'])}) · [handoff]({rel(work['handoff'])}) |")
    lines += ['', '## Observed issue ownership', '',
              'Snapshot coverage is recorded in the registry; verify live tracker state before action.', '',
              '| Issue | Owning work |', '|---|---|']
    for item in data['issueInventory']:
        lines.append(f"| [#{item['number']}](https://github.com/imrohitagrawal/narratwin-ai/issues/{item['number']}) "
                     f"{item['title']} | [{item['workId']}]({item['workId']}/README.md) |")
    return '\n'.join(lines) + '\n'


def validate(root: Path, *, git_timeout: float = archive.DEFAULT_GIT_TIMEOUT_SECONDS,
             profile_id: str | None = None,
             check_index: bool = True) -> dict[str, Any]:
    need(type(git_timeout) in (int, float) and math.isfinite(git_timeout)
         and git_timeout > 0, 'CONFIG_INVALID')
    try:
        root = archive.root_path(root)
    except (OSError, archive.ArchiveError) as exc:
        raise RecordError('ROOT_INVALID') from exc
    schema = document(root, SCHEMA)
    need(isinstance(schema, dict) and schema.get('schemaVersion') == 'WorkRecordsSchemaV1',
         'SCHEMA_UNSUPPORTED')
    data = document(root, REGISTRY)
    exact(data, schema['registryFields'])
    need(type(data['schemaVersion']) is int and data['schemaVersion'] == 1, 'SCHEMA_UNSUPPORTED')
    need(isinstance(data['privateRoots'], list) and bool(data['privateRoots']), 'PRIVATE_POLICY_INVALID')
    try:
        roots = [archive.relative(p) for p in data['privateRoots']]
        need(len(roots) == len(set(roots)), 'PRIVATE_POLICY_INVALID')
        tracked = subprocess.run(['git', '-C', str(root), 'ls-files', '-z'], check=True,
                                 capture_output=True, timeout=git_timeout).stdout.decode().split('\0')
        for path in tracked:
            need(not ('.restricted' in path.split('/') or path.startswith('.evidence/')
                      or path.endswith('/PRIVATE_INVENTORY.json')
                      or any(path == p or path.startswith(p + '/') for p in roots)), 'PRIVATE_TRACKED')
        for private in roots:
            result = subprocess.run(['git', '-C', str(root), 'check-ignore', '--no-index', '-q',
                                     private + '/work-record-probe'], check=False,
                                    capture_output=True, timeout=git_timeout)
            need(result.returncode == 0, 'PRIVATE_IGNORE_MISSING')
    except (subprocess.SubprocessError, OSError, UnicodeError, archive.ArchiveError) as exc:
        raise RecordError('GIT_CHECK_UNAVAILABLE') from exc
    need(isinstance(data['works'], list) and bool(data['works']), 'WORKS_INVALID')
    works: dict[str, Any] = {}
    # Establish the ID set before checking shape-dependent ownership or paths.
    for work in data['works']:
        exact(work, schema['workFields'])
        key = work['id']
        need(isinstance(key, str) and re.fullmatch('[a-z][a-z0-9-]*', key) is not None, 'WORK_ID_INVALID')
        need(key not in works, 'DUPLICATE_WORK')
        works[key] = work
    artifacts: dict[str, Any] = {}
    source_locators: set[tuple[str, str]] = set()
    original_bytes: set[tuple[str, int]] = set()
    uses: list[str] = []
    edges: dict[str, list[str]] = {key: [] for key in works}
    issue_owners: dict[int, str] = {}
    for key, work in works.items():
        need(work['kind'] in schema['kinds'] and all(text(work[k]) for k in
             ('title', 'owner', 'checkpoint')), 'WORK_INVALID')
        need(work['path'] == 'docs/work/' + key and work['handoff'] == work['path'] + '/HANDOFF.md'
             and work['evidenceIndex'] == work['path'] + '/evidence/INDEX.json', 'WORK_PATH_INVALID')
        for path in (work['path'] + '/README.md', work['path'] + '/DECISIONS.md'):
            file_bytes(root, path, roots)
        need(work['statusRef'] == 'docs/STATUS.md', 'STATUS_AUTHORITY_INVALID')
        file_bytes(root, work['statusRef'], roots)
        need(isinstance(work['authorityRefs'], list) and bool(work['authorityRefs']), 'AUTHORITY_INVALID')
        for path in work['authorityRefs']:
            file_bytes(root, path, roots)
        descriptor(root, work['plan'], {'role'}, roots)
        need(work['plan']['role'] in schema['planRoles'], 'PLAN_ROLE_INVALID')
        evidence = file_bytes(root, work['evidenceIndex'], roots)
        handoff = file_bytes(root, work['handoff'], roots).decode('utf-8')
        markers = '\n'.join(re.findall(r'^(?:PLAN|EVIDENCE)_SHA256:.*$', handoff, re.MULTILINE)) + '\n'
        need(markers == handoff_binding(work, evidence), 'HANDOFF_STALE')
        entries = document(root, work['evidenceIndex'], roots)
        exact(entries, ['schemaVersion', 'artifacts', 'uses'])
        need(type(entries['schemaVersion']) is int and entries['schemaVersion'] == 1
             and isinstance(entries['artifacts'], list) and isinstance(entries['uses'], list), 'EVIDENCE_INVALID')
        need(all(text(ref) for ref in entries['uses']) and len(set(entries['uses'])) == len(entries['uses']),
             'EVIDENCE_INVALID')
        uses.extend(entries['uses'])
        for item in entries['artifacts']:
            need(isinstance(item, dict), 'ARTIFACT_INVALID')
            locator = 'restrictedEvidenceRef' if 'restrictedEvidenceRef' in item else 'path'
            exact(item, schema['artifactFields'] + [locator])
            need(text(item['id']) and item['id'] not in artifacts, 'DUPLICATE_ARTIFACT')
            need(item['owner'] == key and text(item['revision']) and item['role'] in schema['artifactRoles']
                 and item['verification'] == 'METADATA_PINNED', 'ARTIFACT_INVALID')
            need(type(item['bytes']) is int and item['bytes'] >= 0 and isinstance(item['sha256'], str)
                 and re.fullmatch('[0-9a-f]{64}', item['sha256']) is not None, 'DESCRIPTOR_INVALID')
            need(isinstance(item['derivedFrom'], list) and all(text(v) for v in item['derivedFrom']),
                 'ARTIFACT_INVALID')
            if locator == 'path':
                need(item['custody'] == 'public', 'ARTIFACT_INVALID')
                descriptor(root, {k: item[k] for k in ('path', 'sha256', 'bytes')}, private_roots=roots)
            else:
                need(item['custody'] == 'restricted' and text(item[locator])
                     and item[locator].startswith('restricted-evidence:'), 'ARTIFACT_INVALID')
            identity = (locator, item[locator])
            need(identity not in source_locators, 'DUPLICATE_SOURCE')
            source_locators.add(identity)
            if item['role'] == 'original':
                fingerprint = (item['sha256'], item['bytes'])
                need(fingerprint not in original_bytes, 'DUPLICATE_SOURCE')
                original_bytes.add(fingerprint)
            artifacts[item['id']] = item
            uses.extend(item['derivedFrom'])
        need(isinstance(work['relationships'], list), 'RELATION_INVALID')
        relations = list(work['relationships'])
        if work['parent'] is not None:
            relations.append(dict(kind='parent', target=work['parent']))
        seen: set[tuple[str, str]] = set()
        for rel in relations:
            exact(rel, ['kind', 'target'])
            need(text(rel['kind']) and text(rel['target']), 'RELATION_INVALID')
            pair = (rel['kind'], rel['target'])
            need(rel['kind'] in schema['relationships'] and rel['target'] in works
                 and rel['target'] != key and pair not in seen, 'RELATION_INVALID')
            seen.add(pair)
            if rel['kind'] in ('parent', 'depends-on'):
                edges[key].append(rel['target'])
        need(isinstance(work['issues'], list), 'ISSUE_INVALID')
        for number in work['issues']:
            need(type(number) is int and number > 0 and number not in issue_owners, 'ISSUE_INVALID')
            issue_owners[number] = key
    need(all(ref in artifacts for ref in uses), 'ARTIFACT_REFERENCE_MISSING')
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(key: str) -> None:
        need(key not in visiting, 'DEPENDENCY_CYCLE')
        if key in done:
            return
        visiting.add(key)
        for target in edges[key]:
            visit(target)
        visiting.remove(key)
        done.add(key)

    for key in works:
        visit(key)
    source = archive.decoded(descriptor(root, data['inventorySource'], private_roots=roots))
    need(isinstance(source, dict) and isinstance(source.get('openIssues'), list), 'INVENTORY_INVALID')
    expected = {row['number']: row['title'] for row in source['openIssues']}
    need(len(expected) == len(source['openIssues']), 'INVENTORY_INVALID')
    actual: dict[int, str] = {}
    need(isinstance(data['issueInventory'], list), 'INVENTORY_INVALID')
    for row in data['issueInventory']:
        exact(row, ['number', 'title', 'workId'])
        need(type(row['number']) is int and row['number'] not in actual and text(row['title'])
             and row['workId'] == issue_owners.get(row['number']), 'INVENTORY_INVALID')
        actual[row['number']] = row['title']
    need(actual == expected and set(issue_owners) == set(expected), 'INVENTORY_COVERAGE')
    if check_index:
        need(file_bytes(root, 'docs/work/INDEX.md', roots).decode() == render_index(data), 'INDEX_STALE')
    for entry in ('README.md', 'docs/STATUS.md', 'docs/CODEX_OPERATING_MODEL.md'):
        need('docs/work/INDEX.md' in file_bytes(root, entry, roots).decode(), 'ENTRYPOINT_MISSING')
    bridge = file_bytes(root, 'CLAUDE.md', roots).decode()
    need('AGENTS.md' in bridge and 'docs/work/INDEX.md' in bridge, 'ENTRYPOINT_MISSING')
    need('docs/STATUS.md' in file_bytes(root, 'AGENTS.md', roots).decode(), 'ENTRYPOINT_MISSING')
    need(isinstance(data['profiles'], list), 'PROFILE_INVALID')
    profiles: dict[str, Any] = {}
    for profile in data['profiles']:
        exact(profile, ['id', 'kind', 'descriptor'])
        need(text(profile['id']) and text(profile['kind']) and profile['id'] not in profiles, 'PROFILE_INVALID')
        descriptor(root, profile['descriptor'], private_roots=roots)
        profiles[profile['id']] = profile
    if profile_id is not None:
        need(profile_id in profiles, 'PROFILE_MISSING')
        profile = profiles[profile_id]
        need(profile['kind'] == 'g1-originals-v1', 'PROFILE_UNSUPPORTED')
        config = document(root, profile['descriptor']['path'], roots)
        exact(config, ['schemaVersion', 'indexPath', 'bindings'])
        need(type(config['schemaVersion']) is int and config['schemaVersion'] == 1, 'PROFILE_INVALID')
        file_bytes(root, config['indexPath'], roots)
        try:
            proof = archive.public_index(root, archive.relative(config['indexPath']), git_timeout)
        except (archive.ArchiveError, OSError) as exc:
            raise RecordError('PROFILE_FAILED') from exc
        need(isinstance(config['bindings'], dict) and
             set(config['bindings']) == {item['id'] for item in proof['artifacts']}, 'PROFILE_BINDING_INVALID')
        for source_item in proof['artifacts']:
            target = artifacts.get(config['bindings'][source_item['id']])
            need(isinstance(target, dict) and all(target.get(k) == source_item[k]
                 for k in ('sha256', 'bytes', 'restrictedEvidenceRef')), 'PROFILE_BINDING_INVALID')
    return dict(publicIndex='VALID', workCount=len(works), issueCount=len(actual),
                artifactCount=len(artifacts), profile=profile_id, privateAvailability='NOT_CHECKED',
                backup='UNPROVED', semanticAcceptance='NOT_GRANTED',
                effectiveConfiguration=dict(gitTimeoutSeconds=git_timeout))


def main() -> int:
    parser = archive.SafeParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--git-timeout-seconds', type=archive.positive_seconds,
                        default=archive.DEFAULT_GIT_TIMEOUT_SECONDS)
    parser.add_argument('--profile')
    parser.add_argument('--write-index', action='store_true')
    args = parser.parse_args()
    try:
        root = archive.root_path(args.repo_root)
        if args.write_index:
            # Validate all public sources before generating any links from untrusted metadata.
            validate(root, git_timeout=args.git_timeout_seconds, profile_id=args.profile, check_index=False)
            # Existing destination must be a regular safe file; never follow a symlink.
            file_bytes(root, 'docs/work/INDEX.md')
            (root / 'docs/work/INDEX.md').write_text(render_index(document(root, REGISTRY)))
        print(json.dumps(validate(root, git_timeout=args.git_timeout_seconds, profile_id=args.profile), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as exc:
        code = str(exc) if isinstance(exc, RecordError) else 'INVALID_OR_UNAVAILABLE'
        print(json.dumps(dict(publicIndex='FAILED', error=code, privateAvailability='NOT_CHECKED',
                              backup='UNPROVED', semanticAcceptance='NOT_GRANTED')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
