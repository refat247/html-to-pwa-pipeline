#!/usr/bin/env python3
"""Check static distribution structure and relative references. Not a runtime test."""
import argparse
import json
import struct
import sys
from html.parser import HTMLParser
from pathlib import Path
from pwa_core import EMAIL_RE,SECRET_RE,suspicious_path,safe_local,cache_token

class DistParser(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.head=False;self.manifest_links=[];self.script=False;self.inline_scripts=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=='head':self.head=True
        if tag=='script':self.script=True
        if tag=='link' and self.head and 'manifest' in d.get('rel','').lower().split():self.manifest_links.append(d.get('href'))
        for n in ('href','src','poster'):
            if n in d and tag in ('link','script','img','source','video'):
                self.refs.append(d[n])
    def handle_endtag(self,tag):
        if tag=='head':self.head=False
        if tag=='script':self.script=False
    def handle_data(self,data):
        if self.script:self.inline_scripts.append(data)


def verify(root:Path):
    root=root.resolve()
    must=['index.html','sw.js','manifest.webmanifest','icon-192.png','icon-512.png']
    errs=[]
    for name in must:
        if not (root/name).is_file():errs.append('Missing '+name)
    if errs:return errs
    manifest=json.loads((root/'manifest.webmanifest').read_text('utf-8'))
    if manifest.get('display')!='standalone' or manifest.get('start_url')!='./' or manifest.get('scope')!='./':errs.append('Manifest must use portable relative scope/start URL')
    if not manifest.get('name') or not manifest.get('short_name'):errs.append('Manifest names missing')
    for size in (192,512):
        p=root/f'icon-{size}.png';b=p.read_bytes()
        if not b.startswith(b'\x89PNG\r\n\x1a\n') or len(b)<24 or struct.unpack('>II',b[16:24])!=(size,size):errs.append('Icon invalid size '+str(size))
    html=(root/'index.html').read_text('utf-8')
    parsed=DistParser();parsed.feed(html)
    if parsed.manifest_links!=['./manifest.webmanifest']:
        errs.append('HTML lacks exactly one real manifest link in head')
    registrar='\n'.join(parsed.inline_scripts)
    if "navigator.serviceWorker.register('./sw.js')" not in registrar:
        errs.append('HTML lacks a real inline Service Worker registrar')
    for ref in parsed.refs:
        status,p=safe_local(ref,root,root)
        if status not in ('local','external','inline'):errs.append('Invalid asset reference '+ref+': '+status)
    worker=(root/'sw.js').read_text('utf-8')
    import re
    if 'CACHE_PREFIX=' not in worker or 'url.pathname!==SHELL_PATH' not in worker:
        errs.append('Worker must scope cache cleanup and navigation handling')
    if "c.put('./index.html'" in worker or "cache.put('./index.html'" in worker:
        errs.append('Worker must not cache arbitrary network navigation as shell')
    expected_token=cache_token({p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and p.name!='sw.js'})
    if f"CACHE=CACHE_PREFIX+'{expected_token}'" not in worker:
        errs.append('Worker cache version does not match public asset bytes')
    precache=re.search(r'const PRECACHE=(\[[^;]+\]);',worker)
    if not precache:errs.append('Service worker precache list missing')
    else:
        try:
            for ref in json.loads(precache.group(1)):
                status,_=safe_local(ref,root,root)
                if ref=='./':continue
                if status!='local':errs.append('Precache target invalid: '+ref+' '+status)
        except json.JSONDecodeError:errs.append('Service worker precache list invalid JSON')
    for required in ('self.addEventListener(\'install\'','self.addEventListener(\'fetch\'','self.addEventListener(\'activate\''):
        if required not in worker:errs.append('Service worker handler missing '+required)
    for p in root.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(root)
        if suspicious_path(rel):errs.append('Sensitive filename in dist: '+str(rel))
        if p.is_symlink() or p.suffix.lower()=='.svg':errs.append('Active SVG or symlink forbidden in dist: '+str(rel))
        if p.suffix.lower() in ('.html','.htm','.js','.css','.json','.webmanifest'):
            t=p.read_text('utf-8',errors='replace')
            if EMAIL_RE.search(t) or SECRET_RE.search(t):errs.append('Sensitive-looking content in '+str(rel))
    return errs


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('dist',type=Path);args=ap.parse_args(argv)
    if not args.dist.is_dir():print('VERIFY FAIL: dist missing',file=sys.stderr);return 2
    try:e=verify(args.dist)
    except (OSError,ValueError,UnicodeError,json.JSONDecodeError) as ex:print('VERIFY FAIL: '+str(ex),file=sys.stderr);return 2
    if e:
        for line in e:print('FAIL '+line,file=sys.stderr)
        return 1
    print('PASS: static dist structure, paths and privacy heuristics. Browser/device gates UNVERIFIED.')
    return 0
if __name__=='__main__':sys.exit(main())
