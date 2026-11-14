#!/usr/bin/env python3
"""Safely build a static single-page HTML PWA without changing original files."""
from __future__ import annotations
import argparse
import hashlib
import os
import tempfile
import json
import re
import shutil
import struct
import sys
import zlib
from html.parser import HTMLParser
from pathlib import Path
from pwa_core import inspect_input, source_root, sha256, cache_token


def make_png(size: int) -> bytes:
    """Simple original navy/mint app mark; standard library only."""
    raw=bytearray()
    for y in range(size):
        raw.append(0)
        for x in range(size):
            border=size//7
            inside=(border<=x<size-border and border<=y<size-border)
            mint=(int(size*.39)<x<int(size*.65) and int(size*.24)<y<int(size*.76))
            white=(inside and not mint)
            raw.extend((255,255,255,255) if white else ((100,214,189,255) if mint else (23,46,85,255)))
    def chunk(kind: bytes, data: bytes):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b'')


class StructuralEnds(HTMLParser):
    """Locate actual </head> and </body> tags, excluding scripts/comments."""
    def __init__(self, html: str):
        super().__init__(convert_charrefs=False)
        self._offsets=[0]
        for line in html.splitlines(keepends=True):
            self._offsets.append(self._offsets[-1]+len(line))
        self.pos={'head':[],'body':[]}

    def handle_endtag(self, tag):
        if tag in self.pos:
            line,col=self.getpos()
            self.pos[tag].append(self._offsets[line-1]+col)


def inject_into_real_closing_tag(html: str, tag: str, insertion: str) -> str:
    parser=StructuralEnds(html)
    parser.feed(html)
    positions=parser.pos[tag]
    if len(positions)!=1:
        raise ValueError(f'Cannot inject PWA metadata: expected one real </{tag}> tag, found {len(positions)}')
    i=positions[0]
    if not re.match(r'</'+tag+r'\s*>',html[i:],re.I):
        raise ValueError(f'HTML closing </{tag}> boundary ambiguous; manual review required')
    return html[:i]+insertion+'\n'+html[i:]


def worker(asset_paths:list[str], token: str) -> str:
    precache=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png']
    precache += ['./'+p for p in asset_paths]
    return ("// Generated scoped PWA shell-only worker; no navigation response caching.\n"
        +"const CACHE_PREFIX='html-pwa-shell-'+encodeURIComponent(new URL(self.registration.scope).pathname)+'-';\n"
        +f"const CACHE=CACHE_PREFIX+'{token}';\nconst PRECACHE={json.dumps(sorted(set(precache)))};\n"
        +"const SHELL_PATH=new URL('./',self.registration.scope).pathname;\n"
        +"const INDEX_PATH=new URL('index.html',self.registration.scope).pathname;\n"
        # cache.addAll() may reuse old bytes from the browser default HTTP cache.
        # Bypass that cache when creating a *new* versioned SW cache.
        +"self.addEventListener('install',event=>{event.waitUntil((async()=>{"
        +"const c=await caches.open(CACHE);"
        +"await Promise.all(PRECACHE.map(async path=>{"
        +"const req=new Request(new URL(path,self.registration.scope),{cache:'reload',credentials:'same-origin'});"
        +"const response=await fetch(req);"
        +"if(!response.ok||response.type==='opaque')throw new Error('Precache fetch refused: '+req.url);"
        +"await c.put(req,response);"
        +"}));await self.skipWaiting();})());});\n"
        +"self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(CACHE_PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});\n"
        +"self.addEventListener('fetch',event=>{const req=event.request;const url=new URL(req.url);"
        +"if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.includes('/api/'))return;"
        +"if(req.mode==='navigate'){if(url.pathname!==SHELL_PATH&&url.pathname!==INDEX_PATH)return;"
        +"event.respondWith(fetch(req).catch(()=>caches.match('./index.html')));return;}"
        +"event.respondWith(caches.match(req,{ignoreSearch:true}).then(hit=>hit||fetch(req)));});\n")


def build(args) -> tuple[dict,Path]:
    root,index=source_root(args.source)
    report=inspect_input(args.source)
    if not report['static_conversion_eligible']:
        raise ValueError('Manual review required; refusing conversion: '+ '; '.join(report['issues']))
    if args.strict_offline and not report['offline_complete_claim_allowed']:
        raise ValueError('External dependencies or runtime calls prevent strict offline claim')
    out=args.out.expanduser().resolve()
    report_path=(args.report or out.parent/'build-report.json').expanduser().resolve()
    if report_path.is_relative_to(out):
        raise ValueError('Never publish the audit report inside dist')
    if out==root or out.is_relative_to(root):
        raise ValueError('Output must be outside input source directory to preserve input and avoid recursion')
    if index.name!='index.html':
        raise ValueError('Source HTML must be named index.html in this draft; do not rename files silently')
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory must be empty or absent; no overwrites')
    out.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.'+out.name+'-staging-',dir=str(out.parent))).resolve()
    try:
        return _build_staged(root,index,report,args,out,staging)
    finally:
        if staging.exists():shutil.rmtree(staging)

def _build_staged(root,index,report,args,out,staging):
    html=index.read_text('utf-8')
    head_tags=f'<link rel="manifest" href="./manifest.webmanifest">\n<meta name="theme-color" content="{args.theme_color}">'
    html=inject_into_real_closing_tag(html,'head',head_tags)
    registration="<script>if('serviceWorker' in navigator && window.isSecureContext){window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(error=>console.warn('Service worker failed:',error)));}</script>"
    html=inject_into_real_closing_tag(html,'body',registration)
    (staging/'index.html').write_text(html,'utf-8')
    for asset in report['local_assets']:
        src=root/asset;dst=staging/asset;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    manifest={
        'name':args.name,'short_name':args.short_name,'description':'Static offline-capable HTML app',
        'id':'./','start_url':'./','scope':'./','display':'standalone',
        'background_color':args.theme_color,'theme_color':args.theme_color,
        'icons':[{'src':f'./icon-{n}.png','sizes':f'{n}x{n}','type':'image/png','purpose':'any'} for n in (192,512)]
    }
    (staging/'manifest.webmanifest').write_text(json.dumps(manifest,indent=2)+'\n','utf-8')
    for s in (192,512):(staging/f'icon-{s}.png').write_bytes(make_png(s))
    src_assets={p.relative_to(staging).as_posix():p for p in staging.rglob('*') if p.is_file()}
    salt=cache_token(src_assets)
    (staging/'sw.js').write_text(worker(report['local_assets'],salt),'utf-8')
    contents=sorted(p.relative_to(staging).as_posix() for p in staging.rglob('*') if p.is_file())
    result={'status':'BUILD_CREATED_NOT_RUNTIME_VERIFIED','source_sha256':report['source_sha256'],
            'dist_files':contents,'dist_sha256':{p:sha256(staging/p) for p in contents},
            'offline_complete_claim_allowed':report['offline_complete_claim_allowed'],
            'external_refs':report['external_refs'],'issues':report['issues']}
    # Stage everything before touching the final directory. Failed builds leave it empty.
    if out.exists():out.rmdir()
    os.replace(staging,out)
    return result,out


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--name',required=True);parser.add_argument('--short-name',required=True)
    parser.add_argument('--theme-color',default='#172e55');parser.add_argument('--strict-offline',action='store_true')
    parser.add_argument('--report',type=Path,help='Report destination OUTSIDE public dist (optional)')
    args=parser.parse_args(argv)
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',args.theme_color):parser.error('Theme color must be #RRGGBB')
    try:
        report,out=build(args)
        path=args.report or out.parent/'build-report.json'
        path=path.expanduser().resolve()
        if path.is_relative_to(out):raise ValueError('Never publish the audit report inside dist')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n','utf-8')
    except (ValueError,OSError,UnicodeError) as e:
        print('BUILD REFUSED: '+str(e),file=sys.stderr);return 2
    print(f"Built {len(report['dist_files'])} public files. Runtime and device tests UNVERIFIED.")
    return 0

if __name__=='__main__':sys.exit(main())
