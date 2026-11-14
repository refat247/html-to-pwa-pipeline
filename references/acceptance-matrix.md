# Evidence-based acceptance matrix

| Gate | Test | PASS proof | Not a substitute |
| --- | --- | --- | --- |
| Input | SHA-256 and dependency census | Original unchanged, exact source | Guess from filename |
| Privacy | Secrets and public-file inventory | No private files/data in dist | Regex scan alone |
| Static conversion | Manifest/icons/scope/worker | Files and references valid | Installability browser proof |
| Browser behavior | Real HTTPS/localhost + Playwright | Console clean, no missing local assets | jsdom synthetic DOM |
| Persistence | Save → full browser close → reopen same HTTPS URL | Same data visible in device | New tab in same browser context |
| Restore | Export private JSON and import synthetic fixture | Old value restored, no unintended replacement | File existence alone |
| Offline | Online warm load → airplane → refresh | Shell and expected cached data render | `sw.js` exists |
| Updates | Deploy a new cache version | New app loaded, stale cache cleared | PWA cache version string only |
| Mobile | 320, 390, keyboard, modal, touch | Android real-device evidence | CSS lint |
| iOS | Safari Add to Home Screen, offline | Real iOS evidence | Android PASS |
| Hosting | Exact URL and HTTP cache headers | Live response observed | Hosting CLI printed Success |
| Governance | Version Manager verify and CI | Green commit-specific job | Readme claims |
| Release | Independent re-audit + owner merge | Merge SHA and production deployment readback | PR open / unmerged |

Record PASS/FAIL/PARTIAL/UNVERIFIED/BLOCKED independently for each gate. Do not combine into one vague green checkmark.
