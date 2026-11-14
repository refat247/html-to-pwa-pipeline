"""Conservative, no-network PWA source inventory. Python 3.10+ standard library."""
from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ALLOWED_ASSETS = {'.html', '.htm', '.css', '.js', '.mjs', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.webmanifest'}
FORBIDDEN_PARTS = {'private', 'secrets', 'credentials', 'node_modules', '.git', '.env', 'backup', 'backups', '__pycache__'}
SECRET_RE = re.compile(r'(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk|ghp|gho|github_pat)_[A-Za-z0-9_-]{18,}|\b(?:api[_-]?key|secret[_-]?token)\s*[:=]\s*["\'][A-Za-z0-9_-]{12,})', re.I)
EMAIL_RE = re.compile(r'(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.I)
RUNTIME_RE = re.compile(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\s*\(|EventSource\s*\(|indexedDB\b|localStorage\b|sessionStorage\b|navigator\.serviceWorker\b)', re.I)
IMPORT_RE = re.compile(r'(?m)^\s*(?:import\s+.+?\s+from\s+|import\s*\(|require\s*\()')
CSS_URL_RE = re.compile(r'url\(\s*["\']?([^"\')]+)', re.I)
CSS_IMPORT_RE = re.compile(r'@import\b', re.I)


class LocalTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.remote = []
        self.has_manifest = False
        self.has_sw_reference = False
        self.has_script_inline = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('iframe','object','embed'):
            self.remote.append('Embedded resource requires manual review: '+tag)
        if tag == 'form' and (attrs.get('action') or attrs.get('method','').lower()=='post'):
            self.remote.append('Form submission requires backend review')
        if tag == 'link' and 'manifest' in attrs.get('rel', '').lower().split():
            self.has_manifest = True
        for name in ('src', 'href', 'poster'):
            raw = attrs.get(name)
            if not raw: continue
            if tag == 'a' and name == 'href': continue
            if name == 'href' and tag not in ('link',): continue
            if name == 'src' and tag not in ('script', 'img', 'source', 'video', 'audio'): continue
            self.refs.append(raw)
        for name in ('srcset',):
            if attrs.get(name):
                self.remote.append('srcset requires manual review: '+attrs[name][:70])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_root(path: Path):
    path = path.expanduser().resolve()
    if path.is_dir():
        root, index = path, path / 'index.html'
    elif path.is_file() and path.suffix.lower() in ('.html', '.htm'):
        root, index = path.parent, path
    else:
        raise ValueError('Input must be a static .html file or folder containing index.html')
    if not index.is_file():
        raise ValueError('No index.html at source directory; automatic multi-entry conversion unsupported')
    return root.resolve(), index.resolve()


def suspicious_path(relative: Path) -> bool:
    parts = [p.lower() for p in relative.parts]
    if any(p in FORBIDDEN_PARTS or p.startswith('.env') for p in parts): return True
    nm = relative.name.lower()
    return any(t in nm for t in ('_private', 'private_', 'backup', 'credential', '.pem', '.key', 'token.json'))


def safe_local(ref: str, parent: Path, root: Path) -> tuple[str, Path | None]:
    ref = ref.strip()
    if not ref or ref.startswith(('#', 'data:', 'blob:', 'mailto:', 'tel:', 'javascript:')):
        return 'inline', None
    split = urlsplit(ref)
    if split.scheme or split.netloc or ref.startswith('//'):
        return 'external', None
    if split.path.startswith('/'):
        return 'root_absolute', None
    rel = unquote(split.path)
    result = (parent / rel).resolve()
    if not result.is_relative_to(root): return 'outside_root', result
    if suspicious_path(result.relative_to(root)): return 'sensitive_path', result
    if not result.is_file(): return 'missing', result
    if result.suffix.lower() not in ALLOWED_ASSETS: return 'unsupported_asset', result
    return 'local', result


def inspect_input(path: Path) -> dict:
    root, index = source_root(path)
    html = index.read_text('utf-8')
    parser = LocalTags(); parser.feed(html)
    refs, issues, scanned, remote = list(parser.refs), [], set(), set()
    if parser.has_manifest: issues.append('Existing web manifest: manual integration required')
    if re.search(r'navigator\.serviceWorker\s*\.\s*register\s*\(', html):
        issues.append('Existing Service Worker registration: manual integration required')
    if SECRET_RE.search(html) or EMAIL_RE.search(html):
        issues.append('Sensitive-looking token or email in input HTML: redact before public packaging')
    if re.search(r'\b(?:import\s*\(|import\s+.+?from\s+|require\s*\()', html):
        issues.append('JavaScript module import or require: unbundled module review required')
    if re.search(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\s*\()', html):
        issues.append('Runtime network call in HTML: cannot guarantee offline completeness')
    if re.search(r'\b(?:action=|method=["\']post)', html, re.I):
        issues.append('HTML form/server submission: backend behavior requires inspection')
    if parser.remote: issues.extend(parser.remote)
    cursor = 0
    while cursor < len(refs):
        ref = refs[cursor]; cursor += 1
        # CSS child references carry their own parent directory.
        if isinstance(ref, tuple):
            raw, parent = ref
        else:
            raw, parent = ref, index.parent
        status, target = safe_local(raw, parent, root)
        if status == 'external': remote.add(ref if isinstance(ref, str) else ref[0]); continue
        if status == 'inline': continue
        if status != 'local':
            issues.append(f'{status}: '+(ref if isinstance(ref,str) else ref[0]))
            continue
        relative = target.relative_to(root).as_posix()
        if target in scanned: continue
        scanned.add(target)
        if SECRET_RE.search(target.read_text('utf-8',errors='replace')) if target.suffix.lower() in ('.js','.mjs','.css','.html') else False:
            issues.append('Sensitive-looking token in '+relative)
        if EMAIL_RE.search(target.read_text('utf-8',errors='replace')) if target.suffix.lower() in ('.js','.mjs','.css','.html') else False:
            issues.append('Sensitive-looking email in '+relative)
        if target.suffix.lower() in ('.js','.mjs'):
            j=target.read_text('utf-8',errors='replace')
            if IMPORT_RE.search(j):issues.append('Unbundled JS import in '+relative)
            if re.search(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\s*\()',j):issues.append('Runtime network usage in '+relative)
        if target.suffix.lower()=='.css':
            css=target.read_text('utf-8',errors='replace')
            if CSS_IMPORT_RE.search(css):issues.append('CSS @import in '+relative+' requires review')
            refs.extend([(match, target.parent) for match in CSS_URL_RE.findall(css)])
    fatal=[v for v in issues if not v.startswith('Runtime network call') and not v.startswith('Runtime network usage')]
    return {
        'source':str(index),'source_sha256':sha256(index),'root':str(root),
        'local_assets':sorted(p.relative_to(root).as_posix() for p in scanned),
        'external_refs':sorted(remote),'issues':sorted(set(issues)),
        'has_browser_storage':bool(re.search(r'\b(?:localStorage|sessionStorage|indexedDB)\b', html)),
        'static_conversion_eligible':not bool(fatal),
        'offline_complete_claim_allowed':not bool(remote or issues),
        'mode':'static-single-page'
    }
