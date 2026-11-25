#!/usr/bin/env python3
"""Verify every package ships the right launcher integration variant.

Flatpak needs `flatpak run ...` actions; native formats (DEB, RPM helper is
helper-only, AppImage, Snap, AUR) need `linux-defender ...` actions. All eight
actions must exist in both sets, and the older duplicate locations in `data/`
and `scripts/` must match the native set byte-for-byte.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLATPAK = ROOT / "crates/linux-defender-core/assets/integrations"
NATIVE = ROOT / "assets/integrations-native"
ASSETS = sorted(p.name for p in FLATPAK.glob("*") if p.is_file())
LAUNCHERS = [name for name in ASSETS if not name.endswith(".sh")]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []
    if not ASSETS:
        print("FAIL: no Flatpak integration assets found", file=sys.stderr)
        return 1
    if sorted(p.name for p in NATIVE.glob("*") if p.is_file()) != ASSETS:
        failures.append("native integration set does not match the Flatpak asset names")

    for name in ASSETS:
        flatpak, native = FLATPAK / name, NATIVE / name
        if not native.exists():
            continue
        if name.endswith(".sh"):
            continue
        for label, path, expected in (("Flatpak", flatpak, "flatpak run io.github.linuxdefender.linuxdefender"),
                                      ("native", native, "linux-defender")):
            text = read(path)
            if f"Exec={expected}" not in text:
                failures.append(f"{label} {name} has the wrong launcher command")
    for name in LAUNCHERS:
        if "flatpak run" in read(NATIVE / name):
            failures.append(f"native {name} still contains a Flatpak launcher")
        if name in {"io.github.linuxdefender.linuxdefender.nemo_action",
                    "io.github.linuxdefender.linuxdefender.service.desktop",
                    "io.github.linuxdefender.linuxdefender-virustotal.nemo_action",
                    "io.github.linuxdefender.linuxdefender-virustotal.desktop"}:
            if (ROOT / "data" / name).read_bytes() != (NATIVE / name).read_bytes():
                failures.append(f"data/{name} is out of sync with the native integration set")
    for name in ("linux-defender-scan-nautilus.sh", "linux-defender-virustotal-nautilus.sh"):
        if (ROOT / "scripts" / name).read_bytes() != (NATIVE / name).read_bytes():
            failures.append(f"scripts/{name} is out of sync with the native integration set")

    sources = {
        "Flatpak": ("flathub/io.github.linuxdefender.linuxdefender.yml",
                    "crates/linux-defender-core/assets/integrations"),
        "AppImage": ("appimage/build-appimage.sh", "assets/integrations-native"),
        "DEB": ("debian/build-deb.sh", "assets/integrations-native"),
        "Snap": ("snap/snapcraft.yaml", "assets/integrations-native"),
        "AUR": ("aur/PKGBUILD", "assets/integrations-native"),
    }
    for label, (rel, expected) in sources.items():
        if expected not in read(ROOT / rel):
            failures.append(f"{label} does not stage {expected}")

    platform = read(ROOT / "crates/linux-defender-core/src/platform.rs")
    if "../assets/integrations/" not in platform:
        failures.append("Rust platform.rs no longer embeds the Flatpak integration set")
    if "thunar" not in platform:
        failures.append("Rust platform.rs lost Thunar integration support")

    if failures:
        print("Integration parity failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} integration failure(s)", file=sys.stderr)
        return 1
    print(f"Integration parity OK: {len(ASSETS)} assets per variant, correctly staged by every format")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
