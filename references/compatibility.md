# Input compatibility and fidelity gates

## Inspect first

Preserve byte-for-byte source and compute SHA-256. Inventory JavaScript/CSS imports, remote network calls, service worker and manifest state, data storage, hardcoded domains, forms requiring backends, authentication and runtime dependencies. Classify: static self-contained, static+assets, static+remote, API-backed, auth-backed, SSR/server-backed. **A visible shell is not a functional app.**

## Supported v0.1.0 converter

- Single-page index.html and direct referenced relative local scripts, CSS and image/font resources, all within source root.
- Relative PWA manifest and Service Worker references (root hosting or subpath).
- Origin-local browser storage can work, but if source relies on file:// URL behavior, flag migration for live test.

## Manual-review blockers

Existing Service Worker or manifest, remote API and external JS, JS `import`/`require` (unbundled modules), dynamic import, CSS `@import`, relative fetch/data files, inline base64 private data, forms submitted to remote endpoints, PHP/CGI server logic, offline third-party assets, or insufficiently reviewed copyright/provenance. Existing PWA should be repaired not overwritten.

## Release criteria

Data semantics, first-run dependencies, accessibility and privacy must pass real-origin and physical-device tests. Unknown is never zero. Source remains unchanged. The builder creates a new `dist/` with an explicit inventory and report rather than copying a directory wholesale.
