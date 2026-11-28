#!/usr/bin/env python3
"""Fail when a master document drops one of the six supported build formats.

A format mentioned as signed in SECURITY.md but absent from the installation
guide (or vice versa) makes the whole repository look inconsistent. This
checker keeps DEB, RPM, AppImage, Flatpak, Snap and AUR present in every
authoritative document and keeps their packaging directories/build workflows
wired, so a future edit cannot quietly half-document the matrix.
"""
from __future__ import annotations

import re

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMATS = ("deb", "rpm", "appimage", "flatpak", "snap", "aur")

MASTER_DOCS = (
    "AGENTS.md",
    "README.md",
    "SECURITY.md",
    "RELEASE_NOTES.md",
    "website/src/content/docs/docs/installation.md",
    "website/src/content/docs/docs/getting-started.md",
    "website/src/content/docs/docs/contributing/development.md",
    "website/src/content/docs/docs/contributing/security.md",
    "docs/clamui-fork/STATUS.md",
)

PACKAGING = {
    "deb": "debian/",
    "rpm": "rpm/",
    "appimage": "appimage/",
    "flatpak": "flathub/",
    "snap": "snap/",
    "aur": "aur/",
}


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for rel in MASTER_DOCS:
        path = root / rel
        if not path.exists():
            failures.append(f"master document {rel} is missing")
            continue
        text = path.read_text(encoding="utf-8")
        aliases = {"deb": ("DEB", "Debian"), "rpm": ("RPM",), "appimage": ("AppImage",),
                   "flatpak": ("Flatpak",), "snap": ("Snap",), "aur": ("AUR",)}
        missing = [
            fmt
            for fmt in FORMATS
            if not any(re.search(rf"\b{re.escape(alias)}s?\b", text, re.IGNORECASE)
                       for alias in aliases[fmt])
        ]
        if missing:
            failures.append(f"{rel} does not mention: {', '.join(missing)}")

    for fmt, directory in PACKAGING.items():
        if not (root / directory).is_dir():
            failures.append(f"packaging directory {directory} for {fmt} is missing")

    integration_docs = (
        "README.md",
        "website/src/content/docs/docs/troubleshooting.md",
    )
    for rel in integration_docs:
        path = root / rel
        if not path.exists():
            failures.append(f"integration note {rel} is missing")
            continue
        text = path.read_text(encoding="utf-8")
        if "Configure Integration" not in text:
            failures.append(f"{rel} lost the Configure Integration note")
            continue
        if "AppImage" not in text.split("Configure Integration", 1)[1][:600]:
            failures.append(f"{rel} integration note omits AppImage staging")

    release = root / "RELEASE_NOTES.md"
    if release.exists():
        text = release.read_text(encoding="utf-8").lower()
        for phrase in ("signed", "built and verified by ci", "source recipes"):
            if phrase not in text:
                failures.append(f"RELEASE_NOTES.md lost the {phrase!r} distribution distinction")

    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Format coverage failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Format coverage OK: all six formats documented and packaged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
