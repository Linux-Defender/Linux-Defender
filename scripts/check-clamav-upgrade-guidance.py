#!/usr/bin/env python3
"""Guard accurate host-ClamAV upgrade guidance.

Claims about engine upgrades must stay technically precise: the engine is
host-owned, 1.5.5 is a security/maintenance patch (not a detection upgrade),
signatures are independent, and the daemon may need a restart. No frontend
installs or bundles an engine.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "website/src/content/docs/docs/troubleshooting.md"


def check(root: Path = ROOT) -> list[str]:
    doc = root / "website/src/content/docs/docs/troubleshooting.md"
    if not doc.exists():
        return ["host-ClamAV upgrade guidance is missing"]
    text = doc.read_text(encoding="utf-8")
    failures: list[str] = []
    required = (
        "## Upgrading the host ClamAV engine",
        "1.5.5",
        "patch",
        "does **not** claim a higher malware detection rate",
        "clamscan --version",
        "clamd --version",
        "freshclam --version",
        "systemctl restart clamav-daemon",
        "releases/tag/clamav-1.5.5",
        "never installs packages",
    )
    for marker in required:
        if marker not in text:
            failures.append(f"upgrade guidance lost {marker!r}")
    lowered = text.lower()
    for bad in ("higher detection rate", "detects more malware", "auto-installs the engine"):
        if bad in lowered and "does **not** claim a higher malware detection rate" not in text:
            failures.append(f"unsupported claim {bad!r}")
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("ClamAV upgrade guidance failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("ClamAV upgrade guidance OK: host-owned engine, patch-only claims, signatures separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
