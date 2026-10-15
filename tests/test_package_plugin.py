import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('package_plugin', 'scripts/package_plugin.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PackagePluginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        for name in ['plugin.json', 'LICENSE']:
            shutil.copy2(name, self.base / name)
        shutil.copytree('skills/physwhen', self.base / 'skills/physwhen', ignore=shutil.ignore_patterns('__pycache__'))
        self.output = self.base / 'plugin.zip'

    def test_same_skill_bytes_and_reproducible_package(self):
        mod.package(self.base, self.output)
        first = self.output.read_bytes()
        mod.package(self.base, self.output)
        self.assertEqual(first, self.output.read_bytes())
        mod.package(self.base, self.output, check=True)
        with zipfile.ZipFile(self.output) as z:
            for name in mod.FILES:
                self.assertEqual(z.read('skills/physwhen/' + name), (self.base / 'skills/physwhen' / name).read_bytes())
        (self.base / 'skills/physwhen/SKILL.md').write_text('---\nname: physwhen\n---\nChanged')
        with self.assertRaisesRegex(ValueError, 'differs from source'):
            mod.package(self.base, self.output, check=True)

    def test_legacy_or_local_dependency_declaration_rejected(self):
        for field in ['skills', 'mcpServers', 'apps', 'interface']:
            p = self.base / 'plugin.json'
            obj = json.loads(Path('plugin.json').read_text());obj[field] = './local-only'
            p.write_text(json.dumps(obj))
            with self.subTest(field=field), self.assertRaises(ValueError):
                mod.plugin_payload(self.base)

    def test_unbundled_reference_rejected(self):
        p = self.base / 'skills/physwhen/SKILL.md'
        p.write_text(p.read_text() + '\n[required](../../data/private.json)\n')
        with self.assertRaisesRegex(ValueError, 'Unbundled'):
            mod.plugin_payload(self.base)

    def test_unrelated_zip_member_rejected(self):
        mod.package(self.base, self.output)
        with zipfile.ZipFile(self.output, 'a') as z:
            z.writestr('reader_assignment_private.json', '{}')
        with self.assertRaisesRegex(ValueError, 'Unexpected plugin archive members'):
            mod.package(self.base, self.output, check=True)

    def test_license_mismatch_rejected(self):
        (self.base / 'LICENSE').write_text('Different license')
        with self.assertRaisesRegex(ValueError, 'licenses differ'):
            mod.plugin_payload(self.base)
