# Changelog

## [0.1.0] - 2026-11-14

### Added
- Initial experimental, standalone HTML-to-PWA Agent Skill bundle.
- Static input audit with dependency, storage, existing-PWA and sensitive-data checks.
- Conservative static HTML builder producing manifest, two icons, service worker and referenced local assets.
- Distribution verifier, synthetic fixtures, automated regression tests and manual device acceptance matrix.
- Version Manager v1.3.0 source-pinned GitHub Actions verification plan.

### Limitations
- Static single-page input and direct asset references only; no framework bundling, backend reconstruction or live API offline translation.
- Browser/PWA installation, service-worker update behavior, real Android and Firebase deployment not yet tested with this skill.
- Package not yet installed, independently reviewed or published in a standalone repository.
