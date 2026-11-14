# Portable skill installation and activation

The standalone GitHub repository is the authoritative package once created, reviewed and merged. A GitHub commit does not install a skill into any agent automatically.

1. Create a **separate repository** for this non-clinical skill. Use one canonical URL. Do not place it inside medical-cdss-skills or copy it to both repos as competing live sources.
2. Inspect all files, current version, license, dependencies and safety warnings. Validate with the pinned canonical Version Manager and Python tests; capture CI result.
3. For Codex, install the reviewed skill root under a supported `.agents/skills/html-to-pwa-pipeline/` directory or the current user's approved skills directory. For Claude Code, use a supported `.claude/skills/html-to-pwa-pipeline/` directory. For other agents, consult that product's current skill path and activation rules rather than guessing.
4. Start a fresh session and invoke the named skill explicitly on the synthetic fixture. Confirm the agent actually loaded SKILL.md, ran an audit and refused to deploy. If no activation evidence, mark NOT_INSTALLED or UNVERIFIED.
5. Only after that apply it to a real user HTML; keep original source and private data separate. Record repo SHA/version, exact install path, runtime smoke, owner approval and update in the existing KOS tracker.

Avoid auto-updating skill files from an unreviewed remote branch. Do not put GitHub tokens, Firebase service-account secrets or customer backup exports in skill package config.
