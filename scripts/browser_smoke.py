#!/usr/bin/env python3
"""Optional real-origin Chromium check: PWA lifecycle, save/reopen, offline shell."""
from __future__ import annotations
import argparse
import json
import sys
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout, Error as BrowserError


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url',help='Localhost URL served from generated dist root')
    parser.add_argument('--dist',type=Path,help='Disposable generated dist served at URL; enables browser upgrade/security regressions')
    opts=parser.parse_args(argv)
    try:
        with sync_playwright() as p:
            chrome=Path(p.chromium.executable_path)
            binary=str(chrome) if chrome.exists() else shutil.which("chromium")
            if not binary:raise BrowserError("No Chromium executable installed")
            browser=p.chromium.launch(headless=True, executable_path=binary)
            ctx=browser.new_context(viewport={'width':390,'height':800},service_workers='allow')
            page=ctx.new_page()
            errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            response=page.goto(opts.url,wait_until='domcontentloaded',timeout=30000)
            assert response and response.status==200,'App HTTP error'
            assert page.title()=='Synthetic Demo','Wrong HTML payload'
            page.locator('#save').click()
            assert page.evaluate("localStorage.getItem('synthetic-test')")=='42','Save failed'
            page.wait_for_function("() => navigator.serviceWorker && navigator.serviceWorker.controller !== null",timeout=30000)
            page2=ctx.new_page()
            page2.goto(opts.url,wait_until='domcontentloaded',timeout=30000)
            assert page2.evaluate("localStorage.getItem('synthetic-test')")=='42','Reopen failed'
            ctx.set_offline(True)
            page2.reload(wait_until='domcontentloaded',timeout=15000)
            assert page2.locator('h1').inner_text()=='Synthetic Demo','Offline shell failed'
            assert page2.evaluate("localStorage.getItem('synthetic-test')")=='42','Offline storage lost'
            ctx.set_offline(False)
            if opts.dist:
                # Test a truly installed worker's asset-only update without changing index.html.
                from build_pwa import worker
                from pwa_core import cache_token,sha256
                root=opts.dist.resolve()
                app_js=root/'app.js'
                original=app_js.read_text('utf-8')
                # Warm the default HTTP cache before updating the installed SW.
                page2.reload(wait_until='domcontentloaded',timeout=15000)
                page2.reload(wait_until='domcontentloaded',timeout=15000)
                assert page2.evaluate("() => window.__PWA_ASSET_REVISION===undefined"),'Old asset fixture unexpectedly changed'
                sw_path=root/'sw.js'
                old_sha=sha256(sw_path)
                app_js.write_text(original+"\nwindow.__PWA_ASSET_REVISION='B';\n",'utf-8')
                paths={p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and p.name!='sw.js'}
                assets=[p for p in paths if p not in ('index.html','manifest.webmanifest','icon-192.png','icon-512.png')]
                new_token=cache_token(paths)
                sw_path.write_text(worker(assets,new_token),'utf-8')
                assert old_sha!=sha256(sw_path),'Asset-only edit failed to change worker bytes'
                # Simulate a sibling app's cache on the same origin.
                page2.evaluate("() => caches.open('html-pwa-shell-SIBLING-DO-NOT-DELETE').then(c=>c.put('/sibling-test',new Response('keep')))")
                page2.evaluate("() => navigator.serviceWorker.getRegistration().then(r=>r.update())")
                page2.wait_for_function(f"() => caches.keys().then(keys=>keys.some(k=>k.includes('{new_token}')))",timeout=20000)
                # Check that the new SW cache really contains B, not stale A.
                page2.wait_for_function(f"async () => {{const keys=await caches.keys();const key=keys.find(k=>k.includes('{new_token}'));"
                    f"if(!key)return false;const c=await caches.open(key);const r=await c.match('./app.js');"
                    f"return r&&(await r.text()).includes('PWA_ASSET_REVISION');}}",timeout=20000)
                page2.wait_for_function("async () => {const reg=await navigator.serviceWorker.getRegistration();"
                    "return reg&&reg.active&&reg.active.state==='activated'&&!reg.installing&&!reg.waiting;}",timeout=20000)
                page2.wait_for_function(f"() => caches.keys().then(keys=>!keys.some(k=>k.startsWith('html-pwa-shell-%2F-')&&!k.includes('{new_token}')))",timeout=20000)
                page2.reload(wait_until='domcontentloaded',timeout=15000)
                page2.wait_for_function("() => window.__PWA_ASSET_REVISION==='B'",timeout=15000)
                assert page2.evaluate("() => caches.keys().then(keys=>keys.includes('html-pwa-shell-SIBLING-DO-NOT-DELETE'))"),'Sibling cache deleted'
                # A navigated HTML with data-like content must never overwrite cached shell.
                other=root/'other.html'
                other.write_text('<html><body>synthetic-marker-secret</body></html>','utf-8')
                page2.goto(opts.url.rstrip('/')+'/other.html',wait_until='domcontentloaded')
                assert 'synthetic-marker-secret' in page2.content(),'Synthetic other page did not load'
                html_entry=page2.evaluate("() => caches.keys().then(keys=>keys.filter(k=>k.startsWith('html-pwa-shell-%2F-'))).then(keys=>caches.open(keys[0])).then(c=>c.match('./index.html')).then(r=>r.text())")
                assert 'synthetic-marker-secret' not in html_entry,'Navigation clobbered cached app shell'
                print('PASS Chromium regression: warmed-HTTP-cache asset-only SW update, sibling-cache preservation, navigation-cache isolation')
            assert not errors,'JS errors: '+'; '.join(errors)
            print('PASS real-origin Chromium: save→second tab, worker offline refresh, persistent localStorage')
            browser.close()
        return 0
    except (BrowserTimeout,BrowserError,AssertionError) as exc:
        print('BROWSER SMOKE FAIL: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
