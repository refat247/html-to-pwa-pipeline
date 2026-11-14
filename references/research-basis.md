# Source/reference register (researched 2026-11-14)

This skill is an original orchestration and minimal converter, not a copy of third-party code.

| Public source | Relevant capability | Limitations for our goal |
| --- | --- | --- |
| https://github.com/pwa-builder/PWABuilder | PWA readiness / store packaging | Does not supply our release governance |
| https://github.com/GoogleChrome/workbox | Service-worker caching toolkit | Does not handle app onboarding/privacy/audit |
| https://github.com/vite-pwa/vite-plugin-pwa | Vite integration, assets and Workbox | Requires Vite; don't inject into arbitrary unbuilt HTML |
| https://github.com/elegantapp/pwa-asset-generator | Icons and splash artwork | Assets only |
| https://github.com/danielcregg/pwa-template | Minimal existing-site PWA pattern | Server assumptions; manual deploy/test |
| https://github.com/mattiasgeniar/offline-first-pwa | Stack-neutral offline-first Agent Skill | Detailed policy, not full converter/release engine |
| https://github.com/mpena2099/pwa-nextjs-skill | Chrome installability test harness | Next.js-specific |
| https://github.com/raphaelmans/agent-skills/blob/main/pwa-development/SKILL.md | PWA skill documentation | General guidance, not owner workflow |
| https://github.com/FirebaseExtended/action-hosting-deploy | GitHub PR preview channels | Credentials/security approval needed |
| https://github.com/refat247/medical-cdss-skills/tree/main/version-manager | Mandatory version governance | Manager version is independent of this skill |

References do not imply endorsement or authorize copying third-party source code. Check licenses before any vendoring. We use no vendored implementation dependencies in v0.1.0.
