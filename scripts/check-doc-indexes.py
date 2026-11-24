#!/usr/bin/env python3
"""Fail when an internal doc is not reachable from its folder's index.

This prevents the 'forgotten file' class of drift: every document under docs/
must be named by the appropriate index so a contributor (or an AI) can find it.
The published website sidebar is checked separately by check-all.sh.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = {
    "docs/revival/README.md": "docs/revival",
    "docs/clamui-fork/README.md": "docs/clamui-fork",
    "docs/translations/README.md": "docs/translations",
}


def main() -> int:
    failures: list[str] = []
    for index_rel, folder in RULES.items():
        index = ROOT / index_rel
        if not index.exists():
            failures.append(f"missing index: {index_rel}")
            continue
        text = index.read_text(encoding="utf-8", errors="replace")
        for doc in sorted((ROOT / folder).glob("*.md")):
            if doc == index:
                continue
            if doc.name not in text:
                failures.append(f"{doc.relative_to(ROOT)} is not linked from {index_rel}")

    root_readme = (ROOT / "docs/README.md").read_text(encoding="utf-8", errors="replace")
    for index_rel in RULES:
        name = Path(index_rel).parent.name
        if name not in root_readme:
            failures.append(f"docs/{name}/ is not linked from docs/README.md")
    if "DESIGN.md" not in root_readme and "documentation/" not in root_readme:
        failures.append("design/documentation docs are not linked from docs/README.md")

    if failures:
        print("Doc index failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} doc index failure(s)", file=sys.stderr)
        return 1
    print("Doc indexes OK: every internal document is reachable from an index")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
