import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'
FIX=ROOT/'tests'/'fixtures'
sys.path.insert(0,str(SCRIPTS))
from pwa_core import inspect_input,sha256
from verify_dist import verify

class PwaPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.dest=self.root/'dist'

    def build(self,source=None,extra=None,expect=0):
        source=source or (FIX/'index.html')
        cmd=[sys.executable,str(SCRIPTS/'build_pwa.py'),str(source),'--out',str(self.dest),'--name','Test PWA','--short-name','Test']+(extra or [])
        r=subprocess.run(cmd,text=True,capture_output=True)
        self.assertEqual(r.returncode,expect,(r.stdout,r.stderr))
        return r

    def test_source_unchanged_and_public_allowlist(self):
        prev={p.name:sha256(p) for p in FIX.iterdir() if p.is_file()}
        self.build()
        self.assertEqual(sorted(p.name for p in self.dest.iterdir()),['app.js','icon-192.png','icon-512.png','index.html','manifest.webmanifest','styles.css','sw.js'])
        self.assertEqual(verify(self.dest),[])
        self.assertEqual(prev,{p.name:sha256(p) for p in FIX.iterdir() if p.is_file()})
        self.assertTrue((self.root/'build-report.json').exists())
        self.assertFalse((self.dest/'build-report.json').exists())
        self.assertIn('cache', (self.dest/'sw.js').read_text().lower())
        self.assertIn("./app.js",(self.dest/'sw.js').read_text())

    def test_same_source_deterministic(self):
        self.build()
        a=sha256(self.dest/'sw.js')
        dest2=self.root/'dist2'
        q=subprocess.run([sys.executable,str(SCRIPTS/'build_pwa.py'),str(FIX/'index.html'),'--out',str(dest2),'--name','Test PWA','--short-name','Test'],capture_output=True,text=True)
        self.assertEqual(q.returncode,0,q.stderr)
        self.assertEqual(a,sha256(dest2/'sw.js'))

    def test_output_existing_refused(self):
        self.build()
        self.build(expect=2)

    def test_file_outside_root_refused(self):
        src=self.root/'escape';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body><script src="../secret.js"></script></body></html>')
        (self.root/'secret.js').write_text('console.log(1)')
        r=inspect_input(src/'index.html')
        self.assertFalse(r['static_conversion_eligible']);self.assertTrue(any('outside_root' in s for s in r['issues']))
        self.build(source=src/'index.html',expect=2)

    def test_private_file_not_copied_or_exposed(self):
        src=self.root/'private_test';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body><h1>Test</h1></body></html>')
        (src/'MY_PRIVATE_BACKUP.json').write_text('{"name":"Test"}')
        self.build(source=src/'index.html')
        self.assertFalse((self.dest/'MY_PRIVATE_BACKUP.json').exists())

    def test_email_or_secret_rejected(self):
        src=self.root/'sensitive';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body>secret@example.com</body></html>')
        r=inspect_input(src)
        self.assertFalse(r['static_conversion_eligible'])
        self.build(source=src,expect=2)

    def test_existing_pwa_rejected(self):
        src=self.root/'existing';src.mkdir()
        (src/'index.html').write_text('<html><head><link rel="manifest" href="x.webmanifest"></head><body></body></html>')
        self.assertFalse(inspect_input(src)['static_conversion_eligible'])
        self.build(source=src,expect=2)

    def test_external_script_warns_and_strict_refuses(self):
        src=self.root/'external';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body><script src="https://cdn.example.net/js/a.js"></script></body></html>')
        r=inspect_input(src)
        self.assertTrue(r['static_conversion_eligible'])
        self.assertFalse(r['offline_complete_claim_allowed'])
        self.build(source=src,extra=['--strict-offline'],expect=2)

    def test_javascript_import_refused(self):
        src=self.root/'esm';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body><script src="app.js"></script></body></html>')
        (src/'app.js').write_text('import {foo} from "./module.js";')
        self.assertFalse(inspect_input(src)['static_conversion_eligible'])

    def test_css_url_copies_relative_asset(self):
        src=self.root/'css';src.mkdir();(src/'assets').mkdir()
        (src/'index.html').write_text('<html><head><link rel="stylesheet" href="styles.css"></head><body></body></html>')
        (src/'styles.css').write_text('body{background-image:url("assets/bg.png")}')
        (src/'assets'/'bg.png').write_bytes(b'\x89PNG\r\n\x1a\n')
        r=inspect_input(src)
        self.assertIn('assets/bg.png',r['local_assets'])
        self.build(source=src)
        self.assertTrue((self.dest/'assets'/'bg.png').exists())

    def test_embedded_iframe_requires_review(self):
        src=self.root/'iframe';src.mkdir()
        (src/'index.html').write_text('<html><head></head><body><iframe src="https://example.net"></iframe></body></html>')
        self.assertFalse(inspect_input(src)['static_conversion_eligible'])
        self.build(source=src,expect=2)

    def test_report_outside_public_dist(self):
        p=self.root/'dist'/'report.json'
        self.build(extra=['--report',str(p)],expect=2)

    def test_relative_manifest_portability(self):
        self.build()
        m=json.loads((self.dest/'manifest.webmanifest').read_text())
        self.assertEqual((m['id'],m['start_url'],m['scope']),('./','./','./'))
        self.assertEqual([x['sizes'] for x in m['icons']],['192x192','512x512'])

if __name__=='__main__':unittest.main()
