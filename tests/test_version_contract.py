"""Reject unresolved and drifted public skill version declarations."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / 'scripts' / 'check_version_contract.py'
REQUIRED = ('SKILL.md', 'agents/openai.yaml', 'README.md', 'CHANGELOG.md')


class PublicVersionContractTests(unittest.TestCase):
    def setUp(self):
        self.context = tempfile.TemporaryDirectory()
        self.addCleanup(self.context.cleanup)
        self.root = Path(self.context.name)
        for relative in REQUIRED:
            dest = self.root / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / relative).read_bytes())

    def run_check(self):
        return subprocess.run([sys.executable, str(CHECKER), str(self.root), '--verify'],
                              capture_output=True, text=True, check=False)

    def test_current_skill_declarations_pass(self):
        self.assertEqual(self.run_check().returncode, 0)

    def test_readme_version_drift_fails_closed(self):
        path = self.root / 'README.md'
        path.write_text(path.read_text().replace('**Version:** 0.1.0', '**Version:** 0.2.0', 1))
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Version drift', result.stderr)

    def test_missing_skill_manifest_fails_closed(self):
        (self.root / 'SKILL.md').unlink()
        result = self.run_check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing required version declaration', result.stderr)


if __name__ == '__main__':
    unittest.main()
