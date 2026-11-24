#!/usr/bin/env python3
"""Verify the Arch/AUR recipes stay wired, rebranded, and version-matched."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUR = ROOT / "aur"
APP = AUR / "PKGBUILD"
HELPER = AUR / "linux-defender-privileged-helper/PKGBUILD"
APP_ID = "io.github.linuxdefender.linuxdefender"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []
    app = read(APP)
    helper = read(HELPER)
    if not app or not helper:
        print("FAIL: AUR PKGBUILD files are missing", file=sys.stderr)
        return 1

    version = re.search(r'^version\s*=\s*"([^"]+)"', read(ROOT / "Cargo.toml"), re.M)
    if not version:
        failures.append("cannot read workspace version")
    else:
        for name, text in (("app", app), ("helper", helper)):
            found = re.search(r"^pkgver=([0-9.]+)$", text, re.M)
            if not found or found.group(1) != version.group(1):
                failures.append(f"{name} pkgver does not match workspace version")

    # Rebranding and host-boundary invariants.
    for name, text in (("app", app), ("helper", helper)):
        if re.search(r"clamui\.com|linx\.systems|linx_systems", text, re.I):
            failures.append(f"{name} PKGBUILD contains a stale upstream brand")
        if not re.search(r"^sha256sums=\('[0-9a-f]{64}'\)$", text, re.M):
            failures.append(f"{name} PKGBUILD has no pinned 64-hex tarball hash")
        if not re.search(r"^_commit=[0-9a-f]{40}$", text, re.M):
            failures.append(f"{name} PKGBUILD does not pin a source commit")
        if "/var/lib/clamav" in text or "clamav-db" in text:
            failures.append(f"{name} PKGBUILD bundles host signature data")

    if f"data/{APP_ID}.desktop" not in app and 'data/$_id.desktop' not in app:
        failures.append("app recipe does not install the rebranded desktop entry")
    if "waybar" not in app or "sway" not in app:
        failures.append("app recipe has no Sway/wlroots tray optdepends")
    if "linux-defender-scheduled-scan" not in app:
        failures.append("app recipe does not install the scheduled-scan CLI")
    if "linux-defender-apply-preferences" not in helper:
        failures.append("helper recipe does not install the canonical helper path")
    if f"data/{APP_ID}.policy" not in helper and 'data/$_id.policy' not in helper:
        failures.append("helper recipe does not install the rebranded polkit policy")

    for p in (APP, HELPER):
        result = subprocess.run(["bash", "-n", str(p)], cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"invalid PKGBUILD syntax: {p.relative_to(ROOT)}")

    # Generated .SRCINFO must match the recipes.
    if shutil.which("makepkg"):
        for p, srcinfo in ((APP, AUR / ".SRCINFO"), (HELPER, HELPER.parent / ".SRCINFO")):
            result = subprocess.run(
                ["makepkg", "--printsrcinfo"], cwd=p.parent, capture_output=True, text=True
            )
            if result.returncode != 0:
                failures.append(f"makepkg --printsrcinfo failed for {p.parent.relative_to(ROOT)}")
            elif read(srcinfo) != result.stdout:
                failures.append(f"stale .SRCINFO: {srcinfo.relative_to(ROOT)} (run makepkg --printsrcinfo)")

    install_doc = read(ROOT / "website/src/content/docs/docs/installation.md")
    tray_doc = read(ROOT / "website/src/content/docs/docs/guides/tray.md")
    if "aur/" not in install_doc or "AUR" not in install_doc:
        failures.append("installation guide does not describe the AUR recipes")
    if "Sway" not in install_doc or "Sway" not in tray_doc:
        failures.append("Sway support is not documented in installation/tray guides")

    if failures:
        print("AUR consistency failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} AUR failure(s)", file=sys.stderr)
        return 1
    print("AUR consistency OK: app/helper recipes rebranded, version-matched, Sway documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
