#!/usr/bin/env python3
"""Independent, public-safe SemVer drift check; not the canonical Version Manager.

CI separately executes the public canonical version-manager v1.3.0 from a pinned commit.
This checker exists so public PR CI does not need a private repository access token.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

SEMVER = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
MATCH = re.compile(rf"^{SEMVER}$")


def check(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    errors: list[str] = []
    found: list[tuple[str, str]] = []
    sources = [
        ("SKILL.md", "skill-frontmatter"),
        ("agents/openai.yaml", "agent-version"),
        ("README.md", "readme-version"),
        ("CHANGELOG.md", "changelog-latest"),
    ]
    for relative, kind in sources:
        file = root / relative
        if not file.is_file():
            errors.append(f"Missing required version declaration file: {relative}")
            continue
        text = file.read_text(encoding="utf-8")
        if kind == "skill-frontmatter":
            lines = text.splitlines()
            if not lines or lines[0] != "---" or "---" not in lines[1:]:
                errors.append("SKILL.md is missing YAML frontmatter")
                continue
            fm = "\n".join(lines[1:lines.index("---", 1)])
            versions = re.findall(r"(?m)^\s*version:\s*['\"]?([^\s'\"]+)", fm)
        elif kind == "agent-version":
            versions = re.findall(r"(?m)^version:\s*['\"]?([^\s'\"]+)", text)
        elif kind == "readme-version":
            versions = re.findall(r"(?m)^\*\*Version:\*\*\s*([^\s]+)", text)
        else:
            versions = re.findall(r"(?m)^##\s+\[([^]]+)\]", text)[:1]
        if not versions:
            errors.append(f"No current version declaration in {relative}")
        for version in versions:
            found.append((relative, version))
            if not MATCH.fullmatch(version):
                errors.append(f"Invalid SemVer in {relative}: {version}")
    if not found:
        errors.append("UNRESOLVED: zero version declarations")
    versions = {v for _, v in found}
    if len(versions) > 1:
        errors.append("Version drift: " + "; ".join(f"{f}={v}" for f, v in found))
    return found, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", nargs="?", type=Path, default=Path("."))
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    found, errors = check(a.root.resolve())
    for path, version in found:
        print(f"DECLARATION {path}: {version}")
    for problem in errors:
        print(f"FAIL: {problem}", file=sys.stderr)
    print("PASS: standalone declaration consistency (NOT canonical CLI execution)" if not errors else "FAIL: version contract")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
