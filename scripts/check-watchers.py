#!/usr/bin/env python3
"""Fail when a scheduled workflow is missing from the watchers index."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs/documentation/WATCHERS.md"


def main() -> int:
    index = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    failures: list[str] = []
    workflows = []
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "schedule:" not in text:
            continue
        workflows.append(path.name)
        if path.name not in index:
            failures.append(f"scheduled workflow not indexed: {path.name}")
    for line in index.splitlines():
        if line.startswith("| `") and ".yml`" in line:
            name = line.split("`")[1]
            path = ROOT / ".github/workflows" / name
            if not path.exists():
                failures.append(f"indexed watcher does not exist: {name}")
            elif "schedule:" not in path.read_text(encoding="utf-8", errors="replace"):
                failures.append(f"indexed watcher has no schedule: {name}")
    if failures:
        print("Watcher index failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"Watchers OK: {len(workflows)} scheduled workflows indexed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
