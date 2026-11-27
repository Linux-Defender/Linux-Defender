#!/usr/bin/env python3
"""Fail when the checkout drifts from the documented release-safe repo state.

One branch (`main`) and no local tags. The clean-tree invariant is checked by
`audit-consistency.sh` at commit/push boundaries; this gate must also pass
while a contributor is still editing. `release-readiness.py` stays a manual,
human-gated tool.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    if git("branch", "--format=%(refname:short)").splitlines() != ["main"]:
        print("check-repo-state: expected exactly one local branch named main", file=sys.stderr)
        return 1
    tags = git("tag", "--list").splitlines()
    if tags:
        print(f"check-repo-state: local tags must be empty, found {tags}", file=sys.stderr)
        return 1
    print("Repo state OK: main only, no tags")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
