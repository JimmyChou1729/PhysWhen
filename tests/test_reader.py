import unittest,json,tempfile
from pathlib import Path
from physstyle.feedback import validate_feedback
from physstyle.parse import parse_tex
class ReaderTests(unittest.TestCase):
 def valid(self):return {'schema':'physwhen.feedback.v1','dataset_id':'fixture','test_mode':False,'reader_id':'anonymous','texts':{'C1:P':{'answers':{'Q1':'uncertain'},'effort':'3','friction':'','complete':False}},'comparisons':{}}
 def test_feedback(self):self.assertEqual(validate_feedback(self.valid(),{'dataset_id':'fixture'})['reader_id'],'anonymous')
 def test_reject_test_wrong_dataset_and_unknown_ids(self):
  for update in [{'test_mode':True},{'dataset_id':'wrong'},{'texts':{'C4:P':{}}}]:
   with self.subTest(update=update),self.assertRaises(ValueError):validate_feedback(self.valid()|update,{'dataset_id':'fixture'})
 def test_public_payload_has_no_answers_or_arms(self):
  text=Path('reader/data.js').read_text();obj=json.loads(text.removeprefix('window.READING_PACK=').strip().removesuffix(';'))
  self.assertEqual(len(obj['cases']),3)
  for c in obj['cases']:
   self.assertEqual(set(c['versions']),{'P','Q'});self.assertNotIn('reference_points',json.dumps(c));self.assertNotIn('preferred_arm',json.dumps(c))
 def test_unsectioned_body(self):
  src='\\begin{document}\\begin{abstract}Summary.\\end{abstract}\n\n'+('A meaningful scientific sentence. '*140)+'\\end{document}'
  with tempfile.TemporaryDirectory() as t:d=parse_tex(src.encode(),Path(t))
  self.assertTrue(d['usable']);self.assertEqual(d['paragraphs'][-1]['section_title'],'Unsectioned body')
 def test_unsectioned_explicit_thanks_and_funding_excluded(self):
  for thanks in ['I thank a colleague for discussions.','We wish to thank colleagues.','This work is supported, in part, by the DOE grant DE-FG02.','This work was funded by a university.','{\\it Acknowledgments}. Support was provided.']:
   src='\\begin{document}\\begin{abstract}Summary.\\end{abstract}\n\n'+('A meaningful scientific sentence. '*140)+'\n\n'+thanks+'\n\n\\end{document}'
   with tempfile.TemporaryDirectory() as t:d=parse_tex(src.encode(),Path(t))
   self.assertEqual(d['main_prose_words'],560)
   self.assertEqual(d['paragraphs'][-1]['section_role'],'acknowledgments')
 def test_unsectioned_scientific_support_not_funding(self):
  src='\\begin{document}\\begin{abstract}Summary.\\end{abstract}\n\n'+('A meaningful scientific sentence. '*140)+'\n\nThis work is supported by a perturbative calculation.\n\n\\end{document}'
  with tempfile.TemporaryDirectory() as t:d=parse_tex(src.encode(),Path(t))
  self.assertEqual(d['paragraphs'][-1]['section_role'],'technical_body')
