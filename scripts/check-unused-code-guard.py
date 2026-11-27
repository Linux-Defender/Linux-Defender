#!/usr/bin/env python3
"""Fail when TypeScript config stops rejecting unused locals/parameters.

CodeQL repeatedly reported `js/unused-local-variable` after refactors because
`tsc --noEmit` did not enable noUnusedLocals. These settings make that class of
dead code fail at the local check stage, before review or CodeQL.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = (
    "desktop/tsconfig.json",
    "mcp/linux-defender-assist/tsconfig.json",
    "website/tsconfig.json",
)
OPTIONS = ("noUnusedLocals", "noUnusedParameters")


def main() -> int:
    failures: list[str] = []
    for rel in PROJECTS:
        path = ROOT / rel
        try:
            config = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{rel}: cannot read tsconfig ({exc})")
            continue
        options = config.get("compilerOptions", {})
        for option in OPTIONS:
            if options.get(option) is not True:
                failures.append(f"{rel}: compilerOptions.{option} must be true")
    if failures:
        print("Unused-code guard failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Unused-code guard OK: TypeScript rejects unused locals and parameters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
