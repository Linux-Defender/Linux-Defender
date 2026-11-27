#!/usr/bin/env python3
"""Fail when install/download/build guidance drifts across distributions/formats.

Covers the README, installation guide, development guide, daemon guide, and all
six packaging READMEs. Every supported family/format must be described, and no
format may claim to bundle the host ClamAV engine or database.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    failures: list[str] = []
    readme = read("README.md")
    install = read("website/src/content/docs/docs/installation.md")
    dev = read("website/src/content/docs/docs/contributing/development.md")
    daemons = read("website/src/content/docs/docs/reference/scan-backends.md")

    # Host ClamAV install commands for every documented family.
    for label, command in (
        ("Debian/Ubuntu", "sudo apt install clamav clamav-freshclam"),
        ("Arch/CachyOS", "sudo pacman -S --needed clamav"),
        ("Fedora", "sudo dnf install clamav clamav-freshclam"),
        ("Fedora Atomic", "sudo rpm-ostree install clamav clamav-freshclam"),
        ("openSUSE", "sudo zypper install clamav"),
    ):
        if command not in readme:
            failures.append(f"README.md misses host ClamAV command for {label}")

    # Install guide: release status + compatibility table cover every format.
    for token in ("Snap", "AUR", "Flatpak", "AppImage", "DEB", "RPM"):
        if token not in install:
            failures.append(f"installation.md omits {token} from release status")
    for row in ("CachyOS / Arch", "Debian / Ubuntu", "Fedora", "Fedora Atomic",
                "openSUSE Tumbleweed/Leap", "AUR (Arch derivatives)", "Snap",
                "Flatpak", "AppImage"):
        if f"| {row} |" not in install:
            failures.append(f"installation.md compatibility table misses {row}")

    # Daemon commands: all five families.
    for command in (
        "sudo systemctl enable --now clamav-daemon",
        "sudo systemctl enable --now clamd@scan",
        "sudo systemctl enable --now clamd",
    ):
        if command not in daemons:
            failures.append(f"scan-backends.md misses daemon command {command}")

    # Development prerequisites for all build families.
    for section in ("### Debian or Ubuntu", "### Fedora", "### Fedora Atomic", "### openSUSE"):
        if section not in dev:
            failures.append(f"development.md misses prerequisites section {section}")
    if "webkit2gtk4.1-devel" not in dev or "webkit2gtk3-devel" not in dev:
        failures.append("development.md misses WebKitGTK 4.1 prerequisite commands")

    # Every format README must state the host-ClamAV boundary.
    for rel in (
        "debian/README.md", "rpm/README.md", "appimage/README.md",
        "flathub/README.md", "snap/README.md", "aur/README.md",
    ):
        text = read(rel)
        if "ClamAV" not in text or not any(
            word in text.lower() for word in ("bundle", "host clamav", "host tools")
        ):
            failures.append(f"{rel} misses the host-ClamAV/no-bundling boundary")

    # snap README must not claim system libraries or a strict host boundary.
    snap = read("snap/README.md")
    for stale in ("uses the system", "through the snap boundary"):
        if stale in snap:
            failures.append(f"snap/README.md retains stale claim: {stale}")

    if failures:
        print("Install guidance failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(f"{len(failures)} install guidance failure(s)", file=sys.stderr)
        return 1
    print("Install guidance OK: all distros and formats documented consistently")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
