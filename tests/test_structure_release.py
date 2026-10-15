"""Isolated release-gate regressions; never build against the working corpus."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from physstyle.common import digest
from physstyle.release import check_forward_bundle, check_semantic_bundle

REPO = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads((REPO / 'data/structure/protocol.json').read_text())


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='physwhen-release-test-')
        self.addCleanup(self.temp.cleanup)
        previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, previous)
        self.ids = [f'fixture{i:02d}' for i in range(30)]
        self.put('data/structure/protocol.json', PROTOCOL)
        for pid in self.ids:
            evidence = {'paragraph_id': 'p0001', 'exact_quote': 'We derive a result.'}
            identity = {'paper_id': pid, 'version': 1, 'source_sha256': 'fixture-source', 'split': 'discovery'}
            packet = dict(identity, main_body_paragraph_ids=['p0001'], paragraphs=[{
                'paragraph_id': 'p0001', 'word_count': 4,
                'blocks': [{'raw': 'We derive a result.', 'source_spans': []}]}])
            record = dict(identity, protocol_version=PROTOCOL['version'],
                          coverage={'main_body': 'full_read', 'abstract': 'read',
                                    'figures': 'not_read', 'appendices': 'not_read'},
                          moves=[{'start_paragraph_id': 'p0001', 'end_paragraph_id': 'p0001',
                                  'role': 'result', 'evidence': [evidence]}],
                          nodes=[{'id': n, 'type': kind, 'text': n,
                                  'occurrences': [dict(evidence, role='development')]}
                                 for n, kind in [('m', 'method'), ('c', 'claim')]],
                          edges=[{'from': 'm', 'to': 'c', 'type': 'derives_from',
                                  'basis': 'explicit', 'rationale': 'Fixture relation.',
                                  'evidence': [evidence]}], question_status=[], recurrences=[])
            self.put(f'data/structure/papers/{pid}.json', packet)
            self.put(f'data/structure/annotations/{pid}.json', record)
            self.put(f'data/structure/initial_annotations/{pid}.json', record)
        self.sem = {'papers_full_mainbody_read': 30, 'paper_ids': self.ids,
                    'selected_nodes': 60, 'selected_edges': 30, 'main_paragraphs': 30,
                    'annotation_manifest': [self.entry(f'data/structure/annotations/{pid}.json')
                                            for pid in self.ids]}
        for index, name in enumerate(['structure_audit_a', 'structure_audit_c', 'structure_audit_c2']):
            self.put(f'reports/{name}.json', {'status': 'complete', 'papers': [
                {'paper_id': pid, 'read_main_body_paragraphs': 1,
                 'edge_reviews': [{'edge_index': 0, 'verdict': 'agree'}]}
                for pid in self.ids[index * 10:(index + 1) * 10]]})
        self.make_forward()

    def put(self, name, value):
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def write(self, name, text):
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def entry(self, name):
        return {'path': name, 'sha256': digest(Path(name).read_bytes())}

    def make_forward(self):
        base = 'experiments/structure_skill_v3_validation'
        cases = {'organize': 'organize.md', 'copyedit': 'copyedit.txt',
                 'conflict': 'conflict.txt', 'appendix': 'appendix.md'}
        paths = []
        for case, filename in cases.items():
            for path in [f'{base}/briefs/{case}.txt', f'{base}/outputs/{filename}',
                         f'{base}/outputs_initial/{filename}']:
                self.write(path, 'Fixture only: ' + path)
                paths.append(path)
        skill = 'skills/physics-paper-style-v3/SKILL.md'
        snapshot = f'{base}/skill_initial_snapshot/SKILL.md'
        self.write(skill, 'Fixture skill.\n')
        self.write(snapshot, 'Initial fixture skill.\n')
        self.prov = {'cases': 4, 'files': [self.entry(x) for x in paths],
                     'initial_tested_skill_snapshot': snapshot,
                     'skill_entry_sha256': digest(Path(snapshot).read_bytes()),
                     'appendix_task_skill_entry_sha256': digest(Path(skill).read_bytes())}
        postfiles = []
        for case in ['organize', 'copyedit', 'conflict']:
            initial = f'{base}/outputs_initial/{cases[case]}'
            final = f'{base}/outputs/{cases[case]}'
            postfiles.append({'initial_path': initial, 'final_path': final,
                              'initial_sha256': digest(Path(initial).read_bytes()),
                              'final_sha256': digest(Path(final).read_bytes())})
        self.put('reports/structure_forward_review.json', {
            'cases': [{'case': k} for k in ['organize', 'copyedit', 'conflict']],
            'summary': {'scientific_contract_failures_found': 0,
                        'invented_result_or_proof_found': False},
            'postedit': {'fixes': [{'status': 'passed'}], 'files': postfiles}})
        self.put('reports/structure_appendix_forward_review.json', {
            'status': 'complete', 'verdict': 'pass', 'required_changes': [],
            'inputs_read': [dict(self.entry(path), role=role) for role, path in [
                ('brief', f'{base}/briefs/appendix.txt'), ('skill', skill),
                ('output', f'{base}/outputs/appendix.md')]]})

    def make_validator_bundle(self):
        self.put('reports/structure_semantic_results.json', self.sem)
        self.put('reports/STRUCTURE_RESULTS.json', {
            'papers_usable': 500, 'split_counts': {'discovery': 400, 'heldout': 100},
            'profile_file': 'reports/feature_profiles.json'})
        self.put('reports/feature_profiles.json', {'discovery': {}})
        self.put('data/splits/frozen.json', {'assignments': {p: 'discovery' for p in self.ids}})
        self.put('data/structure/sample.json', {'papers': [{'paper_id': p} for p in self.ids]})
        anchors = []
        canonical = []
        for i in range(4):
            item = {'paper_id': self.ids[i], 'version': 1, 'source_sha256': 'fixture-source',
                    'node_id': 'c', 'paragraph_id': 'p0001', 'role': 'development',
                    'source_spans': []}
            canonical.append(dict(item, exact_quote='We derive a result.'))
            anchors.append(dict(item, rule=f'G{i + 1}',
                                exact_quote_sha256=digest(b'We derive a result.')))
        anchor_path = 'skills/physics-paper-style-v3/references/structure-source-anchors.jsonl'
        self.write(anchor_path, ''.join(json.dumps(x) + '\n' for x in anchors))
        self.write('data/structure/source_anchors.jsonl', ''.join(json.dumps(x) + '\n' for x in canonical))
        self.put('skills/physics-paper-style-v3/profile.json', {
            'corpus_papers': 500, 'discovery_papers': 400, 'heldout_papers': 100,
            'reference_distributions': {}, 'structure_semantic': self.sem,
            'structure_sample_files': ['data/structure/sample.json'],
            'structural_anchor_count': 4,
            'structural_anchor_sha256': digest(Path(anchor_path).read_bytes())})
        self.put('experiments/structure_skill_v3_validation/provenance.json', self.prov)
        self.package()

    def package(self):
        Path('deliverables').mkdir(exist_ok=True)
        with zipfile.ZipFile('deliverables/PhysWhen-skill-v3.zip', 'w') as archive:
            for path in Path('skills/physics-paper-style-v3').rglob('*'):
                if path.is_file():
                    archive.write(path, str(path.relative_to('skills')))

    def validator(self):
        return subprocess.run([sys.executable, str(REPO / 'scripts/validate_skill_v3.py')],
                              capture_output=True, text=True,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_valid_semantic_bundle(self):
        result = check_semantic_bundle(self.sem, self.ids)
        self.assertEqual((result['papers'], result['original_edges']), (30, 30))

    def test_semantic_identity_mismatch(self):
        self.sem['paper_ids'] = ['other'] + self.ids[1:]
        with self.assertRaisesRegex(AssertionError, 'identity mismatch'):
            check_semantic_bundle(self.sem, self.ids)

    def test_reported_paper_count_must_match_actual_thirty(self):
        self.sem['papers_full_mainbody_read'] = 31
        with self.assertRaises(AssertionError):
            check_semantic_bundle(self.sem, self.ids)

    def test_final_report_rejects_stale_acceptance(self):
        self.make_validator_bundle()
        self.put('reports/structure_validation.json', {
            'status': 'passed', 'stage_input_sha256': 'old-stage',
            'semantic_input_sha256': 'old-semantic'})
        result = subprocess.run(
            [sys.executable, str(REPO / 'scripts/build_structure_report.py')],
            capture_output=True, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('acceptance report is stale', result.stderr)
        self.assertFalse(Path('reports/SKILL_V3_REPORT.md').exists())

    def test_missing_map(self):
        Path(f'data/structure/annotations/{self.ids[0]}.json').unlink()
        with self.assertRaisesRegex(AssertionError, 'actual map set mismatch'):
            check_semantic_bundle(self.sem, self.ids)

    def test_stale_annotation_hash(self):
        path = Path(f'data/structure/annotations/{self.ids[0]}.json')
        path.write_text(path.read_text() + '\n')
        with self.assertRaisesRegex(AssertionError, 'semantic report is stale'):
            check_semantic_bundle(self.sem, self.ids)

    def test_wrong_semantic_denominator(self):
        self.sem['selected_edges'] += 1
        with self.assertRaisesRegex(AssertionError, 'denominators stale'):
            check_semantic_bundle(self.sem, self.ids)

    def test_missing_independent_review(self):
        Path('reports/structure_audit_c.json').unlink()
        with self.assertRaisesRegex(AssertionError, 'missing independent review'):
            check_semantic_bundle(self.sem, self.ids)

    def test_incomplete_edge_review(self):
        path = 'reports/structure_audit_c.json'
        report = json.loads(Path(path).read_text())
        report['papers'][0]['edge_reviews'] = []
        self.put(path, report)
        with self.assertRaisesRegex(AssertionError, 'incomplete edge review'):
            check_semantic_bundle(self.sem, self.ids)

    def test_wrong_review_reading_coverage(self):
        path = 'reports/structure_audit_c.json'
        report = json.loads(Path(path).read_text())
        report['papers'][0]['read_main_body_paragraphs'] = 0
        self.put(path, report)
        with self.assertRaisesRegex(AssertionError, 'reading coverage mismatch'):
            check_semantic_bundle(self.sem, self.ids)

    def test_duplicate_reviewed_paper(self):
        path = 'reports/structure_audit_c.json'
        report = json.loads(Path(path).read_text())
        report['papers'][0]['paper_id'] = self.ids[0]
        self.put(path, report)
        with self.assertRaisesRegex(AssertionError, 'duplicate reviewed paper'):
            check_semantic_bundle(self.sem, self.ids)

    def test_in_progress_review(self):
        path = 'reports/structure_audit_c.json'
        report = json.loads(Path(path).read_text())
        report['status'] = 'in_progress'
        self.put(path, report)
        with self.assertRaisesRegex(AssertionError, 'review not complete'):
            check_semantic_bundle(self.sem, self.ids)

    def test_valid_forward_bundle(self):
        self.assertEqual(check_forward_bundle(self.prov)['cases'], 4)

    def test_empty_forward_manifest(self):
        self.prov['files'] = []
        with self.assertRaisesRegex(AssertionError, 'required forward file sets missing'):
            check_forward_bundle(self.prov)

    def test_missing_fourth_case_from_manifest(self):
        self.prov['files'] = [x for x in self.prov['files'] if not x['path'].endswith('appendix.md')]
        with self.assertRaisesRegex(AssertionError, 'required forward file sets missing'):
            check_forward_bundle(self.prov)

    def test_stale_forward_output(self):
        Path('experiments/structure_skill_v3_validation/outputs/appendix.md').write_text('Changed')
        with self.assertRaisesRegex(AssertionError, 'forward file hash mismatch'):
            check_forward_bundle(self.prov)

    def test_stale_appendix_review(self):
        Path('skills/physics-paper-style-v3/SKILL.md').write_text('Changed skill')
        with self.assertRaisesRegex(AssertionError, 'appendix review stale'):
            check_forward_bundle(self.prov)

    def test_complete_isolated_validator_bundle(self):
        self.make_validator_bundle()
        result = self.validator()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(Path('reports/skill_v3_validation.json').read_text())['wholepaper_maps'], 30)

    def test_empty_anchors_rejected_after_other_gates_pass(self):
        self.make_validator_bundle()
        path = Path('skills/physics-paper-style-v3/references/structure-source-anchors.jsonl')
        path.write_text('')
        self.package()
        result = self.validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('AssertionError', result.stderr)
        self.assertFalse(Path('reports/skill_v3_validation.json').exists())

    def test_original_negative_fixture_rejected(self):
        self.make_validator_bundle()
        # Recreate the original invalid bundle, not a mock of the acceptance function.
        for path in Path('data/structure/annotations').glob('*.json'):
            path.unlink()
        self.sem['paper_ids'] = [f'different{i:02d}' for i in range(30)]
        self.put('reports/structure_semantic_results.json', self.sem)
        profile_path = 'skills/physics-paper-style-v3/profile.json'
        profile = json.loads(Path(profile_path).read_text())
        profile['structure_semantic'] = copy.deepcopy(self.sem)
        self.put(profile_path, profile)
        Path('skills/physics-paper-style-v3/references/structure-source-anchors.jsonl').unlink()
        Path('data/structure/source_anchors.jsonl').unlink()
        self.prov['files'] = []
        self.put('experiments/structure_skill_v3_validation/provenance.json', self.prov)
        for directory in ['outputs', 'outputs_initial']:
            for path in Path('experiments/structure_skill_v3_validation', directory).glob('*'):
                path.unlink()
        self.package()
        result = self.validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('semantic/sample identity mismatch', result.stderr)
        self.assertFalse(Path('reports/skill_v3_validation.json').exists())


if __name__ == '__main__':
    unittest.main()
