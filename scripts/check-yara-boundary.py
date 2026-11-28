#!/usr/bin/env python3
"""Guard the YARA boundary: no bundled rules, bounded user rules, accurate docs.

YARA rules are user-supplied and ClamAV implements only a subset of YARA. The
product must never bundle third-party rules or treat them as a replacement for
the host signature database, and a local rules directory must stay bounded so
it cannot turn a scan into an unbounded command line.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []

    result = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True
    )
    if result.returncode == 0:
        tracked = result.stdout.splitlines()
    else:
        tracked = [
            str(path.relative_to(root))
            for path in root.rglob("*")
            if path.is_file()
        ]
    bundled = [rel for rel in tracked if rel.lower().endswith((".yar", ".yara"))]
    if bundled:
        failures.append(f"YARA rules must not be bundled: {', '.join(bundled)}")

    settings = root / "crates/linux-defender-core/src/settings.rs"
    if not settings.exists() or '"yara_rules_directory": ""' not in settings.read_text(encoding="utf-8"):
        failures.append("no default YARA rules directory must be configured")

    scanner = root / "crates/linux-defender-core/src/scanner.rs"
    if scanner.exists():
        text = scanner.read_text(encoding="utf-8")
        for marker in ("MAX_LOCAL_YARA_FILES", "MAX_LOCAL_YARA_FILE_BYTES", "MAX_LOCAL_YARA_TOTAL_BYTES"):
            if marker not in text:
                failures.append(f"local YARA bound {marker} is missing")

    for rel in (
        "website/src/content/docs/docs/reference/scan-backends.md",
        "website/src/content/docs/docs/guides/settings.md",
    ):
        path = root / rel
        if not path.exists():
            failures.append(f"YARA documentation {rel} is missing")
            continue
        text = path.read_text(encoding="utf-8").lower()
        if "subset" not in text or "clamav" not in text:
            failures.append(f"{rel} must explain the ClamAV YARA subset")
        if "database" not in text:
            failures.append(f"{rel} must state YARA does not replace the host database")

    suggested = root / "desktop/src/suggestedYara.ts"
    if suggested.exists():
        text = suggested.read_text(encoding="utf-8")
        if "Nothing is downloaded or enabled automatically" not in text and "nothing is" not in text.lower():
            failures.append("suggested YARA sources must remain suggestion-only")
    else:
        failures.append("desktop/src/suggestedYara.ts is missing")

    contracts = root / "scripts/cross-layer-contracts.json"
    if not contracts.exists() or '"id": "yara"' not in contracts.read_text(encoding="utf-8"):
        failures.append("yara cross-layer contract is missing")

    return failures


def main() -> int:
    failures = check()
    if failures:
        print("YARA boundary failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("YARA boundary OK: no bundled rules, bounded user rules, accurate docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
