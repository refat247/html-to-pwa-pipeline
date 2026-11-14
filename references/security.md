# Security, persistence and data recovery

- Browser `localStorage` is isolated by scheme+host+port, not URL path. Sibling sites on shared `username.github.io` can access same-origin storage. Use a dedicated isolated hostname for personal data.
- `localStorage` is plaintext, not Firebase cloud storage, authenticated backup, cross-device sync or encryption. An XSS in the same app can still read it. Be explicit about threat model and passphrase recovery.
- Never copy secrets, account lists, user backup JSON, patient records, service-account keys, `.env`, `.git`, cached auth tokens, or unknown unreferenced files into public `dist`.
- Validate import JSON schema, reference integrity, uniqueness, types, user prompts and replacement behavior; sanitize DOM output and never render untrusted HTML as code.
- Export a private backup and verify import/recovery on disposable synthetic data before any real records. Preserve original account data; a wrong import may overwrite it.
- Do not cache responses from API/auth endpoints by default, nor embed tokens in service workers. Do not log private user data into CI or Notion.
- Security scanner is heuristic. Passing it is not an independent penetration test. A manually reviewed threat model and external dependency audit remain required.

## Independent Grok Build 14 November 2026 review follow-up

The initial v0.1.0 review was REQUEST_CHANGES: unchanged workers on asset-only builds, stale sibling cache cleanup, nav cache clobber, unsafe SVG documents, invalid inline HTML insertion, and incomplete JS dependency census. v0.2.0 introduces fail-closed handling and regression tests, but independent re-audit of the latest PR SHA is mandatory. Do not infer a whole-program security proof from regex-based static inspection. Incompatible CSP and active SVG require explicit manual remediation rather than silent sanitization.

## v0.3.0 remaining risk boundary

Automatic conversion rejects ambiguous runtime code construction and generated filename collisions for manual review. Lexical checks, even strict mode, are not JavaScript semantic analysis and cannot prove that a PWA never makes a request. HTTP-header CSP, physical iOS/Android acceptance and crash interruption are not verified by CLI tests. A public GitHub repository is not automatically licensed for third-party reuse; owner decides the LICENSE separately. Do not label the artifact privacy-certified.
