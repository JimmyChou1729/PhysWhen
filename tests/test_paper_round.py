import unittest,tempfile,subprocess,sys,json
from pathlib import Path
class PaperRoundBuildTests(unittest.TestCase):
 def test_configured_standalone_name_does_not_overwrite_app(self):
  script=Path('scripts/build_standalone_reader.py').resolve()
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   files={'configs/reader_current.json':json.dumps({'standalone_name':'Round-Test.html'}),'experiments/reader_pack_manifest.json':json.dumps({'dataset_id':'temporary-engineering-fixture'}),'reader/index.html':'<html><head><link rel="stylesheet" href="style.css"><script defer src="app.js"></script></head><body>Fixture</body></html>','reader/style.css':'body{color:black}','reader/app.js':'window.fixture=true;','reader/data.js':'window.READING_PACK={};','reader/vendor/katex/dist/katex.min.css':'','reader/vendor/katex/dist/katex.min.js':'/* fixture */','reader/vendor/katex/dist/contrib/auto-render.min.js':'/* fixture */','reader/vendor/katex/LICENSE':'Fixture license'}
   for name,text in files.items():p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
   subprocess.run([sys.executable,str(script)],cwd=root,check=True,capture_output=True)
   self.assertEqual((root/'reader/app.js').read_text(),'window.fixture=true;')
   self.assertTrue((root/'deliverables/Round-Test.html').exists());self.assertFalse((root/'deliverables/app.js').exists())
   self.assertIn('window.fixture=true;',(root/'deliverables/Round-Test.html').read_text())
