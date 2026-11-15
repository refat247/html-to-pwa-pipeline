# HTML-to-PWA Pipeline

**Version:** 0.3.2
**Status:** v0.3.2 local experimental candidate pending independent owner review. The repository retains its draft PR and owner-controlled release gates.

Portable Agent Skill and Python standard-library proof-of-concept for auditing and converting eligible **static** HTML projects into PWA distributions without mutating original files.

## Quick start

```bash
python scripts/audit_html.py tests/fixtures/index.html --report /tmp/html-audit.json
python scripts/build_pwa.py tests/fixtures/index.html --out /tmp/html-pwa-dist --name "Simple Demo" --short-name "Demo"
python scripts/verify_dist.py /tmp/html-pwa-dist
python -m unittest discover -s tests -v
```

Serve from an HTTPS origin for production, or `python -m http.server 8000 --directory /tmp/html-pwa-dist` for local development. A static conversion is not proof that every original app feature works. Verify in a real browser and on Android/iOS.

The generated Service Worker uses a network-first navigation for the scoped app shell with cached fallback and precaches only known same-origin static assets. It never stores returned navigation responses in the shell cache. It intentionally avoids third-party/API response caching. Other strategies may be preferable for particular UX requirements; review before release.

## Supported input

- Pass a single `.html` or `.htm` file by name, or a directory containing `index.html`. The generated entry is always `dist/index.html`. The source file keeps its original name and contents.
- Local `<link>`, `<script src>`, `<img>`, `<source>`, and CSS `url(...)` references within the project root.
- External HTTP(S) resources are detected and warned; `--strict-offline` refuses them.
- Existing service worker/manifest, unresolved JS module imports, script fetches or suspicious sensitive input result in a manual-review blocker rather than silent modification.

## Owner-controlled deployment

The skill does **not** automatically change GitHub, Firebase or any account. It prepares files and evidence. Code merge, service billing, host/domain changes, and deployment require explicit approval. Preserve a backup and test rollback. Avoid `*.github.io` shared-origin sibling project exposure for private browser storage.

## Version contract

Canonical Version Manager is `refat247/medical-cdss-skills/version-manager` v1.3.0 as of 2026-11-14; historical private copy and repository policy reference v1.2.1. This authority drift is documented and must be reconciled without silently changing historical provenance. Root package declarations are SKILL.md metadata.version, `agents/openai.yaml` version, README and latest CHANGELOG heading. The canonical Version Manager v1.3.0 is in a **private** repository: the standalone public GitHub Actions token cannot check it out. Public CI therefore uses an independently written strict declaration-drift check (`scripts/check_version_contract.py`), **not the canonical CLI**. Before owner merge, the canonical `--inspect`/`--verify` must still be run in a trusted environment with authorized access; v0.2.1 canonical CLI PASS was reviewer-reported; original CLI must be rerun on v0.3.1 exact HEAD. Do not copy private source into this public repo or add a read PAT to untrusted PR jobs. Branch protection enforcement also requires owner configuration. An initial draft v0.3.1 does not count as stable v1.0.0.

## Provenance

Original skill implementation authored independently. Third-party repositories in references are **design references**, not vendored code. Confirm dependency licenses before copying code. Demonstration fixture is synthetic and contains no user data.

## Security hardening v0.2.0
The conservative prototype **refuses unreviewed SVG, CSP and dynamic JS loaders**, rather than producing a false secure/offline-complete claim. Generated cache keys depend on all packaged file bytes, and cache cleanup is isolated by Service Worker scope. Real browser/site verification remains separate from static CLI PASS.

## v0.3.0 hardening draft

- Service Worker registration tests `localhost` and `127.0.0.1` secure contexts; staging and cache upgrades remain separate tests.
- Refuses generated-file name collisions (`sw.js`, `manifest.webmanifest`, `icon-192.png`, `icon-512.png`) rather than silently replacing referenced source assets.
- Rejects ambiguous script/DOM construction patterns for manual review. This is intentionally restrictive and **not** security certification.
- No explicit LICENSE has been selected by the owner; public visibility does not grant reuse permission. Choose a license only after explicit owner decision.

Experimental status: the v0.3.2 candidate requires independent review before merge or deployment.

### v0.3.1 dynamic-JS boundary (2026-11-15)

The static scanner now fails closed on `.join()` and `.append()` calls (and selected related reflective/DOM calls) even when benign. Complex JavaScript must receive a human/independent source review before conversion; neither `--strict-offline` nor a clean scan can prove absence of obfuscated network activity. Never describe this skill as privacy-safe or security-certified. Owner-approved release and device acceptance are distinct gates.
