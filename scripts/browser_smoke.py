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
            assert not errors,'JS errors: '+'; '.join(errors)
            print('PASS real-origin Chromium: save→second tab, worker offline refresh, persistent localStorage')
            browser.close()
        return 0
    except (BrowserTimeout,BrowserError,AssertionError) as exc:
        print('BROWSER SMOKE FAIL: '+str(exc),file=sys.stderr);return 1

if __name__=='__main__':sys.exit(main())
