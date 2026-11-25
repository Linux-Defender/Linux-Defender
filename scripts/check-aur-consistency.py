#!/usr/bin/env python3
"""AUR-only convenience wrapper around the unified packaging checker.

Kept deliberately: the all-format checker is authoritative, but contributors
who touch only `aur/` can run this named entry point, and both are invoked by
check-all.sh. No rules are duplicated here — this delegates to the same code.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNIFIED = ROOT / "scripts/check-packaging-consistency.py"


def main() -> int:
    result = subprocess.run([sys.executable, str(UNIFIED)], cwd=ROOT)
    if result.returncode == 0:
        print("AUR consistency OK (delegated to unified packaging check)")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
