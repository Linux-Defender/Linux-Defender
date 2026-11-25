#!/usr/bin/env python3
"""Fail when a file that must be executable is not tracked as mode 100755.

Git records the executable bit, but an editor or archive extraction can drop
it silently: the file still looks right in a diff and every text checker
passes, then installation or a direct invocation fails at runtime. These are
the two contracts that must never drift:

  * a tracked ``*.sh`` with a shebang is run directly (hooks, helpers, package
    scripts, file-manager actions), so it must be ``100755``; and
  * every Debian maintainer script under ``debian/DEBIAN/`` must be
    executable, because ``dpkg`` runs it directly (``control`` files must not).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAINTAINER_DIR = "debian/DEBIAN/"
NON_SCRIPT_PREFIXES = ("control",)


def staged_modes(patterns: list[str]) -> dict[str, str]:
    result = subprocess.run(
        ["git", "ls-files", "-s", "--", *patterns],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    modes: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line:
            continue
        meta, path = line.split("\t", 1)
        modes[path] = meta.split()[0]
    return modes


def main() -> int:
    failures: list[str] = []

    for path, mode in sorted(staged_modes(["*.sh"]).items()):
        if mode == "100755":
            continue
        try:
            first = (ROOT / path).open("rb").read(2)
        except OSError as error:
            failures.append(f"{path} could not be read ({error})")
            continue
        if first == b"#!":
            failures.append(f"{path} has a shebang but is tracked as {mode} (expected 100755)")

    for path, mode in sorted(staged_modes([f"{MAINTAINER_DIR}*"]).items()):
        name = Path(path).name
        if name.startswith(NON_SCRIPT_PREFIXES):
            if mode == "100755":
                failures.append(f"{path} is a control file but is tracked as executable")
            continue
        if mode != "100755":
            failures.append(f"{path} is a maintainer script tracked as {mode} (expected 100755)")

    if failures:
        print("File mode failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print("Fix with: git update-index --chmod=+x <path>", file=sys.stderr)
        return 1

    print("File modes OK: shebang scripts and maintainer scripts are executable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
