# Changelog

## [0.3.1] - 2026-11-15

### Fixed — follow-up to Grok Build v0.3.0 independent review
- Reject joined-string and DOM insertion method call patterns (`.join()`, `.append()`, `.prepend()`, `replaceChildren`, `Reflect.get/apply/construct`) in **both inline and referenced JavaScript** before any `--strict-offline` build. This is deliberately conservative and may refuse benign apps for manual review. Synthetic regression reproduces a previously accepted joined `createElement` loader that would fetch a third-party script.
- Remove the remaining `privacy-safe` claim from `agents/openai.yaml` interface metadata. Explicitly describe heuristic review, not privacy or security certification.
- Add focused fail-closed regression cases, version-declaration consistency and refusal/no-dist checks.

### Release boundary
- PATCH from v0.3.0: fixes omissions in the already documented fail-closed dynamic-code policy without introducing a new supported file format or intentional API redesign.
- Experimental draft. Original private canonical Version Manager v1.3.0 verification and independent read-only re-audit of the **new exact commit** remain mandatory. No automatic owner merge, production deployment, privacy certification or Android/iOS installation claim.

## [0.3.0] - 2026-11-14

### Changed — P3 security hardening (owner Option B)
- Restrict ambiguous dynamic code/DOM construction in inline and referenced JavaScript; manual review required instead of treating clever split-string loaders as offline-safe.
- Refuse references to reserved generated PWA filenames rather than silently shadowing a source service worker, manifest or icon.
- Use secure-context capability detection for the Service Worker registrar, including loopback 127.0.0.1 where supported by the browser.
- Extend synthetic regression tests and Chromium localhost/127.0.0.1 smoke workflow.
- Clarify scanner limitations, public-repository license status, unchanged source preservation and scope of test claims.

### Version and release gates
- v0.2.1 to v0.3.0 is a **MINOR** release under pre-1.0 SemVer: previously accepted ambiguous JS constructions are intentionally refused.
- Draft only. Original canonical Version Manager v1.3.0 CLI and independent Grok re-audit required on the new exact HEAD before any owner merge; Android/iOS and production deployment remain UNVERIFIED.

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
