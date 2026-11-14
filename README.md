# HTML-to-PWA Pipeline

**Version:** 0.2.1
**Status:** Experimental Draft PR; local unit and synthetic browser CI tests available. Not merged, installed, or deployed. Independent Grok Build audits of v0.1.0 and v0.2.0 returned REQUEST_CHANGES; v0.2.1 patch awaits new independent re-audit.

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

- A single HTML file, or directory containing `index.html`.
- Local `<link>`, `<script src>`, `<img>`, `<source>`, and CSS `url(...)` references within the project root.
- External HTTP(S) resources are detected and warned; `--strict-offline` refuses them.
- Existing service worker/manifest, unresolved JS module imports, script fetches or suspicious sensitive input result in a manual-review blocker rather than silent modification.

## Owner-controlled deployment

The skill does **not** automatically change GitHub, Firebase or any account. It prepares files and evidence. Code merge, service billing, host/domain changes, and deployment require explicit approval. Preserve a backup and test rollback. Avoid `*.github.io` shared-origin sibling project exposure for private browser storage.

## Version contract

Canonical Version Manager is `refat247/medical-cdss-skills/version-manager` v1.3.0 as of 2026-11-14; historical private copy and repository policy reference v1.2.1. This authority drift is documented and must be reconciled without silently changing historical provenance. Root package declarations are SKILL.md metadata.version, `agents/openai.yaml` version, README and latest CHANGELOG heading. The canonical Version Manager v1.3.0 is in a **private** repository: the standalone public GitHub Actions token cannot check it out. Public CI therefore uses an independently written strict declaration-drift check (`scripts/check_version_contract.py`), **not the canonical CLI**. Before owner merge, the canonical `--inspect`/`--verify` must still be run in a trusted environment with authorized access; this gate is currently UNVERIFIED. Do not copy private source into this public repo or add a read PAT to untrusted PR jobs. Branch protection enforcement also requires owner configuration. An initial draft v0.2.1 does not count as stable v1.0.0.

## Provenance

Original skill implementation authored independently. Third-party repositories in references are **design references**, not vendored code. Confirm dependency licenses before copying code. Demonstration fixture is synthetic and contains no user data.

## Security hardening v0.2.0
The conservative prototype **refuses unreviewed SVG, CSP and dynamic JS loaders**, rather than producing a false secure/offline-complete claim. Generated cache keys depend on all packaged file bytes, and cache cleanup is isolated by Service Worker scope. Real browser/site verification remains separate from static CLI PASS.
