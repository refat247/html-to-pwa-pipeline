# Changelog

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
