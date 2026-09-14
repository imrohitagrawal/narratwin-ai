"""Public, offline documentation navigation; never capability or approval evidence."""
from __future__ import annotations

import argparse
import json
import math
import posixpath
from pathlib import Path
import re
import subprocess
from typing import Any
from urllib.parse import unquote, urlsplit

from scripts import work_archive as files


class CatalogError(ValueError):
    """Fixed public diagnostics contain no document contents."""


def require(value: bool, code: str) -> None:
    if not value:
        raise CatalogError(code)


def shape(value: Any, keys: str) -> None:
    require(isinstance(value, dict) and set(value) == set(keys.split()), 'SHAPE_INVALID')


def label(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(
        c in value for c in '\n\r\x00|<>')


def prose(value: str) -> str:
    """Supported subset: ATX headings, inline links; omit comments and fenced examples."""
    value = re.sub(r'<!--.*?-->', '', value, flags=re.S)
    result: list[str] = []
    fence = ''
    for line in value.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            fence_marker = marker[1]
            if not fence:
                fence = fence_marker
            elif fence_marker[0] == fence[0] and len(fence_marker) >= len(fence):
                fence = ''
            continue
        if not fence:
            result.append(line)
    return '\n'.join(result)


def anchors(value: str) -> set[str]:
    used: set[str] = set()
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', prose(value), re.M):
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        unique, number = slug, 0
        while unique in used:
            number += 1
            unique = f'{slug}-{number}'
        used.add(unique)
    for explicit in re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']\s*>', prose(value)):
        require(explicit not in used, 'ANCHOR_AMBIGUOUS')
        used.add(explicit)
    return used


def links(value: str) -> list[str]:
    value = re.sub(r'(`+)(?!`)(.*?)\1(?!`)', '', prose(value), flags=re.S)
    return re.findall(r'(?<![\\!])\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"\n]*")?\)', value)


def declarations(value: str, field: str, *, include_label: bool = False) -> list[str]:
    """Retain existing heading and inline/bullet metadata, including wrapped restrictions."""
    lines = prose(value).splitlines()
    values = []
    for index, line in enumerate(lines):
        heading = re.fullmatch(r'##\s+' + field + r'\s*', line, re.I)
        inline = re.match(r'^\s*(?:-\s+)?' + field + r':\s*(.*)$', line, re.I)
        if not heading and not inline:
            continue
        parts = [inline[1]] if inline else []
        for following in lines[index + 1:]:
            if re.match(r'^#{1,6}\s|^\s*-\s+\w|^\w[\w -]*:', following):
                break
            if not following.strip() and parts and not heading:
                break
            if following.strip():
                parts.append(following.strip())
        prefix = re.sub(r':.*$', ':', line).strip().removeprefix('- ') + ' ' if inline else line.lstrip('# ') + ': '
        values.append((prefix if include_label else '') + ' '.join(parts).strip())
    return values


def source_status(value: str) -> str:
    values = declarations(value, 'Status')
    return values[0] if len(values) == 1 and values[0] else 'needs-review: missing or ambiguous source status'


def local_target(source: str, target: str) -> tuple[str, str] | None:
    url = urlsplit(target)
    if url.scheme or url.netloc:
        require(url.scheme in {'https', 'http', 'mailto'}, 'LINK_SCHEME_INVALID')
        return None
    path = unquote(url.path)
    require(not path.startswith('/'), 'PATH_UNSAFE')
    path = posixpath.normpath(posixpath.join(posixpath.dirname(source), path)) if path else source
    return path, unquote(url.fragment)


def relative(source: str, target: str) -> str:
    path, marker, fragment = target.partition('#')
    return posixpath.relpath(path, posixpath.dirname(source)) + (marker + fragment if marker else '')


class Catalog:
    def __init__(self, root: Path, config: str, timeout: float):
        require(type(timeout) in (float, int) and math.isfinite(timeout) and timeout > 0,
                'CONFIG_INVALID')
        self.root = files.root_path(root)
        raw = subprocess.run(['git', '-C', str(self.root), 'ls-files', '-z'],
                             check=True, capture_output=True, timeout=timeout).stdout
        self.tracked = set(raw.decode().split('\0')) - {''}
        self.private = ['.evidence', 'docs/work-archive/.restricted']
        self.config = config
        self.data = files.decoded(self.read(config))
        shape(self.data, 'schemaVersion title privateRoots inventory entries collections templates '
              'routes impacts forms adr outputs checkedLinks requiredLinks')
        require(self.data['schemaVersion'] == 'DocumentationNavigationV1', 'SCHEMA_UNSUPPORTED')
        require(label(self.data['title']), 'TITLE_INVALID')
        require(isinstance(self.data['privateRoots'], list) and bool(self.data['privateRoots']),
                'PRIVATE_POLICY_INVALID')
        for name in self.data['privateRoots']:
            self.private.append(files.relative(name))
        for name in self.tracked:
            self.safe(name)
        self.entries: dict[str, Any] = {}
        self.contents: dict[str, str] = {}

    def safe(self, name: str) -> None:
        files.relative(name)
        require('.restricted' not in name.split('/') and name.split('/')[-1] != 'PRIVATE_INVENTORY.json'
                and not any(name == p or name.startswith(p + '/') for p in self.private),
                'PRIVATE_REFERENCE')

    def read(self, name: str) -> bytes:
        self.safe(name)
        require(name in self.tracked, 'TARGET_UNTRACKED_OR_MISSING')
        return files.read(self.root, name)

    def target(self, name: str) -> str:
        path, _, fragment = name.partition('#')
        if any(path + '/' == x['prefix'] for x in self.data['collections']):
            self.safe(path)
            require(not fragment and any(p.startswith(path + '/') for p in self.tracked), 'COLLECTION_LINK_INVALID')
            cursor = self.root
            for part in path.split('/'):
                cursor = cursor / part
                require(not cursor.is_symlink() and cursor.is_dir(), 'PATH_UNSAFE')
            return ''
        value = self.contents.get(path)
        if value is None:
            value = self.read(path).decode('utf-8')
            self.contents[path] = value
        if fragment:
            require(fragment in anchors(value), 'ANCHOR_MISSING')
        return value

    def validate(self, *, generated: bool = True) -> dict[str, Any]:
        d = self.data
        for key in ('entries', 'collections', 'templates', 'routes', 'impacts', 'forms',
                    'checkedLinks', 'requiredLinks'):
            require(isinstance(d[key], list), 'SHAPE_INVALID')
        require(bool(d['entries']) and bool(d['routes']), 'EMPTY_CATALOG')
        owners: set[str] = set()
        for entry in d['entries']:
            shape(entry, 'id path title role owner updateWhen')
            require(all(label(v) for v in entry.values()), 'ENTRY_INVALID')
            require(re.fullmatch('[a-z][a-z0-9-]*', entry['id']) is not None, 'ID_INVALID')
            require(entry['id'] not in self.entries and entry['path'] not in owners, 'DUPLICATE_OWNER')
            require('#' not in entry['path'], 'OWNER_MUST_BE_FILE')
            self.safe(entry['path'])
            require(entry['path'] in self.tracked, 'TARGET_UNTRACKED_OR_MISSING')
            owners.add(entry['path'])
            self.entries[entry['id']] = entry
        shape(d['outputs'], 'documents templates adrs')
        outputs = list(d['outputs'].values())
        require(len(set(outputs)) == 3 and all(x in owners for x in outputs), 'OUTPUT_INVALID')
        for entry in self.entries.values():
            if entry['path'] not in outputs:
                self.target(entry['path'])
        prefixes: set[str] = set()
        for item in d['collections']:
            shape(item, 'prefix title owner role updateWhen')
            require(all(label(v) for v in item.values()), 'COLLECTION_INVALID')
            require(item['prefix'].endswith('/'), 'COLLECTION_INVALID')
            self.safe(item['prefix'][:-1])
            require(item['prefix'] not in prefixes, 'AMBIGUOUS_COLLECTION')
            prefixes.add(item['prefix'])
        shape(d['inventory'], 'roots files rootMarkdown')
        require(type(d['inventory']['rootMarkdown']) is bool, 'INVENTORY_INVALID')
        require(all(isinstance(d['inventory'][k], list) for k in ('roots', 'files')), 'INVENTORY_INVALID')
        for prefix in d['inventory']['roots']:
            require(isinstance(prefix, str) and prefix.endswith('/'), 'INVENTORY_INVALID')
            self.safe(prefix[:-1])
        for name in d['inventory']['files']:
            self.safe(name)
            require(name in self.tracked, 'INVENTORY_MISSING')
        covered = {p for p in self.tracked if (d['inventory']['rootMarkdown'] and '/' not in p and p.endswith('.md'))
                   or p in d['inventory']['files'] or any(
            p.startswith(x) for x in d['inventory']['roots'])}
        require(bool(covered), 'EMPTY_INVENTORY')
        for path in covered:
            if path not in owners:
                matches = [x for x in prefixes if path.startswith(x)]
                require(bool(matches), 'DOCUMENT_UNCLASSIFIED')
        template_ids: set[str] = set()
        template_targets: set[str] = set()
        for item in d['templates']:
            shape(item, 'id entry anchor title useWhen')
            require(all(label(item[k]) for k in ('id', 'entry', 'title', 'useWhen'))
                    and isinstance(item['anchor'], str), 'TEMPLATE_INVALID')
            require(item['entry'] in self.entries, 'TEMPLATE_OWNER_MISSING')
            target = self.entries[item['entry']]['path'] + ('#' + item['anchor'] if item['anchor'] else '')
            require(item['id'] not in template_ids and target not in template_targets, 'DUPLICATE_TEMPLATE')
            template_ids.add(item['id'])
            template_targets.add(target)
            self.target(target)
        template_files = {x.split('#')[0] for x in template_targets}
        for path in covered:
            if ('/templates/' in path or '/ISSUE_TEMPLATE/' in path or 'pull_request_template' in path):
                require(path in template_files or path in outputs, 'TEMPLATE_UNREGISTERED')
        for item in d['routes']:
            shape(item, 'audience question entries')
            require(label(item['audience']) and label(item['question']), 'ROUTE_INVALID')
            self.refs(item['entries'])
        areas: set[str] = set()
        for item in d['impacts']:
            shape(item, 'area implementation entries owner updateWhen')
            require(all(label(item[k]) for k in ('area', 'owner', 'updateWhen')), 'IMPACT_INVALID')
            require(item['area'] not in areas, 'DUPLICATE_IMPACT')
            areas.add(item['area'])
            require(isinstance(item['implementation'], list) and bool(item['implementation']), 'IMPACT_INVALID')
            for name in item['implementation']:
                self.safe(name.rstrip('/'))
                require(any(p.startswith(name) if name.endswith('/') else p == name for p in self.tracked),
                        'IMPACT_PATH_MISSING')
            self.refs(item['entries'])
        self.validate_forms(template_files)
        adr_rows = self.adr_rows()
        rendered = self.render(adr_rows)
        if generated:
            for path, value in rendered.items():
                require(self.read(path).decode() == value, 'GENERATED_DRIFT')
        # Link checks also validate the to-be-generated pages before writing them.
        self.contents.update(rendered)
        for path in d['checkedLinks']:
            value = self.target(path)
            for link in links(value):
                target = local_target(path, link)
                if target is not None:
                    name, fragment = target
                    self.target(name + ('#' + fragment if fragment else ''))
        for item in d['requiredLinks']:
            shape(item, 'source target')
            matching = [t for link in links(self.target(item['source']))
                        if (t := local_target(item['source'], link)) is not None and t[0] == item['target']]
            require(bool(matching), 'REQUIRED_LINK_MISSING')
            for name, fragment in matching:
                self.target(name + ('#' + fragment if fragment else ''))
        return {'schemaVersion': d['schemaVersion'], 'documentsClassified': len(covered),
                'templates': len(template_ids), 'adrs': len(adr_rows),
                'capabilityAcceptance': 'NOT_PROVED', 'semanticCompleteness': 'NOT_PROVED',
                'rendered': rendered}

    def refs(self, refs: Any) -> None:
        require(isinstance(refs, list) and bool(refs) and len(refs) == len(set(refs)), 'ROUTE_INVALID')
        require(all(x in self.entries for x in refs), 'ROUTE_TARGET_MISSING')

    def validate_forms(self, template_files: set[str]) -> None:
        seen: set[str] = set()
        for rule in self.data['forms']:
            shape(rule, 'path requiredIds retainedIds retainedChecks')
            require(rule['path'] in template_files and rule['path'] not in seen, 'FORM_UNREGISTERED')
            seen.add(rule['path'])
            form = files.decoded(self.read(rule['path']))
            require(isinstance(form, dict) and label(form.get('name')) and label(form.get('description'))
                    and isinstance(form.get('body'), list), 'FORM_INVALID')
            ids: set[str] = set()
            required: set[str] = set()
            checks: dict[str, set[str]] = {}
            for field in form['body']:
                require(isinstance(field, dict) and field.get('type') in
                        {'markdown', 'input', 'textarea', 'checkboxes', 'dropdown'}, 'FORM_INVALID')
                require(isinstance(field.get('attributes'), dict), 'FORM_INVALID')
                if field['type'] == 'markdown':
                    require(label(field['attributes'].get('value')), 'FORM_INVALID')
                    continue
                key = field.get('id')
                require(label(key) and re.fullmatch(r'[A-Za-z0-9_-]+', key) is not None
                        and key not in ids and label(field['attributes'].get('label')), 'FORM_FIELD_INVALID')
                ids.add(key)
                attributes = field['attributes']
                if field['type'] in {'dropdown', 'checkboxes'}:
                    options = attributes.get('options')
                    require(isinstance(options, list) and bool(options), 'FORM_OPTIONS_INVALID')
                    if field['type'] == 'dropdown':
                        require(all(label(x) for x in options) and len(options) == len(set(options)), 'FORM_OPTIONS_INVALID')
                        require(type(attributes.get('multiple', False)) is bool, 'FORM_OPTIONS_INVALID')
                        if 'default' in attributes:
                            require(type(attributes['default']) is int and 0 <= attributes['default'] < len(options)
                                    and all(x.lower() not in {'none', 'n/a'} for x in options), 'FORM_OPTIONS_INVALID')
                    else:
                        require(all(isinstance(x, dict) and label(x.get('label'))
                                    and type(x.get('required', False)) is bool for x in options), 'FORM_OPTIONS_INVALID')
                        require(len({x['label'] for x in options}) == len(options), 'FORM_OPTIONS_INVALID')
                        checks[key] = {x['label'] for x in options if x.get('required')}
                validation = field.get('validations', {})
                require(isinstance(validation, dict) and type(validation.get('required', False)) is bool,
                        'FORM_INVALID')
                if validation.get('required'):
                    required.add(key)
            require(isinstance(rule['requiredIds'], list) and isinstance(rule['retainedIds'], list), 'FORM_INVALID')
            require(set(rule['requiredIds']) <= required and set(rule['retainedIds']) <= ids, 'FORM_REQUIREMENT_MISSING')
            require(isinstance(rule['retainedChecks'], dict), 'FORM_INVALID')
            for key, expected in rule['retainedChecks'].items():
                require(isinstance(expected, list) and bool(expected) and all(label(x) for x in expected), 'FORM_INVALID')
                require(key in checks and set(expected) <= checks[key], 'FORM_REQUIREMENT_MISSING')
        native = {p for p in template_files if '/ISSUE_TEMPLATE/' in p and p.endswith(('.yml', '.yaml'))}
        require(native == seen, 'FORM_UNREGISTERED')

    def adr_rows(self) -> list[tuple[str, str, str, str]]:
        cfg = self.data['adr']
        shape(cfg, 'prefix legacyCollisions')
        require(isinstance(cfg['prefix'], str) and cfg['prefix'].endswith('/'), 'ADR_INVALID')
        self.safe(cfg['prefix'][:-1])
        require(isinstance(cfg['legacyCollisions'], dict), 'ADR_INVALID')
        groups: dict[str, list[str]] = {}
        rows = []
        sources = []
        for name in sorted(self.tracked):
            if not name.startswith(cfg['prefix']) or not re.fullmatch(r'\d{4}-.+\.md', Path(name).name):
                continue
            groups.setdefault(Path(name).name[:4], []).append(name)
            sources.append(name)
        for name in sources:
            source = self.target(name)
            status = source_status(source)
            # Preserve source links, including supersession, and check their destinations.
            for link in links(source):
                target = local_target(name, link)
                if target is not None:
                    self.target(target[0] + ('#' + target[1] if target[1] else ''))
            supersession = declarations(source, r'(?:Supersedes|Superseded by|Supersession)', include_label=True)
            # Older status sections sometimes state supersession without a colon.
            if not supersession:
                supersession = re.findall(r'^Superseded by .+$', prose(source), re.M | re.I)
            relation = '; '.join(supersession) if supersession else 'Not declared; effective lifecycle unproved'
            def path_link(match: re.Match[str]) -> str:
                path = match[1]
                self.target(path)
                return f'[{path}]({relative(name, path)})'
            relation = re.sub(r'`((?:[^`\n]+/)\d{4}-[^`\n]+\.md)`', path_link, relation)
            def id_link(match: re.Match[str]) -> str:
                choices = groups.get(match[1], [])
                if len(choices) != 1:
                    return match[0] + ' (needs-review: ambiguous or missing source)'
                return f'[{match[0]}]({relative(name, choices[0])})'
            relation = re.sub(r'\bADR (\d{4})\b(?![\w/-])', id_link, relation)
            rows.append((Path(name).stem, name, status, relation))
        collisions = {k: v for k, v in groups.items() if len(v) > 1}
        require(collisions == cfg['legacyCollisions'], 'ADR_COLLISION_DRIFT')
        return rows

    def render(self, adrs: list[tuple[str, str, str, str]]) -> dict[str, str]:
        d = self.data
        doc, template, adr = (d['outputs'][k] for k in ('documents', 'templates', 'adrs'))
        def ref(source: str, key: str) -> str:
            e = self.entries[key]
            return f"[{e['title']}]({relative(source, e['path'])})"
        lines = [f"# {d['title']}", '', 'Generated navigation from the repository catalog; it grants no approval.', '',
                 '| Start here | Question | Read in order |', '|---|---|---|']
        for route in d['routes']:
            lines.append(f"| {route['audience']} | {route['question']} | " + ' → '.join(ref(doc, k) for k in route['entries']) + ' |')
        lines += ['', '## Document owners and update triggers', '', '| Document | Role | Maintainer role | Update when |', '|---|---|---|---|']
        for entry in d['entries']:
            lines.append(f"| {ref(doc, entry['id'])} | {entry['role']} | {entry['owner']} | {entry['updateWhen']} |")
        lines += ['', '## Collections', '', 'Collection roles describe storage, not acceptance of every child.', '',
                  '| Location | Purpose | Maintainer role | Update when |', '|---|---|---|---|']
        for item in d['collections']:
            lines.append(f"| [{item['prefix']}]({relative(doc, item['prefix'])}/) | {item['role']} | {item['owner']} | {item['updateWhen']} |")
        t = ['# Template catalog', '', 'Generated links to single canonical sources. Tool-native locations stay intact.', '',
             'Whole-source entries include their embedded forms; frequent sections are linked directly below.', '',
             '| Template or embedded form | Use when |', '|---|---|']
        for item in d['templates']:
            target = self.entries[item['entry']]['path'] + ('#' + item['anchor'] if item['anchor'] else '')
            t.append(f"| [{item['title']}]({relative(template, target)}) | {item['useWhen']} |")
        a = ['# Architecture decision registry', '',
             'Stable identity is the complete filename below. Existing numeric collisions are explicit aliases;',
             'original files are retained. Status text is quoted from each source, not an acceptance verdict.',
             'Missing or ambiguous status needs review. Absence of a supersession link proves no lifecycle claim.', '',
             '| Stable alias | Source-declared status | Source-declared supersession |', '|---|---|---|']
        for alias, path, status, relation in adrs:
            # Use source-relative links for any links embedded in the source status.
            status = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: self.status_link(path, adr, m), status)
            relation = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: self.status_link(path, adr, m), relation)
            a.append(f'| [{alias}]({relative(adr, path)}) | {status.replace("|", "&#124;")} | {relation.replace("|", "&#124;")} |')
        return {doc: '\n'.join(lines) + '\n', template: '\n'.join(t) + '\n', adr: '\n'.join(a) + '\n'}

    @staticmethod
    def status_link(source: str, output: str, match: re.Match[str]) -> str:
        target = local_target(source, match[2])
        href = match[2] if target is None else relative(output, target[0]) + ('#' + target[1] if target[1] else '')
        return f'[{match[1]}]({href})'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--git-timeout-seconds', type=files.positive_seconds, default=files.DEFAULT_GIT_TIMEOUT_SECONDS)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--area', help='Show configured impact references; does not enforce changed-code impact.')
    args = parser.parse_args()
    try:
        catalog = Catalog(args.root, args.catalog, args.git_timeout_seconds)
        result = catalog.validate(generated=not args.write)
        if args.area:
            matching = [x for x in catalog.data['impacts'] if x['area'] == args.area]
            require(len(matching) == 1, 'IMPACT_AREA_UNKNOWN')
            result['impactRoute'] = matching[0]
        rendered = result.pop('rendered')
        if args.write:
            for name, value in rendered.items():
                catalog.safe(name)
                # Existing output must be a normal tracked file before mutation.
                catalog.read(name)
            for name, value in rendered.items():
                (catalog.root / name).write_text(value, encoding='utf-8')
        print(json.dumps(result, sort_keys=True))
        return 0
    except (CatalogError, files.ArchiveError, OSError, ValueError, TypeError, KeyError,
            subprocess.SubprocessError) as exc:
        code = str(exc) if isinstance(exc, (CatalogError, files.ArchiveError)) else 'CATALOG_INVALID'
        print(json.dumps({'status': 'invalid', 'code': code}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
