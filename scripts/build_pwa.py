#!/usr/bin/env python3
"""Safely build a static single-page HTML PWA without changing original files."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
import zlib
from pathlib import Path
from pwa_core import inspect_input, source_root, sha256


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


def worker(asset_paths:list[str], token: str) -> str:
    precache=['./','./index.html','./manifest.webmanifest','./icon-192.png','./icon-512.png']
    precache += ['./'+p for p in asset_paths]
    return ("// Generated shell-only worker. Review offline strategy and private data threats before release.\n"
        +f"const CACHE='html-pwa-shell-{token}';\nconst PRECACHE={json.dumps(sorted(set(precache)))};\n"
        +"self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(c=>c.addAll(PRECACHE)).then(()=>self.skipWaiting()));});\n"
        +"self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('html-pwa-shell-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});\n"
        +"self.addEventListener('fetch',event=>{const req=event.request;const url=new URL(req.url);"
        +"if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.includes('/api/'))return;"
        +"if(req.mode==='navigate'){event.respondWith(fetch(req).then(r=>{if(r.ok){const copy=r.clone();caches.open(CACHE).then(c=>c.put('./index.html',copy));}return r;}).catch(()=>caches.match('./index.html')));return;}"
        +"event.respondWith(caches.match(req).then(hit=>hit||fetch(req)));});\n")


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
    out.mkdir(parents=True,exist_ok=True)
    html=index.read_text('utf-8')
    head_tags=f'<link rel="manifest" href="./manifest.webmanifest">\n<meta name="theme-color" content="{args.theme_color}">'
    html,head_count=re.subn(r'</head\s*>',lambda _:head_tags+'\n</head>',html,count=1,flags=re.I)
    if head_count!=1:raise ValueError('Cannot inject manifest: source missing </head>')
    registration="<script>if('serviceWorker' in navigator && (location.protocol==='https:' || location.hostname==='localhost')){window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(error=>console.warn('Service worker failed:',error)));}</script>"
    html,body_count=re.subn(r'</body\s*>',lambda _:registration+'\n</body>',html,count=1,flags=re.I)
    if body_count!=1:raise ValueError('Cannot inject worker: source missing </body>')
    (out/'index.html').write_text(html,'utf-8')
    for asset in report['local_assets']:
        src=root/asset;dst=out/asset;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    manifest={
        'name':args.name,'short_name':args.short_name,'description':'Static offline-capable HTML app',
        'id':'./','start_url':'./','scope':'./','display':'standalone',
        'background_color':args.theme_color,'theme_color':args.theme_color,
        'icons':[{'src':f'./icon-{n}.png','sizes':f'{n}x{n}','type':'image/png','purpose':'any'} for n in (192,512)]
    }
    (out/'manifest.webmanifest').write_text(json.dumps(manifest,indent=2)+'\n','utf-8')
    for s in (192,512):(out/f'icon-{s}.png').write_bytes(make_png(s))
    salt=hashlib.sha256((sha256(index)+'\n'+'\n'.join(report['local_assets'])).encode()).hexdigest()[:16]
    (out/'sw.js').write_text(worker(report['local_assets'],salt),'utf-8')
    contents=sorted(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file())
    result={'status':'BUILD_CREATED_NOT_RUNTIME_VERIFIED','source_sha256':report['source_sha256'],
            'dist_files':contents,'dist_sha256':{p:sha256(out/p) for p in contents},
            'offline_complete_claim_allowed':report['offline_complete_claim_allowed'],
            'external_refs':report['external_refs'],'issues':report['issues']}
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
