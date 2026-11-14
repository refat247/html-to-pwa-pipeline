"""Conservative, no-network PWA source inventory. Python 3.10+ standard library."""
from __future__ import annotations

import hashlib
import re
import struct
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ALLOWED_ASSETS = {'.html', '.htm', '.css', '.js', '.mjs', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.webmanifest'}
GENERATED_NAMES = {'sw.js', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'}
FORBIDDEN_PARTS = {'private', 'secrets', 'credentials', 'node_modules', '.git', '.env', 'backup', 'backups', '__pycache__'}
SECRET_RE = re.compile(r'(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:sk|ghp|gho|github_pat)_[A-Za-z0-9_-]{18,}|\b(?:api[_-]?key|secret[_-]?token)\s*[:=]\s*["\'][A-Za-z0-9_-]{12,})', re.I)
EMAIL_RE = re.compile(r'(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.I)
RUNTIME_RE = re.compile(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\s*\(|EventSource\s*\(|indexedDB\b|localStorage\b|sessionStorage\b|navigator\.serviceWorker\b)', re.I)
IMPORT_RE = re.compile(r'\b(?:import\s*\(|import\s+[^;\n]+?\s+from\s*[\"\']|require\s*\()')
CSS_URL_RE = re.compile(r'url\(\s*["\']?([^"\')]+)', re.I)
CSS_IMPORT_RE = re.compile(r'@import\b', re.I)
SW_REGISTER_RE = re.compile(r'\bnavigator\s*\.\s*serviceWorker\s*\.\s*register\s*\(', re.I)
NETWORK_RE = re.compile(r'\b(?:fetch\s*\(|XMLHttpRequest\b|WebSocket\s*\(|EventSource\s*\(|sendBeacon\s*\(|https?://)', re.I)
UNSAFE_DYNAMIC_RE = re.compile(r'\b(?:document\.write\s*\(|insertAdjacentHTML\s*\(|\.innerHTML\s*=|createElement\s*\(\s*[\"\']script[\"\']\s*\()', re.I)
# Security-first default: static inspection is not a JS parser or an SVG sanitizer.
# Fail closed on dynamic code/asset constructors (including split-string loader shapes).
# This is deliberately over-sensitive: it is NOT full JavaScript analysis.
DYNAMIC_CODE_RE = re.compile(
    r'''(?ix)
    \b(?:eval|Function|importScripts|setAttribute|appendChild|insertBefore|replaceChild|createElement|createElementNS|String\.fromCharCode|atob|setInterval|setTimeout)\s*\(
    | \b(?:document|window|globalThis)\s*\[
    | \b(?:create|cre|Element|script)\s*["']\s*\+\s*["']
    | \b(?:src|href)\s*\+\s*=
    | \bnew\s+Function\b
    | \b(?:import|export)\s*\(
    ''')
ACTIVE_SVG_RE = re.compile(r'(?i)\.svg$')
MAX_ASSET_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024


def cache_token(paths: dict[str, Path]) -> str:
    """Content-derived identity, deterministic across OSes and build roots."""
    h = hashlib.sha256()
    for rel, path in sorted(paths.items()):
        raw = path.read_bytes()
        name = rel.encode('utf-8')
        h.update(struct.pack('>Q', len(name)))
        h.update(name)
        h.update(struct.pack('>Q', len(raw)))
        h.update(raw)
    return h.hexdigest()[:16]



class LocalTags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.remote = []
        self.has_manifest = False
        self.has_sw_reference = False
        self.has_script_inline = False
        self.has_csp = False
        self.has_base = False
        self._script = False
        self.inline_scripts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script':
            self._script = True
        if tag == 'base':
            self.has_base = True
        if tag == 'meta' and attrs.get('http-equiv','').strip().lower() == 'content-security-policy':
            self.has_csp = True
        if tag in ('iframe','object','embed'):
            self.remote.append('Embedded resource requires manual review: '+tag)
        if tag == 'form' and (attrs.get('action') or attrs.get('method','').lower()=='post'):
            self.remote.append('Form submission requires backend review')
        if tag == 'link' and 'manifest' in attrs.get('rel', '').lower().split():
            self.has_manifest = True
        if any(name.lower().startswith('on') for name in attrs):
            self.remote.append('Inline event handler requires manual review: '+tag)
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

    def handle_endtag(self,tag):
        if tag == 'script':
            self._script = False

    def handle_data(self, data):
        if self._script:
            self.inline_scripts.append(data)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)



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
    if ref.lower().startswith(('javascript:', 'data:', 'blob:')):
        return 'unsafe_scheme', None
    if not ref or ref.startswith(('#', 'mailto:', 'tel:')):
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
    if parser.has_base: issues.append('HTML base href: changes relative URL semantics; manual review required')
    if parser.has_csp: issues.append('Content-Security-Policy meta: injected inline registrar may violate CSP; manual integration required')
    if SW_REGISTER_RE.search(html):
        issues.append('Existing Service Worker registration: manual integration required')
    if SECRET_RE.search(html) or EMAIL_RE.search(html):
        issues.append('Sensitive-looking token or email in input HTML: redact before public packaging')
    if IMPORT_RE.search(html):
        issues.append('JavaScript module import or require: unbundled module review required')
    if DYNAMIC_CODE_RE.search('\n'.join(parser.inline_scripts)):
        issues.append('Dynamic code or DOM construction in inline JS: manual review required')
    if NETWORK_RE.search('\n'.join(parser.inline_scripts)):
        issues.append('Runtime network call in HTML: cannot guarantee offline completeness')
    if re.search(r'\b(?:action=|method=["\']post)', html, re.I):
        issues.append('HTML form/server submission: backend behavior requires inspection')
    if UNSAFE_DYNAMIC_RE.search('\n'.join(parser.inline_scripts)):
        issues.append('Dynamic HTML/script injection in inline JS: manual security review required')
    if re.search(r'https?://','\n'.join(parser.inline_scripts),re.I):
        issues.append('Unverified external URL in inline JS: manual security review required')
    if parser.remote: issues.extend(parser.remote)
    size_total = index.stat().st_size
    if size_total > MAX_ASSET_BYTES:
        issues.append('Source index.html exceeds maximum supported asset size')
    has_storage = bool(re.search(r'\b(?:localStorage|sessionStorage|indexedDB)\b', html))
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
        if relative.lower() in GENERATED_NAMES:
            issues.append('Generated PWA output filename collision: '+relative)
            continue
        if target in scanned: continue
        if target.suffix.lower() in ('.html', '.htm'):
            issues.append('Referenced secondary HTML page requires manual review: '+relative)
        size = target.stat().st_size
        size_total += size
        if size > MAX_ASSET_BYTES or size_total > MAX_TOTAL_BYTES:
            issues.append('Asset/package exceeds conservative 20MB per-file or 50MB total size cap: '+relative)
        scanned.add(target)
        if target.suffix.lower()=='.svg':
            issues.append('SVG assets require manual sanitization or raster conversion: '+relative)
            # An SVG is an active standalone document on the same origin.
            # Never allow an SVG merely because img src rendering is inert.

        if SECRET_RE.search(target.read_text('utf-8',errors='replace')) if target.suffix.lower() in ('.js','.mjs','.css','.html') else False:
            issues.append('Sensitive-looking token in '+relative)
        if EMAIL_RE.search(target.read_text('utf-8',errors='replace')) if target.suffix.lower() in ('.js','.mjs','.css','.html') else False:
            issues.append('Sensitive-looking email in '+relative)
        if target.suffix.lower() in ('.js','.mjs'):
            j=target.read_text('utf-8',errors='replace')
            if IMPORT_RE.search(j):issues.append('Unbundled JS import in '+relative)
            if DYNAMIC_CODE_RE.search(j):issues.append('Dynamic code or DOM construction in '+relative+' requires manual review')
            if SW_REGISTER_RE.search(j):issues.append('Existing Service Worker registration in '+relative)
            if UNSAFE_DYNAMIC_RE.search(j):issues.append('Dynamic HTML/script injection in '+relative+' requires manual review')
            if NETWORK_RE.search(j):issues.append('Runtime network usage in '+relative)
            if re.search(r'https?://',j,re.I):issues.append('Unverified external URL in JS requires manual review: '+relative)
            if re.search(r'\b(?:localStorage|sessionStorage|indexedDB)\b',j):has_storage=True

        if target.suffix.lower()=='.css':
            css=target.read_text('utf-8',errors='replace')
            if CSS_IMPORT_RE.search(css):issues.append('CSS @import in '+relative+' requires review')
            refs.extend([(match, target.parent) for match in CSS_URL_RE.findall(css)])
    fatal=[v for v in issues if not v.startswith('Runtime network call') and not v.startswith('Runtime network usage')]
    return {
        'source':str(index),'source_sha256':sha256(index),'root':str(root),
        'local_assets':sorted(p.relative_to(root).as_posix() for p in scanned),
        'external_refs':sorted(remote),'issues':sorted(set(issues)),
        'has_browser_storage':has_storage,
        'static_conversion_eligible':not bool(fatal),
        'offline_complete_claim_allowed':not bool(remote or issues),
        'mode':'static-single-page'
    }
