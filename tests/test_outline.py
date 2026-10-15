import unittest,importlib.util
from pathlib import Path
p=Path('skills/physwhen/scripts/check_outline.py');spec=importlib.util.spec_from_file_location('outline',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class OutlineTest(unittest.TestCase):
 def setUp(self):
  self.plan={'questions':[{'id':'q','status':'answered','claim_ids':['c']}],'claims':[{'id':'c','status':'supported','evidence_ids':['e'],'condition_ids':['a']}],'evidence':[{'id':'e'}],'conditions':[{'id':'a'}],'sections':[{'id':'overview','purpose':'Preview result','claim_ids':['c'],'condition_ids':['a']},{'id':'derivation','purpose':'Supply later derivation','evidence_ids':['e']}],'dependencies':[{'from':'e','to':'c'}]}
 def test_non_object_input_returns_structured_failure(self):
  for data in [[],None,'text',3,True]:
   with self.subTest(data=data):
    result=mod.check(data);self.assertEqual(result['status'],'fail');self.assertIn('top level: expected object',result['errors'])
 def test_cli_non_object_has_json_error_not_traceback(self):
  import tempfile,subprocess,sys,json
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'input.json';path.write_text('[]')
   result=subprocess.run([sys.executable,str(p),str(path)],capture_output=True,text=True)
   self.assertEqual(result.returncode,1);self.assertEqual(json.loads(result.stdout)['status'],'fail');self.assertNotIn('Traceback',result.stderr)
 def test_result_first_accepted(self):self.assertEqual(mod.check(self.plan)['status'],'pass')
 def test_lost_condition_rejected(self):
  self.plan['sections'][0]['condition_ids']=[];self.assertIn('a: absent from section plan',mod.check(self.plan)['errors'])
 def test_missing_support_not_hidden(self):
  self.plan['claims'][0]['evidence_ids']=[];self.assertTrue(any('without identified evidence' in e for e in mod.check(self.plan)['errors']))
 def test_unknown_claim_and_duplicate_id_rejected(self):
  self.plan['questions'][0]['claim_ids']=['ghost'];self.plan['conditions'].append({'id':'e'});errors=mod.check(self.plan)['errors'];self.assertIn('duplicate id: e',errors);self.assertIn('q: unknown claim_ids ghost',errors)
 def test_unwritten_appendix_disclosed(self):
  self.plan['deferred_material']=[{'id':'app','reason':'auxiliary','destination':'Appendix A','available':False}];r=mod.check(self.plan);self.assertEqual(r['status'],'pass');self.assertTrue(r['review_hints'])
if __name__=='__main__':unittest.main()
