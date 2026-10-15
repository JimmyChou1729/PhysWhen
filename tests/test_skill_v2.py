import unittest,importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('portable_prose',Path('skills/physics-paper-style-v2/scripts/check_prose.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class SkillV2Tests(unittest.TestCase):
 def test_equation_integrity_is_separate_from_semantics(self):
  p={'discovery_papers':168,'reference_profiles':{'D01_sentence_p90':{'median':37.75}}}
  r=module.inspect('The result is\n\\[x=y+1\\]\nunder the stated assumption.',p,['x=y+1'])
  self.assertTrue(r['equation_checks'][0]['exact_occurrence_check']);self.assertIn('not_checked',r['scientific_semantics']);self.assertEqual(r['prose_words'],7)
  self.assertFalse(module.inspect('\\[x=y-1\\]',p,['x=y+1'])['equation_checks'][0]['exact_occurrence_check'])
 def test_repeated_equation_and_math_only_paragraph(self):
  p={'discovery_papers':168,'reference_profiles':{'D01_sentence_p90':{'median':37.75}}}
  r=module.inspect('One short paragraph.\n\n\\[x=y\\]\n\n\\[x=y\\]',p,['x=y'])
  self.assertEqual(r['paragraphs'],1);self.assertEqual(r['prose_words'],3);self.assertFalse(r['equation_checks'][0]['exact_occurrence_check'])

 def test_display_internal_newlines_do_not_split_prose_paragraph(self):
  p={'discovery_papers':168,'reference_profiles':{'D01_sentence_p90':{'median':37.75}}}
  text='We write\n\\[\n x=y\n\n+z\n\\]\nwhere the symbols are defined.'
  r=module.inspect(text,p)
  self.assertEqual(r['paragraphs'],1);self.assertEqual(r['prose_words'],7)
