# Security, persistence and data recovery

- Browser `localStorage` is isolated by scheme+host+port, not URL path. Sibling sites on shared `username.github.io` can access same-origin storage. Use a dedicated isolated hostname for personal data.
- `localStorage` is plaintext, not Firebase cloud storage, authenticated backup, cross-device sync or encryption. An XSS in the same app can still read it. Be explicit about threat model and passphrase recovery.
- Never copy secrets, account lists, user backup JSON, patient records, service-account keys, `.env`, `.git`, cached auth tokens, or unknown unreferenced files into public `dist`.
- Validate import JSON schema, reference integrity, uniqueness, types, user prompts and replacement behavior; sanitize DOM output and never render untrusted HTML as code.
- Export a private backup and verify import/recovery on disposable synthetic data before any real records. Preserve original account data; a wrong import may overwrite it.
- Do not cache responses from API/auth endpoints by default, nor embed tokens in service workers. Do not log private user data into CI or Notion.
- Security scanner is heuristic. Passing it is not an independent penetration test. A manually reviewed threat model and external dependency audit remain required.
