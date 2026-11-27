#!/usr/bin/env python3
"""Fail when packaging stops shipping the MIT license or stages build-only keys.

Every format must include the project LICENSE in its package; the signing key
is a build-time input compiled into the binary and must never be shipped.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LICENSE_FILES = (
    "debian/build-deb.sh",
    "debian/build-privileged-helper-deb.sh",
    "rpm/linux-defender-privileged-helper.spec",
    "rpm/build-privileged-helper-rpm.sh",
    "appimage/build-appimage.sh",
    "flathub/io.github.linuxdefender.linuxdefender.yml",
    "flathub/io.github.linuxdefender.linuxdefender.local.yml",
    "snap/snapcraft.yaml",
    "aur/PKGBUILD",
    "aur/linux-defender-privileged-helper/PKGBUILD",
)


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    failures: list[str] = []
    for rel in LICENSE_FILES:
        text = read(rel)
        if "LICENSE" not in text:
            failures.append(f"{rel}: project LICENSE is not staged")
    for rel in LICENSE_FILES:
        if "signing-key.asc" in read(rel):
            failures.append(f"{rel}: build-only signing key is staged into a package")
    if "linux-defender-privileged-helper=0.6.0" not in read("aur/PKGBUILD"):
        failures.append("aur/PKGBUILD: optional helper must be version-pinned")
    if failures:
        print("Packaging license failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Packaging license OK: all formats ship LICENSE; build keys are not staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
