import copy,json,os,tempfile,unittest
from pathlib import Path
from physstyle.group_feedback import validate_v2,reconcile,import_path,summarize
from physstyle.common import write_json,read_json,digest

def fixture():
 return {'schema':'physwhen.feedback.v2','dataset_id':'fixture','participant_id':'a'*32,'revision':1,'test_mode':False,'prior_exposure':'no','case_order':['C2','C1','C3'],'presentation':{c:{'X':'P','Y':'Q'} for c in ['C1','C2','C3']},'texts':{'C1:X':{'effort':'4','naturalness':'2','friction':'','complete':True},'C1:Y':{'effort':'2','naturalness':'4','friction':'','complete':True}},'comparisons':{'C1':{'preference':'Y','note':'','familiarity':'basic'}},'created_at':'2026-10-14T00:00:00Z','updated_at':'2026-10-14T01:00:00Z','exported_at':'2026-10-14T01:00:00Z'}
class GroupFeedbackTests(unittest.TestCase):
 def test_valid_partial_and_unknown_rating(self):
  r=fixture();r['texts']['C1:Y']['effort']='unfamiliar';validate_v2(r,{'dataset_id':'fixture'})
  r['texts']={};r['comparisons']={};validate_v2(r,{'dataset_id':'fixture'})
 def test_reject_bad_qa_identity_assignment_and_completion(self):
  for key,val in [('test_mode',True),('revision',True),('dataset_id','wrong'),('participant_id','../escape'),('case_order',['C1','C1','C3']),('presentation',{'C1':{'X':'P','Y':'P'}})]:
   r=fixture();r[key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):validate_v2(r,{'dataset_id':'fixture'})
  r=fixture();r['texts']['C1:X']['effort']=''
  with self.assertRaises(ValueError):validate_v2(r,{'dataset_id':'fixture'})
 def test_latest_revision_and_conflict(self):
  a=fixture();b=copy.deepcopy(a);b['revision']=2;b['texts']['C1:X']['effort']='3'
  chosen,conflicts=reconcile([a,b,b]);self.assertEqual(len(chosen),1);self.assertEqual(chosen[0]['revision'],2);self.assertFalse(conflicts)
  c=copy.deepcopy(b);c['texts']['C1:X']['effort']='1';self.assertTrue(reconcile([a,b,c])[1])
  c=copy.deepcopy(b);c['presentation']['C1']={'X':'Q','Y':'P'};self.assertTrue(reconcile([a,c])[1])
 def test_batch_rejection_dedupe_and_summary_units(self):
  cwd=Path.cwd()
  with tempfile.TemporaryDirectory() as tmp:
   try:
    os.chdir(tmp);mapping={c:{'P':'A','Q':'B'} for c in ['C1','C2','C3']};write_json('key.json',mapping);write_json('experiments/reader_pack_manifest.json',{'dataset_id':'fixture','private_assignment':'key.json','private_assignment_sha256':digest(Path('key.json').read_bytes())})
    r=fixture();write_json('inbox/valid.json',r);q=copy.deepcopy(r);q['test_mode']=True;write_json('inbox/qa.json',q)
    result=import_path('inbox');self.assertEqual(result['accepted_count'],1);self.assertEqual(result['rejected_count'],1)
    self.assertTrue(import_path('inbox/valid.json')['duplicate_file'])
    r['revision']=2;r['texts']['C1:Y']['effort']='unfamiliar';write_json('inbox/new.json',r);import_path('inbox/new.json')
    out=summarize();self.assertEqual(out['retained_reader_codes'],1);self.assertEqual(out['completed_pairs'],1);self.assertEqual(out['by_case']['C1']['preferences'],{'B':1});self.assertEqual(out['paired_ratings']['effort']['reader_codes_with_numeric_pairs'],0);self.assertEqual(out['paired_ratings']['naturalness']['median_of_within_reader_median_paired_differences'],2)
   finally:os.chdir(cwd)
 def test_standalone_has_no_external_assets_or_questions(self):
  import re
  build=read_json('reports/standalone_reader_build.json')
  delivered=[p for p in Path('deliverables').glob('*.html') if digest(p.read_bytes())==build['sha256']]
  self.assertTrue(delivered,'built standalone artifact missing or changed; filename may be user-renamed')
  text=delivered[0].read_text()
  self.assertFalse(re.search(r'<(?:script|link)\b[^>]*\b(?:src|href)=',text,re.I))
  data=json.loads(Path('reader/data.js').read_text().removeprefix('window.READING_PACK=').strip().removesuffix(';'))
  self.assertTrue(all(set(c) in ({'id','name','versions'},{'id','name','versions','paper_title','reference'}) for c in data['cases']))
  self.assertNotIn('reference_points',text);self.assertNotIn('为什么四维',text)

class PreferenceOnlyTests(unittest.TestCase):
 def preference(self):
  r=fixture();r['instrument']='pair-preference-v1'
  for t in r['texts'].values():t.update(effort='',naturalness='',friction='')
  return r
 def test_empty_ratings_allowed_only_for_explicit_instrument(self):
  r=self.preference();validate_v2(r,{'dataset_id':'fixture'})
  del r['instrument']
  with self.assertRaises(ValueError):validate_v2(r,{'dataset_id':'fixture'})
 def test_reject_fake_ratings_and_inconsistent_pair(self):
  for edit in ('numeric','completion','preference','instrument'):
   r=self.preference()
   if edit=='numeric':r['texts']['C1:X']['effort']='3'
   if edit=='completion':r['texts']['C1:X']['complete']=False
   if edit=='preference':r['comparisons']['C1']['preference']=''
   if edit=='instrument':r['instrument']='unknown'
   with self.subTest(edit=edit),self.assertRaises(ValueError):validate_v2(r,{'dataset_id':'fixture'})
 def test_preference_summary_omits_numeric_metrics_and_other_instrument(self):
  cwd=Path.cwd()
  with tempfile.TemporaryDirectory() as tmp:
   try:
    os.chdir(tmp);write_json('key.json',{c:{'P':'A','Q':'B'} for c in ['C1','C2','C3']});write_json('experiments/reader_pack_manifest.json',{'dataset_id':'fixture','private_assignment':'key.json'});write_json('configs/reader_current.json',{'feedback_instrument':'pair-preference-v1'})
    write_json('inbox/new.json',self.preference());legacy=fixture();legacy['participant_id']='b'*32;write_json('inbox/old.json',legacy)
    self.assertEqual(import_path('inbox')['accepted_count'],2)
    out=summarize();self.assertEqual(out['completed_pairs'],1);self.assertEqual(out['by_case']['C1']['preferences'],{'B':1});self.assertEqual(out['skipped']['other_instrument'],1)
    for metric in out['paired_ratings'].values():self.assertEqual(metric['reader_codes_with_numeric_pairs'],0);self.assertIsNone(metric['median_of_within_reader_median_paired_differences'])
   finally:os.chdir(cwd)
