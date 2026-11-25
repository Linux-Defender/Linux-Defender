#!/usr/bin/env python3
"""Verify Sway/wlroots integration is wired without claiming desktop validation."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []
    tray = read("desktop/src-tauri/src/tray.rs")
    if not tray or "ksni" not in tray.lower():
        failures.append("Rust SNI tray implementation is missing from the Tauri runtime")
    if re.search(r"python|libdbusmenu", tray, re.I):
        failures.append("tray implementation reintroduced a Python/libdbusmenu dependency")

    pkg = read("aur/PKGBUILD")
    for token in ("waybar", "sway", "xdg-desktop-portal-wlr"):
        if token not in pkg:
            failures.append(f"AUR recipe has no Sway/wlroots optdepend for {token}")

    install_doc = read("website/src/content/docs/docs/installation.md")
    tray_doc = read("website/src/content/docs/docs/guides/tray.md")
    for token in ("Sway", "xdg-desktop-portal-wlr"):
        if token not in install_doc or token not in tray_doc:
            failures.append(f"{token} is not documented in installation/tray guides")
    if "validate-sway.sh" not in tray_doc:
        failures.append("tray guide does not link the Sway validation helper")
    if not (ROOT / "scripts/validate-sway.sh").exists():
        failures.append("Sway validation helper is missing")

    if failures:
        print("Sway integration failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} Sway failure(s)", file=sys.stderr)
        return 1
    print("Sway integration OK: Rust SNI, AUR optdepends, docs, and runtime helper wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
