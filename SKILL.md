---
name: html-to-pwa-pipeline
description: Audit, convert, test, package, and prepare a static HTML project as an installable Progressive Web App with privacy-safe assets, offline behavior and version-governed delivery. Use for HTML-to-PWA conversion, mobile offline debugging, PWA packaging, Firebase Hosting preparation, origin/persistence audits, or PWA release reviews. Never deploy or merge by default.
metadata:
  version: 0.1.0
---

# HTML-to-PWA Pipeline

**Version:** 0.1.0 — experimental draft, NOT independently audited or installed.

## Operating contract

Preserve the source and assess feasibility before changing output. An HTML file can be made installable when it can be served over HTTPS, but a framework, remote API, login, database or server-driven page does not become fully operational offline merely by adding a manifest and service worker.

Modes: `AUDIT_ONLY` (default for review requests), `CONVERT` (safe-copy static source), `REPAIR`, `DEPLOY_PREP`, `RELEASE_REVIEW`, `ROLLBACK_REVIEW`. Never merge, buy a domain, enable billing, configure credentials or deploy without explicit owner approval. Do not print/commit private JSON, credentials, account email lists or patient data. Read `references/compatibility.md` and `references/security.md` for all builds.

## Required workflow

1. **Discover** the existing project, source files, canonical repository, active branch, current version, deployment origin, saved data and latest verified checkpoint. For Chat Mode tasks, first consult the user's KOS SOP and Master Workstream Index, then the existing project tracker. Do not create duplicate trackers.
2. **Classify** input as self-contained static HTML, static multi-asset, API-dependent, auth-dependent or server-dependent. Inventory external CDN calls, fetch/XHR/websocket/storage use, existing manifests/workers, referenced local files and possible sensitive content. A failure to inspect inputs is a BLOCKER, not PASS.
3. **Audit** with `python scripts/audit_html.py PATH --report audit.json`. Refuse unsafe paths and sensitive input until redacted. For interactive apps review first-run dependencies (e.g. a quota must select a previously created plan), forms, keyboard, empty states and data validation.
4. **Convert** only eligible static inputs using `python scripts/build_pwa.py SOURCE --out build/dist --name "Example App" --short-name "Example"`. This copies local referenced assets, adds manifest and service worker, generates two PNG icons and writes `build-report.json` outside `dist`. Original input is never modified. `--strict-offline` refuses external dependencies. Existing manifest or service-worker registration requires manual adjudication, not blind replacement.
5. **Verify** with `python scripts/verify_dist.py build/dist`. Review the privacy audit, generated file manifest and data-storage plan. A successful file copy does not demonstrate installation, offline readiness, storage persistence, browser compatibility or security.
6. **Test** in real HTTP(S) origin with Chromium/Playwright where available: two-tab same-origin save/reopen, localStorage/IndexedDB failure, malformed import, first-run empty state, correct cache updates, offline refresh, 320/390/768/1366 viewport layout, keyboard+dialog and no browser downloads on every edit. If browser testing unavailable, mark UNVERIFIED. Physical Android/iOS real-device acceptance remains a separate gate. Read `references/acceptance-matrix.md`.
7. **Prepare hosting** with explicit HTTPS origin, not shared-host paths for sensitive storage. Offer Firebase Hosting, GitHub Pages (public-only data) or existing hosting as an **option**; do not assume deploy access. See `references/hosting.md`. Deploy only a reviewed allowlist directory, never private backups.
8. **Govern versions** under canonical [`version-manager`](https://github.com/refat247/medical-cdss-skills/tree/main/version-manager): inspect, classify MAJOR/MINOR/PATCH, dry run, synchronize all current declarations in SKILL.md, `agents/openai.yaml`, README, CHANGELOG, scripts/tests as applicable, run `--verify` (zero declarations is failure), review tests, prepare focused PR and require owner-controlled merge. Source edits, successful package QA, GitHub sync, installation and runtime smoke are DIFFERENT statuses.
9. **Audit/re-audit** against reproducible evidence, with independent reviewer on risky changes, and record exact reviewer, timestamp, baseline SHA, environment, PASS/FAIL/PARTIAL/UNVERIFIED, pending blockers, costs and next cursor. Read back any tracker write. No invented acceptance, subscriptions, test results or future deliverables.

## Invocation routing

- One existing `.html` file: audit, then safe-copy builder where supported.
- Static project directory: copy referenced local assets only. Unreferenced files are intentionally excluded; dynamic module imports, CSS processors and other build tools require manual project-specific handling.
- React/Vite project: consider `vite-plugin-pwa` rather than replace its build. The generic builder must refuse to claim support for an unbuilt framework project.
- Backend PHP, Python, Next.js, dynamic API: audit only by default, preserve backend, choose framework-specific strategy.
- Sensitive clinical/financial/account app: privacy threat model, isolated domain, local encryption/sync decisions and explicit clinical/financial safety gates before release.
- Review of existing PWA: do not overwrite its worker or manifest; inspect actual scope and update lifecycle before proposing a repair.

## Expected deliverables

`audit.json`, redacted feasibility verdict, source hash, clean versioned PWA dist folder, `build-report.json`, reusable test/evidence matrix, hosting proposal, rollback plan, and a PR-ready handoff. Report each unavailable output explicitly.

## Compatibility boundaries

This v0.1.0 converter intentionally handles **single-page static HTML and directly referenced local assets**; it does not rewrite JS modules, fetch internal data files, bundle frameworks, automatically make API content offline, encrypt storage, implement account sync or create Firebase projects. Service Worker is a generated shell cache, not proof of offline completeness. Do not use the resulting assets for sensitive production deployment before independent audit.

## References

- `references/compatibility.md`
- `references/security.md`
- `references/hosting.md`
- `references/acceptance-matrix.md`
- `references/research-basis.md`
- `references/installation.md`
