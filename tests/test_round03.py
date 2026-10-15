import unittest,importlib.util,subprocess,json,re
from pathlib import Path
from physstyle.common import read_json
spec=importlib.util.spec_from_file_location('round03',Path('scripts/check_round03.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class Round03Tests(unittest.TestCase):
 def test_length_math_not_counted_as_prose(self):
  self.assertEqual(mod.prose_count('# Title\n\n## Abstract\n\nOne two. \\( x+y \\)\n\n\\[a=b\\]\n\n## Result\n\nThree.'),3)
 def test_flexible_headings_not_fixed_template(self):
  contract={'prose_word_range':[4,8],'abstract_word_range':[1,3]};brief={'paper_title':'Title','protected_math':['x=y']}
  text='# Title\n\n## Abstract\n\nOne two.\n\n## A physical question\n\nThree four.\n\n## Answer and limits\n\nFive six.\n\n\\[x=y\\]'
  result=mod.inspect(text,brief,contract);self.assertFalse(result['errors']);self.assertEqual(result['prose_words'],6)
 def test_equation_corruption_and_condition_leak_rejected(self):
  c={'prose_word_range':[1,100],'abstract_word_range':[1,100]};b={'paper_title':'T','protected_math':['x=y']}
  text='# T\n\n## Abstract\n\nSummary.\n\n## Setup\n\nOne.\n\n## Results\n\nUse physics-paper-style-v3. \\[x=-y\\]'
  r=mod.inspect(text,b,c);self.assertIn('protected math',r['errors']);self.assertIn('condition leakage',r['errors'])
 def test_renderer_headings_without_blank_lines(self):
  # Run the actual pure block parser; supports normal Markdown heading boundaries.
  src=Path('reader/app.js').read_text();fn=src[src.index('function paperBlocks('):src.index('function currentCase()')]
  code=fn+'\nprocess.stdout.write(JSON.stringify(paperBlocks("# T\\n## Abstract\\nText.\\n## Results\\nMore.")));'
  out=subprocess.run(['node','-e',code],capture_output=True,text=True,check=True)
  self.assertEqual(json.loads(out.stdout),['# T','## Abstract','Text.','## Results','More.'])
if __name__=='__main__':unittest.main()
