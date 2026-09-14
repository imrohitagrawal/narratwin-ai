"""Work-record invariants: each negative case mutates an otherwise valid fixture."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import work_records as wr


class WorkRecordsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        source = Path(__file__).resolve().parents[1]
        self.put('docs/work/templates/registry.schema.json',
                 (source / 'docs/work/templates/registry.schema.json').read_text())
        for name in ('README.md', 'AGENTS.md', 'CLAUDE.md', 'docs/STATUS.md',
                     'docs/PRD.md', 'docs/CODEX_OPERATING_MODEL.md', 'docs/work/PROCESS.md'):
            self.put(name, 'See docs/work/INDEX.md and docs/STATUS.md and AGENTS.md\n')
        self.put('.gitignore', '/.evidence/\n/docs/work-archive/.restricted/\n')
        self.put('source.json', json.dumps({'openIssues': [{'number': 7, 'title': 'A'}]}))
        self.data = dict(schemaVersion=1, inventorySource=self.ref('source.json'),
                         privateRoots=['.evidence', 'docs/work-archive/.restricted'],
                         profiles=[], issueInventory=[dict(number=7,title='A',workId='alpha')],
                         works=[self.work('alpha', [7]), self.work('beta', [])])
        self.save()

    def put(self, path, data):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(data)

    def ref(self, path):
        data = (self.root / path).read_bytes()
        return dict(path=path, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))

    def work(self, key, issues):
        base = 'docs/work/' + key
        self.put(base + '/README.md', '# ' + key + '\n')
        self.put(base + '/DECISIONS.md', '# Decisions\n')
        self.put(base + '/evidence/INDEX.json', json.dumps(dict(schemaVersion=1,artifacts=[],uses=[])))
        item = dict(id=key,title=key,kind='workstream',owner='root',path=base,
                    plan={**self.ref(base + '/README.md'), 'role':'source-pointer'},
                    statusRef='docs/STATUS.md',authorityRefs=['docs/PRD.md'],issues=issues,
                    parent=None,relationships=[],evidenceIndex=base+'/evidence/INDEX.json',
                    handoff=base+'/HANDOFF.md',checkpoint='observed source revision; verify live before acting')
        self.put(item['handoff'], wr.handoff_binding(item, (self.root / item['evidenceIndex']).read_bytes()))
        return item

    def save(self):
        self.put('docs/work/registry.json', json.dumps(self.data))
        self.put('docs/work/INDEX.md', wr.render_index(self.data))

    def rejected(self, code):
        self.save()
        with self.assertRaisesRegex(wr.RecordError, code):
            wr.validate(self.root)

    def test_positive_shared_relationships(self):
        """Red if reciprocal related-to links are confused with prerequisites."""
        self.data['works'][0]['relationships']=[dict(kind='related-to',target='beta')]
        self.data['works'][1]['relationships']=[dict(kind='related-to',target='alpha')]
        self.save()
        report=wr.validate(self.root)
        self.assertEqual(report['workCount'],2)
        self.assertEqual(report['issueCount'],1)
        self.assertEqual(report['privateAvailability'],'NOT_CHECKED')
        self.assertEqual(report['backup'],'UNPROVED')

    def test_duplicate_id(self):
        """Red if work IDs can silently replace an existing owner."""
        self.data['works'][1]['id']='alpha'
        self.rejected('DUPLICATE_WORK')

    def test_dangling_link(self):
        """Red if a work dependency can point at absent work."""
        self.data['works'][0]['relationships']=[dict(kind='depends-on',target='missing')]
        self.rejected('RELATION_INVALID')

    def test_mixed_dependency_cycle(self):
        """Red if parent plus dependency edges can form a hidden cycle."""
        self.data['works'][0]['parent']='beta'
        self.data['works'][1]['relationships']=[dict(kind='depends-on',target='alpha')]
        self.rejected('DEPENDENCY_CYCLE')

    def test_inventory_omission(self):
        """Red if removing both assignment and inventory hides an observed open issue."""
        self.data['issueInventory']=[]
        self.data['works'][0]['issues']=[]
        self.rejected('INVENTORY_COVERAGE')

    def test_missing_plan(self):
        """Red if a branch-only or missing plan appears locally available."""
        (self.root/self.data['works'][0]['plan']['path']).unlink()
        self.rejected('FILE_UNAVAILABLE')

    def test_plan_drift(self):
        """Red if modified plan bytes keep an old approved/source binding."""
        self.put(self.data['works'][0]['plan']['path'],'changed\n')
        self.rejected('CONTENT_DRIFT')

    def test_handoff_drift(self):
        """Red if a handoff from another artifact set is reused."""
        self.put(self.data['works'][0]['handoff'],'PLAN_SHA256: stale\n')
        self.rejected('HANDOFF_STALE')

    def test_generated_index_drift(self):
        """Red if hand-written navigation can diverge from the registry."""
        self.put('docs/work/INDEX.md','# stale index\n')
        with self.assertRaisesRegex(wr.RecordError,'INDEX_STALE'):
            wr.validate(self.root)

    def test_traversal_and_symlink(self):
        """Red if source reads can escape their registered repository."""
        self.data['works'][0]['plan']['path']='../outside'
        self.rejected('UNSAFE_PATH')

    def test_symlink(self):
        """Red if a source follows a link instead of reading owned bytes."""
        p=self.root/self.data['works'][0]['plan']['path']
        p.unlink()
        p.symlink_to(self.root/'README.md')
        self.rejected('UNSAFE_PATH')

    def test_private_tracking(self):
        """Red if force-add bypasses the private-root ignore policy."""
        self.put('.evidence/secret.txt','synthetic private fixture')
        subprocess.run(['git','-C',str(self.root),'add','-f','.evidence/secret.txt'],check=True)
        self.rejected('PRIVATE_TRACKED')

    def test_invalid_timeout(self):
        """Red if malformed or infinite policy reaches subprocess calls."""
        for value in (True, 0, -1, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaisesRegex(wr.RecordError,'CONFIG_INVALID'):
                wr.validate(self.root,git_timeout=value)

    def test_timeout_override_reaches_git(self):
        """Red if the configured timeout is reported but ignored by a Git call."""
        with patch.object(wr.subprocess, 'run', wraps=subprocess.run) as run:
            report=wr.validate(self.root,git_timeout=1.25)
        self.assertEqual(report['effectiveConfiguration']['gitTimeoutSeconds'],1.25)
        self.assertGreater(len(run.call_args_list),0)
        self.assertTrue(all(call.kwargs['timeout']==1.25 for call in run.call_args_list))

    def test_profile_selection(self):
        """Red if missing profile silently passes, or unknown profile blocks unrelated navigation."""
        self.data['profiles']=[dict(id='future',kind='future-v2',descriptor=self.ref('source.json'))]
        self.save()
        self.assertEqual(wr.validate(self.root)['workCount'],2)
        with self.assertRaisesRegex(wr.RecordError,'PROFILE_UNSUPPORTED'):
            wr.validate(self.root,profile_id='future')
        with self.assertRaisesRegex(wr.RecordError,'PROFILE_MISSING'):
            wr.validate(self.root,profile_id='g1-originals')

    def test_artifact_ownership(self):
        """Red if two work records claim the same immutable evidence identity."""
        artifact=dict(id='source',owner='alpha',role='original',revision='v1',
                      sha256='a'*64,bytes=4,restrictedEvidenceRef='restricted-evidence:fixture',
                      custody='restricted',verification='METADATA_PINNED',derivedFrom=[])
        for work in self.data['works']:
            entry=copy.deepcopy(artifact)
            entry['owner']=work['id']
            self.put(work['evidenceIndex'],json.dumps(dict(schemaVersion=1,artifacts=[entry],uses=[])))
            self.put(work['handoff'],wr.handoff_binding(work,(self.root/work['evidenceIndex']).read_bytes()))
        self.rejected('DUPLICATE_ARTIFACT')

    def test_same_source_different_ids(self):
        """IR01: red if distinct IDs hide duplicate ownership of one restricted source."""
        for work in self.data['works']:
            item=dict(id=work['id']+'-source',owner=work['id'],role='original',revision='v1',
                      sha256='a'*64,bytes=4,restrictedEvidenceRef='restricted-evidence:same-source',
                      custody='restricted',verification='METADATA_PINNED',derivedFrom=[])
            self.put(work['evidenceIndex'],json.dumps(dict(schemaVersion=1,artifacts=[item],uses=[])))
            self.put(work['handoff'],wr.handoff_binding(work,(self.root/work['evidenceIndex']).read_bytes()))
        self.rejected('DUPLICATE_SOURCE')

    def test_public_plan_cannot_read_private_store(self):
        """IR02: red if correctly hashed private bytes become a public plan/link."""
        self.put('.evidence/secret.txt','synthetic private source')
        work=self.data['works'][0]
        work['plan']={**self.ref('.evidence/secret.txt'),'role':'source-pointer'}
        self.put(work['handoff'],wr.handoff_binding(work,(self.root/work['evidenceIndex']).read_bytes()))
        self.rejected('PRIVATE_REFERENCE')

    def test_public_reference_to_configured_private_root(self):
        """IR02: red if protection only covers the default private directory name."""
        self.data['privateRoots'].append('local-custody')
        self.put('.gitignore',(self.root/'.gitignore').read_text()+'/local-custody/\n')
        self.put('local-custody/source.md','synthetic private source')
        self.data['works'][0]['authorityRefs']=['local-custody/source.md']
        self.rejected('PRIVATE_REFERENCE')


if __name__ == '__main__':
    unittest.main()
