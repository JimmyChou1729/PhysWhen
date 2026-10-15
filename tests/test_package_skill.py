import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('package_skill', 'scripts/package_skill.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PackageSkillTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'physwhen'
        shutil.copytree('skills/physwhen', self.root, ignore=shutil.ignore_patterns('__pycache__'))
        self.output = Path(self.temp.name) / 'skill.zip'

    def test_repeatable_archive_and_stale_resource_rejected(self):
        mod.package(self.root, self.output)
        first = self.output.read_bytes()
        mod.package(self.root, self.output)
        self.assertEqual(first, self.output.read_bytes())
        mod.package(self.root, self.output, check=True)
        (self.root / 'references/local-evidence.md').write_text('A changed observation')
        with self.assertRaisesRegex(ValueError, 'differs from source'):
            mod.package(self.root, self.output, check=True)

    def test_injected_member_rejected(self):
        mod.package(self.root, self.output)
        with zipfile.ZipFile(self.output, 'a') as archive:
            archive.writestr('private-feedback.json', '{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected package members'):
            mod.package(self.root, self.output, check=True)

    def test_external_resource_symlink_rejected(self):
        path = self.root / 'profile.json'
        path.unlink()
        outside = Path(self.temp.name) / 'outside.json'
        outside.write_text('{}')
        path.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'escapes its directory'):
            mod.package(self.root, self.output)
