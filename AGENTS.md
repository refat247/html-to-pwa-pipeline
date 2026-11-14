# Agent governance for HTML-to-PWA Pipeline

This standalone repository is separate from clinical repos. All changes require:

1. Inspect source, latest commit, owner instructions and canonical Version Manager (currently v1.3.0 in `refat247/medical-cdss-skills/version-manager`). Historical private copy v1.2.1 is not silently promoted or overwritten.
2. Classify SemVer: MAJOR incompatible changes, MINOR backward-compatible additions, PATCH repairs. Never bump silently or rewrite historical changelog entries.
3. Run `--inspect`, preview via `--dry-run`, synchronize SKILL.md/agent metadata/README/latest CHANGELOG heading, run `--verify`, then unit/browser tests.
4. Prepare a focused PR and request owner-controlled merge. Passing GitHub Actions does not imply merge-blocking rule unless owner verifies required status check and a deliberately failing PR cannot merge.
5. Separate tests, upload/installation, runtime activation, website deployment, and physical-device acceptance. Store signed-off evidence in the existing KOS tracker, read it back, and avoid duplicate trackers.
6. No private files, credentials, user account metadata or patient records in public repo, CI logs, generated `dist/` or Notion.

**Public CI credential boundary:** The canonical Version Manager v1.3.0 repository is private. Never place its source or a read PAT in this public PR. CI runs an independent SemVer drift checker; the owner must separately verify canonical `--inspect`/`--verify` before merge.

**Experimental compatibility boundary (0.x):** The 2026-11-14 v0.2.0 revision intentionally narrows accepted unsafe inputs compared with v0.1.0. Since the package remains pre-1.0 and no stable compatibility guarantee has been published, this breaking experimental scope change is classified as an explicit 0.x MINOR increase. Independent reviewer and owner must verify this classification before merging.
