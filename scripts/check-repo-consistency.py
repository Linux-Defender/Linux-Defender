#!/usr/bin/env python3
"""Fail when repo-wide declarations drift: versions, identity, or inventories.

Checks that the application version agrees across the workspace manifest, the
Tauri crate, the desktop package, AppStream metadata, the Flatpak release notes,
and both AUR PKGBUILDs; that every package format uses the public app id; and
that every workflow and maintenance script is referenced somewhere so none is
forgotten.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ID = "io.github.linuxdefender.linuxdefender"


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def match(pattern: str, text: str, label: str, failures: list[str]) -> str:
    found = re.search(pattern, text, re.M)
    if not found:
        failures.append(f"cannot read {label}")
        return ""
    return found.group(1)


def tracked_texts() -> dict[str, str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    texts: dict[str, str] = {}
    for rel in out.stdout.splitlines():
        p = ROOT / rel
        if not p.is_file():
            continue
        try:
            texts[rel] = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            texts[rel] = ""
    return texts


def main() -> int:
    failures: list[str] = []

    # Version agreement across production layers (the website has its own
    # independent site version and is intentionally excluded).
    versions = {
        "workspace Cargo.toml": match(r'^version\s*=\s*"([^"]+)"', read("Cargo.toml"), "workspace version", failures),
        "Tauri Cargo.toml": match(r'^version\s*=\s*"([^"]+)"', read("desktop/src-tauri/Cargo.toml"), "Tauri version", failures),
        "desktop package.json": match(r'"version"\s*:\s*"([^"]+)"', read("desktop/package.json"), "desktop version", failures),
        "AppStream release": match(r'<release\s+version="([^"]+)"', read(f"data/{APP_ID}.metainfo.xml"), "AppStream release", failures),
        "Flatpak release notes": match(r"^# Linux Defender ([0-9.]+) release description", read("flathub/RELEASE_NOTES.md"), "Flatpak release notes", failures),
        "AUR app": match(r"^pkgver=([0-9.]+)$", read("aur/PKGBUILD"), "AUR app version", failures),
        "AUR helper": match(r"^pkgver=([0-9.]+)$", read("aur/linux-defender-privileged-helper/PKGBUILD"), "AUR helper version", failures),
    }
    distinct = {v for v in versions.values() if v}
    if len(distinct) > 1:
        failures.append(f"version mismatch across layers: {versions}")

    # Public app identity in every package format.
    identity_files = [
        f"data/{APP_ID}.desktop",
        f"data/{APP_ID}.metainfo.xml",
        f"flathub/{APP_ID}.yml",
        f"flathub/{APP_ID}.local.yml",
    ]
    for rel in identity_files:
        if APP_ID not in read(rel):
            failures.append(f"public app id missing or wrong in {rel}")
    tauri_conf = read("desktop/src-tauri/tauri.conf.json")
    if '"identifier"' not in tauri_conf or APP_ID not in tauri_conf:
        failures.append("Tauri bundle identifier does not match the public app id")

    texts = tracked_texts()
    corpus = "\n".join(texts.values())

    # Every workflow must be discoverable by filename or by its `name:` value.
    for p in sorted((ROOT / ".github/workflows").glob("*.yml")):
        rel = p.relative_to(ROOT).as_posix()
        name_match = re.search(r"^name:\s*(.+)$", p.read_text(encoding="utf-8"), re.M)
        names = {p.name}
        if name_match:
            names.add(name_match.group(1).strip().strip("\"'"))
        if not any(n in corpus for n in names):
            failures.append(f"workflow not referenced in docs or tooling: {rel}")

    # Every maintenance script must be referenced by a doc, workflow, or manifest.
    for p in sorted((ROOT / "scripts").glob("*")):
        if not p.is_file() or p.suffix not in {".sh", ".py", ".ts"}:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if p.name not in corpus:
            failures.append(f"maintenance script not referenced anywhere: {rel}")

    if failures:
        print("Repository consistency failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} repository consistency failure(s)", file=sys.stderr)
        return 1
    print(f"Repository consistency OK: version {versions['workspace Cargo.toml']}, "
          f"id {APP_ID}, workflows and scripts all referenced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
