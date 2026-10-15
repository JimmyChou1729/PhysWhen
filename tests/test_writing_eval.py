import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('writing_eval','scripts/writing_eval.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class WritingEvaluationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.case={'id':'H01','family':'fidelity','mode':'edit','task_type':'fixture','audience':'fixture','instruction':'Controlled test; no retrieval','material':'Synthetic material: R=Kx.','required_literals':['R=Kx'],'forbidden_literals':[],'source_status':'synthetic fixture; never real research data','word_limit':60}
  self.cases=self.root/'cases.jsonl';self.cases.write_text(json.dumps(self.case)+'\n')
  self.protocol=self.root/'protocol.json';self.protocol.write_text(json.dumps({'generic_prompt':'Edit clearly.','generation':'One initial and final.'}))
  for name in ['baseline','candidate']:
   d=self.root/name;d.mkdir();(d/'SKILL.md').write_text('---\nname: fixture\n---\nPreserve science.')
  self.freeze=self.root/'freeze.json';m.freeze_candidate(self.root/'candidate',self.freeze)
  self.rubric=self.root/'rubric.jsonl';self.rubric.write_text(json.dumps({'case_id':'H01','required_facts':['supplied equation'],'comprehension':[{'question':'What relation is supplied?','accepted_points':['SECRET_EXPECTED_ANSWER']} ]})+'\n')
  self.jobs=self.root/'jobs'
  m.export_jobs(self.cases,self.protocol,self.root/'baseline',self.root/'candidate',self.freeze,self.jobs,self.rubric)
 def response(self,arm='generic'):return {'job_id':json.loads((self.jobs/arm/'H01.json').read_text())['job_id'],'case_id':'H01','first_draft':'R=Kx.','manuscript':'R=Kx.','note':'No retrieval, synthetic task.','checks_performed':['Compared equation']}
 def test_freeze_is_write_once_and_detects_changes(self):
  with self.assertRaises(ValueError):m.freeze_candidate(self.root/'candidate',self.freeze)
  (self.root/'candidate/SKILL.md').write_text('Changed')
  with self.assertRaises(ValueError):m.verify_candidate(self.root/'candidate',self.freeze)
 def test_jobs_exclude_expected_checks_and_cannot_overwrite(self):
  job=json.loads((self.jobs/'candidate/H01.json').read_text());self.assertNotIn('required_literals',job);self.assertNotIn('comprehension',job)
  with self.assertRaises(ValueError):m.export_jobs(self.cases,self.protocol,self.root/'baseline',self.root/'candidate',self.freeze,self.jobs,self.rubric)
 def test_partial_import_and_identity_rejection(self):
  responses=self.root/'responses';p=responses/'generic/H01.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(self.response()))
  out=self.root/'collected.json';self.assertEqual(m.collect(self.cases,self.jobs,responses,out),(1,2))
  r=self.response();r['case_id']='H02';p.write_text(json.dumps(r))
  with self.assertRaises(ValueError):m.collect(self.cases,self.jobs,responses,out)
 def test_changed_case_manifest_rejected(self):
  self.cases.write_text(json.dumps(self.case|{'material':'Changed after export'})+'\n')
  with self.assertRaises(ValueError):m.collect(self.cases,self.jobs,self.root/'responses',self.root/'out.json')
 def test_literal_flags_are_not_semantic_scores(self):
  p=self.root/'responses/generic/H01.json';p.parent.mkdir(parents=True);r=self.response();r['manuscript']='This is vague.';p.write_text(json.dumps(r));out=self.root/'out.json'
  m.collect(self.cases,self.jobs,self.root/'responses',out);data=json.loads(out.read_text());self.assertEqual(data['records'][0]['flags'][0]['kind'],'literal_not_found');self.assertNotIn('fidelity',data['records'][0]);self.assertEqual(data['human_effect'],'not_established')
 def test_masking_keeps_three_arms_and_review_quotes_are_checked(self):
  for arm in m.ARMS:
   p=self.root/'responses'/arm/'H01.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(self.response(arm)))
  collected=self.root/'collected.json';m.collect(self.cases,self.jobs,self.root/'responses',collected)
  rubric=self.rubric
  review=self.root/'review';m.prepare_review(self.cases,rubric,collected,review)
  self.assertEqual(set(json.loads((review/'private_key.json').read_text())['H01'].values()),set(m.ARMS))
  packet=json.loads((review/'masked/H01.json').read_text());self.assertEqual(set(packet['texts']),{'U','V','W'});self.assertNotIn('arm',packet)
  rows=[{'review_packet_id':packet['review_packet_id'],'case_id':'H01','alias':a,'fidelity':'preserved','clarity':'clear','defect_resolution':'not_applicable','unnecessary_rewrite':'no','fact_checks':[{'fact':'supplied equation','status':'preserved','evidence_quote':'R=Kx','reason':'equation retained'}],'notes':''} for a in ['U','V','W']]
  path=self.root/'judgments.jsonl';path.write_text(''.join(json.dumps(x)+'\n' for x in rows));out=self.root/'summary.json';self.assertEqual(m.summarize_reviews(review,path,out),(3,0));self.assertEqual(json.loads(out.read_text())['human_participants'],0)
  forms=self.root/'human';self.assertEqual(m.export_human_review(review,forms),3)
  assigned=[]
  for i in range(1,4):
   text=(forms/f'form-{i}.md').read_text();self.assertNotIn('SECRET_EXPECTED_ANSWER',text)
   obj=json.loads((forms/f'form-{i}-responses.json').read_text());assigned.append(obj['responses'][0]['assigned_alias']);self.assertEqual(obj['responses'][0]['answers'][0]['answer'],'')
  self.assertEqual(set(assigned),{'U','V','W'})
  rows[0]['fact_checks'][0]['evidence_quote']='not in text';path.write_text(''.join(json.dumps(x)+'\n' for x in rows))
  with self.assertRaises(ValueError):m.summarize_reviews(review,path,out)
 def test_wrong_arm_job_and_changed_source_rejected(self):
  p=self.root/'responses/candidate/H01.json';p.parent.mkdir(parents=True);p.write_text(json.dumps(self.response('generic')))
  with self.assertRaisesRegex(ValueError,'job/protocol/source'):m.collect(self.cases,self.jobs,self.root/'responses',self.root/'out.json')
  p.write_text(json.dumps(self.response('candidate')));(self.root/'candidate/SKILL.md').write_text('Changed')
  with self.assertRaisesRegex(ValueError,'source changed'):m.collect(self.cases,self.jobs,self.root/'responses',self.root/'out.json')
 def test_changed_rubric_and_review_case_rejected(self):
  self.rubric.write_text('{}\n')
  with self.assertRaisesRegex(ValueError,'protocol/rubric'):m.collect(self.cases,self.jobs,self.root/'responses',self.root/'out.json')
 def test_invalid_case_identity_or_non_synthetic_provenance(self):
  for update in [{'id':'../escape'},{'id':5},{'source_status':'real paper'},{'word_limit':True}]:
   with self.subTest(update=update),self.assertRaises(ValueError):m.validate_cases([self.case|update])
