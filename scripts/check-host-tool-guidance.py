#!/usr/bin/env python3
"""Keep app and website host-ClamAV setup guidance identical and upstream-synced."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "desktop/src/pages/Components.tsx"
SITE = ROOT / "website/src/content/docs/docs/reference/scan-backends.md"
MATRIX = ROOT / "docs/revival/RELATED-PROJECT-REVIEW.md"
POT = ROOT / "po/linux-defender.pot"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []
    app, site = read(APP), read(SITE)
    for label in ("Ubuntu/Debian", "Fedora Workstation", "Fedora Atomic", "Arch Linux"):
        if label not in app:
            failures.append(f"app component guides miss {label}")
        if label not in site:
            failures.append(f"website daemon guide misses {label}")
    for command in (
        "sudo apt install clamav", "sudo dnf install clamav",
        "sudo rpm-ostree install clamav", "sudo pacman -S clamav",
        "sudo apt install clamav-freshclam", "sudo dnf install clamav-freshclam",
        "sudo rpm-ostree install clamav-freshclam",
        "sudo apt install clamav-daemon", "sudo dnf install clamd clamav-freshclam",
        "sudo systemctl enable --now clamav-daemon",
        "sudo systemctl enable --now clamd@scan",
        "sudo rpm-ostree install clamd clamav-freshclam",
        "clamdscan --config-file=/etc/clamd.d/scan.conf --ping 3",
    ):
        if command not in app:
            failures.append(f"app component guidance lost: {command}")
        if command not in site:
            failures.append(f"website daemon guidance lost: {command}")
    warning = "Setup instructions are copy-only. Linux Defender never installs packages or starts services for you."
    if warning not in app:
        failures.append("app lost the copy-only setup warning")
    if "copy-only" not in site:
        failures.append("website does not state that daemon commands are copy-only")
    if "Setup instructions are copy-only" in read(POT):
        pass  # extractor already covers the app literal
    else:
        failures.append("copy-only warning is missing from the POT")

    matrix = read(MATRIX)
    if "14362e804b65f44e9e4e777a1c13b98c36b1a926" not in matrix:
        failures.append("parity matrix does not record the reviewed upstream snapshot 14362e8")
    if "component guides" not in matrix:
        failures.append("parity matrix does not record the host-tool guide disposition")

    if failures:
        print("Host-tool guidance failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} guidance failure(s)", file=sys.stderr)
        return 1
    print("Host-tool guidance OK: app/site commands and upstream disposition aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
