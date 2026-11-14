# Agent governance for HTML-to-PWA Pipeline

This standalone repository is separate from clinical repos. All changes require:

1. Inspect source, latest commit, owner instructions and canonical Version Manager (currently v1.3.0 in `refat247/medical-cdss-skills/version-manager`). Historical private copy v1.2.1 is not silently promoted or overwritten.
2. Classify SemVer: MAJOR incompatible changes, MINOR backward-compatible additions, PATCH repairs. Never bump silently or rewrite historical changelog entries.
3. Run `--inspect`, preview via `--dry-run`, synchronize SKILL.md/agent metadata/README/latest CHANGELOG heading, run `--verify`, then unit/browser tests.
4. Prepare a focused PR and request owner-controlled merge. Passing GitHub Actions does not imply merge-blocking rule unless owner verifies required status check and a deliberately failing PR cannot merge.
5. Separate tests, upload/installation, runtime activation, website deployment, and physical-device acceptance. Store signed-off evidence in the existing KOS tracker, read it back, and avoid duplicate trackers.
6. No private files, credentials, user account metadata or patient records in public repo, CI logs, generated `dist/` or Notion.

**Public CI credential boundary:** The canonical Version Manager v1.3.0 source is public in `refat247/medical-cdss-skills` and is checked out at the exact pinned SHA `c92d342d77d8b3c433fe16280a0c0d57f4d8f48f` read-only, using sparse checkout and no extra PAT. CI must execute the original `--inspect` and `--verify` plus the local drift checker. Verify the GitHub Actions run before closing the gate. The historical private v1.2.1 copy remains a separate governance reconciliation.
