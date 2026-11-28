#!/usr/bin/env python3
"""Fail when size-conscious release profile settings are removed or weakened.

Every package format (DEB, RPM, AppImage, Flatpak, Snap, AUR) builds from the
workspace release profile. Without these settings the shipped binaries grow
substantially and the contributor guide's release-build contract is silently
broken, so the settings are guarded in the same static gate as the rest.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = {
    "lto": {"thin", "true", "fat"},
    "codegen-units": {"1"},
    "opt-level": {"s", "z", "3"},
    "panic": {"abort"},
    "strip": {"true", '"symbols"'},
}


def profile_body(root: Path) -> str | None:
    manifest = root / "Cargo.toml"
    if not manifest.exists():
        return None
    lines = manifest.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "[profile.release]":
            continue
        body: list[str] = []
        for following in lines[index + 1 :]:
            if following.lstrip().startswith("["):
                break
            body.append(following.strip())
        return "\n".join(body)
    return None


def check(root: Path = ROOT) -> list[str]:
    body = profile_body(root)
    if body is None:
        return ["workspace Cargo.toml has no [profile.release] section"]

    failures: list[str] = []
    values: dict[str, str] = {}
    for line in body.splitlines():
        match = re.match(r"^([a-z-]+)\s*=\s*(.+)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"')

    for key, allowed in REQUIRED.items():
        value = values.get(key)
        if value is None:
            failures.append(f"release profile lost {key}")
        elif value not in allowed:
            failures.append(f"release profile {key}={value} is not a supported size setting")
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Release profile failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Release profile OK: lto, codegen-units, opt-level, panic, strip guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
