# Hosting, update and rollback policies

**Hosting is an explicit post-build step.** Verify the user controls a project and that billing cannot be enabled without explicit approval. Dedicated Firebase Hosting Spark project and HTTPS `*.web.app` origin are supported for static app assets; if personal data exists, isolate the app origin from unrelated content. Never treat the `*.firebaseapp.com` alias as the same storage origin.

Firebase example (do not execute automatically):

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["**/.*", "**/node_modules/**"],
    "headers": [
      {"source":"/", "headers":[{"key":"Cache-Control","value":"no-cache"}]},
      {"source":"/index.html", "headers":[{"key":"Cache-Control","value":"no-cache"}]},
      {"source":"/sw.js", "headers":[{"key":"Cache-Control","value":"no-cache"}]}
    ]
  }
}
```

Run `npm test` and inspect the exact `dist` allowlist before any `firebase deploy --only hosting --project ACTUAL_ID`. Existing code may need a project-specific build or config. CLI command success is not live HTTP/Android acceptance. Confirm content, origin, cache headers, worker scope and runtime version after deploy. Separate a PR preview from production deployment. Rollback using a verified prior release and re-test storage/schema migration; old origins do not transfer localStorage automatically.
