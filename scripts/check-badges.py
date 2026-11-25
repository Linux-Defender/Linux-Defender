#!/usr/bin/env python3
"""Fail when a workflow has no README status badge."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"


def main() -> int:
    readme = README.read_text(encoding="utf-8") if README.exists() else ""
    missing = []
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    for path in workflows:
        needle = f"actions/workflows/{path.name}/badge.svg"
        if needle not in readme:
            missing.append(path.name)
    if missing:
        print("Workflows missing README badges:", file=sys.stderr)
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        print(f"{len(missing)} missing badge(s)", file=sys.stderr)
        return 1
    print(f"Badges OK: {len(workflows)} workflows linked from README")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
