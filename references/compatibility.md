# Input compatibility and fidelity gates

## Inspect first

Preserve byte-for-byte source and compute SHA-256. Inventory JavaScript/CSS imports, remote network calls, service worker and manifest state, data storage, hardcoded domains, forms requiring backends, authentication and runtime dependencies. Classify: static self-contained, static+assets, static+remote, API-backed, auth-backed, SSR/server-backed. **A visible shell is not a functional app.**

## Supported experimental v0.2.0 converter

- Single-page index.html and direct referenced relative local scripts, CSS and image/font resources, all within source root.
- Relative PWA manifest and Service Worker references (root hosting or subpath).
- Origin-local browser storage can work, but if source relies on file:// URL behavior, flag migration for live test.

## v0.2.0 conservative security boundary

References to executable SVG, inline CSP, dynamic script creation, inline event handlers or JS module imports are not safely converted by this prototype: conversion refuses them for manual review. JS-linked `localStorage` use is counted in the census. `--strict-offline` must reject unresolved fetch/external dependencies rather than claiming full offline completeness.

## Manual-review blockers

Existing Service Worker or manifest, remote API and external JS, JS `import`/`require` (unbundled modules), dynamic import, CSS `@import`, relative fetch/data files, inline base64 private data, forms submitted to remote endpoints, PHP/CGI server logic, offline third-party assets, or insufficiently reviewed copyright/provenance. Existing PWA should be repaired not overwritten.

## Release criteria

Data semantics, first-run dependencies, accessibility and privacy must pass real-origin and physical-device tests. Unknown is never zero. Source remains unchanged. The builder creates a new `dist/` with an explicit inventory and report rather than copying a directory wholesale.

## v0.3.0 remaining risk boundary

Automatic conversion rejects ambiguous runtime code construction and generated filename collisions for manual review. Lexical checks, even strict mode, are not JavaScript semantic analysis and cannot prove that a PWA never makes a request. HTTP-header CSP, physical iOS/Android acceptance and crash interruption are not verified by CLI tests. A public GitHub repository is not automatically licensed for third-party reuse; owner decides the LICENSE separately. Do not label the artifact privacy-certified.
