#!/usr/bin/env python3
"""Fail when a tracked script is not listed in docs/documentation/SCRIPTS.md."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs/documentation/SCRIPTS.md"


def main() -> int:
    out = subprocess.run(["git", "ls-files", "scripts/"], cwd=ROOT,
                         capture_output=True, text=True, check=True)
    files = [rel for rel in out.stdout.splitlines()
             if Path(rel).suffix in {".py", ".sh", ".ts"}]
    text = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
    missing = [rel for rel in files
               if Path(rel).name not in text and Path(rel).stem not in text]
    if missing:
        print("Scripts missing from docs/documentation/SCRIPTS.md:", file=sys.stderr)
        for rel in missing:
            print(f"  {rel}", file=sys.stderr)
        print(f"{len(missing)} unlisted script(s)", file=sys.stderr)
        return 1
    print(f"Scripts index OK: {len(files)} tracked scripts listed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
