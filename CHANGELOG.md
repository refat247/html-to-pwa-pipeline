# Changelog

## [0.1.1] - 2026-11-14

### Fixed
- Corrected the mistaken assumption that the canonical Version Manager v1.3.0 source was private.
- Added SHA-pinned public checkout of the canonical source to GitHub CI, with original `--inspect` and `--verify` as explicit jobs. Retained the local public checker as defense-in-depth.
- Synchronized all current SemVer declarations and version-pinned tests. No converter API/schema changes.

### Verification boundary
- This code change does not establish CI PASS, independent security approval, owner merge, skill installation or production deployment. Check the actual workflow logs and reviewer report.

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
