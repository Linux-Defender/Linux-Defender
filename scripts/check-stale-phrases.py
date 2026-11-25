#!/usr/bin/env python3
"""Fail when known-stale claims resurface in live documentation.

These phrases were true in older snapshots but are now wrong: they contradict
the shipped translations, compatibility contracts, or the reviewed project set.
This is a small, explicit denylist for regressions the link/file checkers
cannot detect. Add a pattern here whenever a stale statement is corrected.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "node_modules", "target", "dist", ".astro", "vendor", "__pycache__"}

STALE = {
    "Lensorreview": "misspelled/nonexistent project name in parity docs",
    "de done, others English fallback": "all 10 catalogs are now maintained",
    "ClamUI was deprecated upstream": "upstream status claim is no longer made",
    "Dashboard.tsx`, `ScanOverview.tsx`, new modules": "superseded pages were removed",
    "docs/clamui-fork/REPOS.md": "inventory moved to docs/revival/UPSTREAM-REPOSITORIES.md",
    "update-pot.sh --check fails": "POT is current and all checks pass",
    "32 missing in all 10": "all catalogs contain every source message",
    "Blocked on: translations of those 32": "historical gap is closed",
    "all 23 workflows": "workflow count grew; use non-numeric wording",
    "all 60 tracked documents": "doc map count grew; use non-numeric wording",
    "261 external URLs": "link count grew; use non-numeric wording",
    "Four scheduled workflows": "more scheduled workflows were added",
}


def main() -> int:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    files = [ROOT / p for p in out.stdout.splitlines()
             if p.endswith((".md", ".mdx")) and not any(part in SKIP_PARTS for part in Path(p).parts)]
    hits: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for phrase, reason in STALE.items():
            if phrase in text:
                hits.append(f"{path.relative_to(ROOT)}: {phrase!r} ({reason})")
    # The ledger records the history of these fixes, not the stale wording
    # itself; it is excluded explicitly so the record can describe the change.
    hits = [h for h in hits if not h.startswith("docs/revival/CHAT-AND-PROJECT-AUDIT.md")]
    if hits:
        print("Stale documentation phrases:", file=sys.stderr)
        for hit in hits:
            print(f"  {hit}", file=sys.stderr)
        print(f"{len(hits)} stale phrase(s)", file=sys.stderr)
        return 1
    print(f"Stale phrases OK: {len(STALE)} known-bad claims absent from {len(files)} docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
