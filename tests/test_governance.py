from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GovernanceTests(unittest.TestCase):
    def test_version_declarations(self):
        skill=(ROOT/'SKILL.md').read_text()
        meta=(ROOT/'agents/openai.yaml').read_text()
        readme=(ROOT/'README.md').read_text()
        changelog=(ROOT/'CHANGELOG.md').read_text()
        version=re.search(r'(?m)^  version: (\d+\.\d+\.\d+)$',skill).group(1)
        self.assertEqual(version,'0.2.0')
        self.assertRegex(meta,r'(?m)^version: '+re.escape(version)+r'$')
        self.assertIn('**Version:** '+version,readme)
        self.assertIn('## ['+version+']',changelog)
    def test_required_structure(self):
        for p in ('SKILL.md','README.md','CHANGELOG.md','agents/openai.yaml','assets/icon.svg','references/compatibility.md','references/security.md','references/hosting.md','references/acceptance-matrix.md','scripts/audit_html.py','scripts/build_pwa.py','scripts/verify_dist.py'):
            self.assertTrue((ROOT/p).is_file(),p)
