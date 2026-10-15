import unittest
from unittest.mock import patch
from physstyle.pilot import enlarged_corpus
from physstyle.pipeline import analyze
from physstyle.report import finalize_results
class PilotRoutingTests(unittest.TestCase):
    def test_enlarged_counts_only_qualified_usable(self):
        rows=[{'screening':'include','parse_status':'usable'}]*30+[{'screening':'include','parse_status':'failed'}]*12
        with patch('physstyle.pilot.read_jsonl',return_value=rows),patch('pathlib.Path.exists',return_value=True):
            self.assertFalse(enlarged_corpus())
        rows.append({'screening':'include','parse_status':'usable'})
        with patch('physstyle.pilot.read_jsonl',return_value=rows),patch('pathlib.Path.exists',return_value=True):
            self.assertTrue(enlarged_corpus())
    def test_enlarged_analysis_and_report_preserve_smoke_route(self):
        with patch('physstyle.pilot.enlarged_corpus',return_value=True),patch('physstyle.pilot.analyze_pilot',return_value={'pilot':'fixture'}) as runner:
            self.assertEqual(analyze({}),{'pilot':'fixture'})
            self.assertEqual(finalize_results(),{'pilot':'fixture'})
            self.assertEqual(runner.call_count,2)

class CorpusTransactionTests(unittest.TestCase):
    def test_nested_and_cross_process_lock(self):
        import os,sys,tempfile,subprocess
        from pathlib import Path
        from physstyle.common import corpus_lock
        repo=str(Path(__file__).resolve().parents[1]);previous=Path.cwd()
        code='import sys; sys.path.insert(0,'+repr(repo)+'); from physstyle.common import corpus_lock\ntry:\n with corpus_lock(): pass\nexcept RuntimeError:\n sys.exit(2)\n'
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                with corpus_lock():
                    with corpus_lock():pass
                    self.assertEqual(subprocess.run([sys.executable,'-c',code],capture_output=True).returncode,2)
                self.assertEqual(subprocess.run([sys.executable,'-c',code],capture_output=True).returncode,0)
            finally:os.chdir(previous)
