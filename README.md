# HTML-to-PWA Pipeline

**Version:** 0.1.1
**Status:** Experimental Draft PR; local unit and synthetic browser CI tests available. Not merged, installed, independently audited, or deployed.

Portable Agent Skill and Python standard-library proof-of-concept for auditing and converting eligible **static** HTML projects into PWA distributions without mutating original files.

## Quick start

```bash
python scripts/audit_html.py tests/fixtures/index.html --report /tmp/html-audit.json
python scripts/build_pwa.py tests/fixtures/index.html --out /tmp/html-pwa-dist --name "Simple Demo" --short-name "Demo"
python scripts/verify_dist.py /tmp/html-pwa-dist
python -m unittest discover -s tests -v
```

Serve from an HTTPS origin for production, or `python -m http.server 8000 --directory /tmp/html-pwa-dist` for local development. A static conversion is not proof that every original app feature works. Verify in a real browser and on Android/iOS.

The generated service worker uses a network-first navigational shell with cached fallback and caches only same-origin listed assets. It intentionally avoids third-party/API response caching. Other strategies may be preferable for particular UX requirements; review before release.

## Supported input

- A single HTML file, or directory containing `index.html`.
- Local `<link>`, `<script src>`, `<img>`, `<source>`, and CSS `url(...)` references within the project root.
- External HTTP(S) resources are detected and warned; `--strict-offline` refuses them.
- Existing service worker/manifest, unresolved JS module imports, script fetches or suspicious sensitive input result in a manual-review blocker rather than silent modification.

## Owner-controlled deployment

The skill does **not** automatically change GitHub, Firebase or any account. It prepares files and evidence. Code merge, service billing, host/domain changes, and deployment require explicit approval. Preserve a backup and test rollback. Avoid `*.github.io` shared-origin sibling project exposure for private browser storage.

## Version contract

Canonical Version Manager is `refat247/medical-cdss-skills/version-manager` v1.3.0 as of 2026-11-14; historical private copy and repository policy reference v1.2.1. This authority drift is documented and must be reconciled without silently changing historical provenance. Root package declarations are SKILL.md metadata.version, `agents/openai.yaml` version, README and latest CHANGELOG heading. The canonical Version Manager v1.3.0 is accessible in the **public** `refat247/medical-cdss-skills` repository. GitHub Actions sparsely check out that repository at pinned commit `c92d342d77d8b3c433fe16280a0c0d57f4d8f48f` without a PAT, then run the original `--inspect` and `--verify` directly against this skill. `scripts/check_version_contract.py` is also run as defense-in-depth, not as a replacement. Source inspection does not prove execution: confirm the CI logs and exact checked-out commit. Branch protection enforcement requires separate owner verification. The historical private v1.2.1 copy and stale policy remain a documented reconciliation task. Draft v0.1.1 is not a stable v1.0.0 release.

## Provenance

Original skill implementation authored independently. Third-party repositories in references are **design references**, not vendored code. Confirm dependency licenses before copying code. Demonstration fixture is synthetic and contains no user data.
