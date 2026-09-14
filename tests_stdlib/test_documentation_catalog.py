"""Behavioral contracts: each negative changes a valid portable repository fixture."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import documentation_catalog as nav
from scripts import guardrails_check as guardrails


class HostedCompatibilityTests(unittest.TestCase):
    def test_catalog_source_passes_actual_repository_secret_scan(self):
        # Exercise the hosted scanner on this source even before Git tracks it.
        source = Path(nav.__file__).resolve()
        with patch.object(guardrails, 'iter_text_files', return_value=[source]), \
                patch.object(guardrails, 'failures', []):
            guardrails.check_secrets()
            self.assertEqual(guardrails.failures, [])


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write('START.md', '[Guide](handbook/process.md)\n')
        self.write('handbook/process.md', '# Process\n\n## Intake\n\nReal guidance.\n')
        self.write('handbook/home.md', '')
        self.write('handbook/forms.md', '')
        self.write('handbook/decisions.md', '')
        self.write('decisions/0001-example.md', '# Decision\n\n## Status\n\nProposed\n')
        self.write('service/entry.py', '# fixture\n')
        entries = []
        for key, path in [('start', 'START.md'), ('process', 'handbook/process.md'),
                          ('home', 'handbook/home.md'), ('forms', 'handbook/forms.md'),
                          ('decisions', 'handbook/decisions.md'), ('catalog', 'nav.json')]:
            entries.append(dict(id=key, path=path, title=key, role='reference',
                                owner='Maintainer', updateWhen='Contract changes'))
        self.data = dict(
            schemaVersion='DocumentationNavigationV1', title='Other project',
            privateRoots=['private-store'], inventory=dict(roots=['handbook/', 'decisions/'], files=['START.md', 'nav.json'], rootMarkdown=True),
            entries=entries, collections=[dict(prefix='decisions/', title='Decisions', owner='Architect',
                                              role='Source declared', updateWhen='Design changes')],
            templates=[dict(id='intake', entry='process', anchor='intake', title='Intake', useWhen='A new idea')],
            routes=[dict(audience='New designer', question='Where to start?', entries=['start', 'process'])],
            impacts=[dict(area='service', implementation=['service/'], entries=['process'],
                          owner='Engineer', updateWhen='Contract changes')],
            forms=[], adr=dict(prefix='decisions/', legacyCollisions={}),
            outputs=dict(documents='handbook/home.md', templates='handbook/forms.md', adrs='handbook/decisions.md'),
            checkedLinks=['START.md', 'handbook/home.md', 'handbook/forms.md', 'handbook/decisions.md'],
            requiredLinks=[dict(source='START.md', target='handbook/process.md')])
        self.save()
        result = self.load().validate(generated=False)
        for path, value in result['rendered'].items():
            self.write(path, value)
        self.track()

    def write(self, name, text):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)

    def track(self):
        subprocess.run(['git', '-C', str(self.root), 'add', '.'], check=True)

    def save(self):
        self.write('nav.json', json.dumps(self.data))
        self.track()

    def load(self, timeout=0.625):
        return nav.Catalog(self.root, 'nav.json', timeout)

    def rejects(self, code):
        with self.assertRaisesRegex(nav.CatalogError, '^' + code + '$'):
            self.load().validate(generated=False)

    def test_portable_positive_has_no_github_or_narratwin_paths(self):
        result = self.load().validate()
        self.assertEqual((result['documentsClassified'], result['templates'], result['adrs']), (7, 1, 1))
        self.assertEqual(result['capabilityAcceptance'], 'NOT_PROVED')

    def test_missing_canonical_procedure_rejected(self):
        # Red if registered sources need not exist.
        (self.root / 'handbook/process.md').unlink()
        with self.assertRaises(OSError):
            self.load().validate()

    def test_duplicate_owner_rejected(self):
        self.data['entries'].append({**self.data['entries'][1], 'id': 'alias'})
        self.save()
        self.rejects('DUPLICATE_OWNER')

    def test_unclassified_document_rejected(self):
        self.write('handbook/unregistered.md', '# Unregistered\n')
        self.track()
        self.rejects('DOCUMENT_UNCLASSIFIED')

    def test_new_root_markdown_cannot_escape_inventory(self):
        self.write('NEW_PROJECT_GUIDE.md', '# An unregistered root guide\n')
        self.track()
        self.rejects('DOCUMENT_UNCLASSIFIED')

    def test_collection_positive_and_tied_owner_negative(self):
        self.write('decisions/notes.md', 'Historical notes\n')
        self.track()
        self.load().validate(generated=False)
        self.data['collections'].append(dict(self.data['collections'][0]))
        self.save()
        self.rejects('AMBIGUOUS_COLLECTION')

    def test_missing_template_anchor_rejected(self):
        self.data['templates'][0]['anchor'] = 'not-present'
        self.save()
        self.rejects('ANCHOR_MISSING')

    def test_duplicate_template_reference_rejected(self):
        self.data['templates'].append({**self.data['templates'][0], 'id': 'another-id'})
        self.save()
        self.rejects('DUPLICATE_TEMPLATE')

    def test_template_cannot_hide_under_collection(self):
        self.write('handbook/templates/extra.md', '# Extra\n')
        self.data['collections'].append(dict(prefix='handbook/templates/', title='Forms', owner='Engineer',
                                              role='Templates', updateWhen='Form changes'))
        self.save()
        self.rejects('TEMPLATE_UNREGISTERED')

    def test_commented_and_fenced_links_do_not_satisfy_entry_route(self):
        self.write('START.md', '<!-- [Guide](handbook/process.md) -->\n```md\n[Guide](handbook/process.md)\n```\n')
        self.rejects('REQUIRED_LINK_MISSING')

    def test_broken_actual_link_rejected_even_with_expected_comment(self):
        self.write('START.md', '<!-- handbook/process.md -->\n[Guide](handbook/missing.md)\n')
        self.rejects('TARGET_UNTRACKED_OR_MISSING')

    def test_non_navigation_markdown_cannot_satisfy_required_link(self):
        for text in ('`[Guide](handbook/process.md)`', r'\[Guide](handbook/process.md)',
                     '![Guide](handbook/process.md)'):
            with self.subTest(text=text):
                self.write('START.md', text + '\n')
                self.rejects('REQUIRED_LINK_MISSING')

    def test_anchor_and_source_relative_link_positive(self):
        self.write('START.md', '[Guide](handbook/process.md#intake)\n')
        self.load().validate()

    def test_required_link_only_source_checks_its_actual_fragment(self):
        self.data['checkedLinks'].remove('START.md')
        self.save()
        self.write('START.md', '[Guide](handbook/process.md#intake)\n')
        self.load().validate()
        self.write('START.md', '[Guide](handbook/process.md#missing-anchor)\n')
        self.rejects('ANCHOR_MISSING')

    def test_generated_drift_rejected(self):
        self.write('handbook/forms.md', '# Fake catalog\n')
        with self.assertRaisesRegex(nav.CatalogError, 'GENERATED_DRIFT'):
            self.load().validate()

    def test_private_target_is_never_read(self):
        self.write('private-store/secret.md', 'synthetic fixture only')
        self.write('START.md', '[Private](private-store/secret.md)\n')
        seen = []
        original = nav.files.read
        def spy(root, name):
            seen.append(name)
            return original(root, name)
        with patch.object(nav.files, 'read', side_effect=spy):
            self.rejects('PRIVATE_REFERENCE')
        self.assertNotIn('private-store/secret.md', seen)

    def test_symlink_target_and_escape_rejected(self):
        (self.root / 'handbook/process.md').unlink()
        (self.root / 'handbook/process.md').symlink_to(self.root / 'START.md')
        with self.assertRaises(OSError):
            self.load().validate()
        self.assertEqual(nav.local_target('START.md', '../outside.md'), ('../outside.md', ''))
        with self.assertRaises(nav.files.ArchiveError):
            self.load().read('../outside.md')

    def test_unknown_impact_reference_rejected(self):
        self.data['impacts'][0]['entries'] = ['missing']
        self.save()
        self.rejects('ROUTE_TARGET_MISSING')

    def test_adr_status_ambiguity_not_inferred_accepted(self):
        self.write('decisions/0001-example.md', '# Decision\n\nNo lifecycle was declared.\n')
        rows = self.load().validate(generated=False)['rendered']['handbook/decisions.md']
        self.assertIn('needs-review: missing or ambiguous source status', rows)

    def test_legacy_status_formats_preserve_restrictions(self):
        for declaration in ('Status: Accepted for this issue scope only',
                            '- Status: proposed; no implementation authority until reviewed\n  merge and closeout'):
            with self.subTest(declaration=declaration):
                self.write('decisions/0001-example.md', '# Decision\n\n' + declaration + '\n\n## Context\n\nContext.\n')
                rows = self.load().validate(generated=False)['rendered']['handbook/decisions.md']
                self.assertIn(declaration.split(': ', 1)[1].replace('\n  ', ' '), rows)

    def test_empty_or_conflicting_source_status_needs_review(self):
        for source in ('# Decision\n\n## Status\n\n## Context\n\nContext',
                       '# Decision\n\nStatus: Accepted\n\n## Status\n\nProposed\n'):
            self.write('decisions/0001-example.md', source)
            rows = self.load().validate(generated=False)['rendered']['handbook/decisions.md']
            self.assertIn('needs-review: missing or ambiguous source status', rows)

    def test_supersession_reference_and_scope_are_preserved(self):
        self.write('decisions/0002-next.md', '# Next\n\n- Status: Proposed\n- Supersedes: ADR 0001 only for this predicate\n')
        self.track()
        rows = self.load().validate(generated=False)['rendered']['handbook/decisions.md']
        self.assertIn('only for this predicate', rows)
        self.assertIn('[ADR 0001](../decisions/0001-example.md)', rows)

    def test_legacy_collision_explicit_positive_and_new_collision_negative(self):
        second = 'decisions/0001-second.md'
        self.write(second, '# Second\n\n## Status\n\nProposed\n')
        self.track()
        self.rejects('ADR_COLLISION_DRIFT')
        self.data['adr']['legacyCollisions'] = {'0001': ['decisions/0001-example.md', second]}
        self.save()
        self.assertEqual(self.load().validate(generated=False)['adrs'], 2)

    def test_timeout_override_reaches_git_and_invalid_rejected(self):
        real = subprocess.run
        with patch.object(nav.subprocess, 'run', wraps=real) as spy:
            self.load(timeout=0.375).validate()
            self.assertEqual(spy.call_args.kwargs['timeout'], 0.375)
        for value in (True, 0, -1, float('inf'), float('nan'), '1'):
            with self.subTest(value=value), self.assertRaisesRegex(nav.CatalogError, 'CONFIG_INVALID'):
                self.load(timeout=value)

    def test_invalid_write_preserves_all_output_bytes(self):
        before = {p: (self.root / p).read_bytes() for p in self.data['outputs'].values()}
        self.data['templates'][0]['anchor'] = 'absent'
        self.save()
        with patch('sys.argv', ['catalog', '--root', str(self.root), '--catalog', 'nav.json', '--write']), redirect_stdout(io.StringIO()):
            self.assertEqual(nav.main(), 1)
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in before})

    def test_issue_form_positive_and_duplicate_or_missing_required_negative(self):
        path = '.github/ISSUE_TEMPLATE/discovery.yml'
        form = dict(name='Idea', description='Explore a question', body=[dict(type='textarea', id='problem',
                    attributes=dict(label='What problem?'), validations=dict(required=True))])
        self.write(path, json.dumps(form))
        self.data['inventory']['roots'].append('.github/ISSUE_TEMPLATE/')
        self.data['entries'].append(dict(id='discovery', path=path, title='Discovery', role='Intake', owner='Maintainer', updateWhen='Intake changes'))
        self.data['templates'].append(dict(id='discovery', entry='discovery', anchor='', title='Discovery', useWhen='New question'))
        self.data['forms'] = [dict(path=path, requiredIds=['problem'], retainedIds=['problem'], retainedChecks={})]
        self.save()
        self.load().validate(generated=False)
        form['body'].append(dict(form['body'][0]))
        self.write(path, json.dumps(form))
        self.rejects('FORM_FIELD_INVALID')
        form['body'].pop()
        form['body'][0]['validations']['required'] = False
        self.write(path, json.dumps(form))
        self.rejects('FORM_REQUIREMENT_MISSING')

    def test_dropdown_and_checkbox_options_must_be_usable(self):
        path = '.github/ISSUE_TEMPLATE/discovery.yml'
        self.data['inventory']['roots'].append('.github/ISSUE_TEMPLATE/')
        self.data['entries'].append(dict(id='form', path=path, title='Form', role='Intake', owner='Maintainer', updateWhen='Intake changes'))
        self.data['templates'].append(dict(id='form', entry='form', anchor='', title='Form', useWhen='Intake'))
        self.data['forms'] = [dict(path=path, requiredIds=['choice'], retainedIds=['choice'], retainedChecks={})]
        for kind, options in [('dropdown', []), ('dropdown', ['same', 'same']),
                              ('checkboxes', []), ('checkboxes', [{'label': 'Act', 'required': 'yes'}])]:
            with self.subTest(kind=kind, options=options):
                form = dict(name='Form', description='Intake', body=[dict(type=kind, id='choice',
                    attributes=dict(label='Choose', options=options), validations=dict(required=True))])
                self.write(path, json.dumps(form))
                self.save()
                self.rejects('FORM_OPTIONS_INVALID')

    def test_valid_choices_and_retained_checkbox_obligations(self):
        path = '.github/ISSUE_TEMPLATE/implementation.yml'
        self.data['inventory']['roots'].append('.github/ISSUE_TEMPLATE/')
        self.data['entries'].append(dict(id='form', path=path, title='Form', role='Intake', owner='Maintainer', updateWhen='Intake changes'))
        self.data['templates'].append(dict(id='form', entry='form', anchor='', title='Form', useWhen='Intake'))
        self.data['forms'] = [dict(path=path, requiredIds=['choice'], retainedIds=['guardrails'],
                                  retainedChecks={'guardrails': ['Work requires review.']})]
        form = dict(name='Plan', description='Plan work', body=[
            dict(type='dropdown', id='choice', attributes=dict(label='Choose', options=['A', 'B'], default=0), validations=dict(required=True)),
            dict(type='checkboxes', id='guardrails', attributes=dict(label='Obligation', options=[dict(label='Work requires review.', required=True)]))])
        self.write(path, json.dumps(form))
        self.save()
        self.load().validate(generated=False)
        form['body'][1]['attributes']['options'][0]['required'] = False
        self.write(path, json.dumps(form))
        self.rejects('FORM_REQUIREMENT_MISSING')
        form['body'][1]['attributes']['options'][0]['required'] = True
        form['body'][0]['attributes']['default'] = 3
        self.write(path, json.dumps(form))
        self.rejects('FORM_OPTIONS_INVALID')


if __name__ == '__main__':
    unittest.main()
