# Changelog

## [0.2.1] - 2026-11-14

### Fixed — response to independent Grok Build re-audit
- Replace `cache.addAll(PRECACHE)` with same-origin `fetch(new Request(url, {cache:'reload'}))` and `cache.put()` in the install precache, so asset-only worker upgrades do not copy stale bytes from the browser HTTP cache.
- Extend Chromium smoke test to warm a default static server, inspect newly cached `app.js` bytes, wait for worker activation and verify the new DOM after reload.
- Add regression for HTTP-cache bypass; preserve existing scoped cache cleanup and offline verification.

### Release status
- Experimental draft only; canonical Version Manager v1.3.0 and independent Grok Build re-audit must run on the *new exact HEAD*. Local and GitHub CI PASS alone do not authorize merge.

## [0.2.0] - 2026-11-14

### Changed — security-hardening of experimental inputs
- Fail closed for unreviewed active SVG, inline CSP, JavaScript dynamic injection, external runtime URLs, module imports and existing Service Worker registrations (including script files).
- Service Worker cache identity now includes all local asset bytes, cleanup is scope-specific, and unrelated navigations are never cached as index.html.
- Manifest/Service Worker insertion locates actual HTML closing tags, not unparsed textual matches. Dist verifier requires real manifest node and validates cache token.
- New staged-build rollback, maximum asset/package size, expanded dependency census, and regression tests for Grok Build findings.
- Version changed from experimental v0.1.0 to experimental v0.2.0: stricter input acceptance intentionally changes supported scope, not yet a stable release.

### Not yet verified
- Independent Grok Build re-audit of this new HEAD and physical Android/iOS installation; private canonical Version Manager re-run after bump.

## [0.1.0] - 2026-11-14

### Added
- Initial experimental, standalone HTML-to-PWA Agent Skill bundle.
- Static input audit with dependency, storage, existing-PWA and sensitive-data checks.
- Conservative static HTML builder producing manifest, two icons, service worker and referenced local assets.
- Distribution verifier, synthetic fixtures, automated regression tests and manual device acceptance matrix.
- Public SemVer declaration CI check; canonical private Version Manager v1.3.0 requires authorized pre-merge verification (not auto-fetched by public CI).

### Limitations
- Static single-page input and direct asset references only; no framework bundling, backend reconstruction or live API offline translation.
- Browser/PWA installation, service-worker update behavior, real Android and Firebase deployment not yet tested with this skill.
- Package not yet installed, independently reviewed or published in a standalone repository.
