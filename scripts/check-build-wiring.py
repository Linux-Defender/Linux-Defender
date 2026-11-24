#!/usr/bin/env python3
"""Fail when the documented dev/build path is no longer wired to its inputs.

Checks the command contributors actually run (`bun run --cwd desktop tauri dev`)
end to end: the Tauri dev command, Vite dev URL, frontend install/build, the
patched vendored glib crate, and the crate manifests referenced by the audit.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []

    # Tauri dev command must point at Vite and at the Tauri crate's binary.
    tauri_conf = read("desktop/src-tauri/tauri.conf.json")
    try:
        conf = json.loads(tauri_conf)
    except json.JSONDecodeError as exc:
        failures.append(f"invalid tauri.conf.json: {exc}")
        conf = {}
    build = conf.get("build", {})
    raw_before = build.get("beforeDevCommand", "")
    # Tauri accepts either a string or { script, cwd }.
    before = raw_before.get("script", "") if isinstance(raw_before, dict) else str(raw_before)
    dev_url = build.get("devUrl", "")
    frontend = build.get("frontendDist", "")
    # `bun run --cwd desktop dev` resolves through desktop/package.json, where
    # the `dev` script is Vite; accept that form as well as a direct vite call.
    if not ("vite" in str(before) or re.search(r"--cwd\s+desktop\s+dev\b", str(before))):
        failures.append(f"beforeDevCommand does not run the desktop Vite dev server: {before!r}")
    if "127.0.0.1" not in str(dev_url) or "1420" not in str(dev_url):
        failures.append(f"devUrl must be the pinned 127.0.0.1:1420 dev server: {dev_url!r}")
    if "dist" not in str(frontend):
        failures.append(f"frontendDist must embed the built frontend: {frontend!r}")
    vite = read("desktop/vite.config.ts")
    if "1420" not in vite or "strictPort" not in vite:
        failures.append("desktop/vite.config.ts must pin port 1420 with strictPort")

    # The dev/build command must have all of its frontend inputs installable.
    pkg = json.loads(read("desktop/package.json") or "{}")
    scripts = pkg.get("scripts", {})
    for script in ("dev", "check", "build", "tauri"):
        if script not in scripts:
            failures.append(f"desktop/package.json missing script: {script}")
    if not (ROOT / "desktop/bun.lock").exists():
        failures.append("desktop/bun.lock missing (frozen install cannot run)")

    # Vendored glib security patch must be wired via [patch.crates-io].
    cargo = read("Cargo.toml")
    if "[patch.crates-io]" not in cargo:
        failures.append("Cargo.toml has no [patch.crates-io] section")
    if 'glib = { path = "vendor/glib-0.18.5" }' not in cargo:
        failures.append("vendored glib 0.18.5 patch is not wired in Cargo.toml")
    vendored = ROOT / "vendor/glib-0.18.5"
    if not (vendored / "Cargo.toml").is_file():
        failures.append("vendor/glib-0.18.5/Cargo.toml is missing")
    source = (vendored / "src/collections/ptr_slice.rs").read_text(errors="replace") if (vendored / "src/collections/ptr_slice.rs").exists() else ""
    if "ptr::read" not in source:
        failures.append("vendored glib PtrSlice soundness fix (ptr::read) is missing")

    # Lockfile must still contain the patched glib and every workspace crate.
    lock = read("Cargo.lock")
    if 'name = "glib"' not in lock or 'version = "0.18.5"' not in lock:
        failures.append("Cargo.lock does not resolve glib 0.18.5")
    for crate in ("linux-defender-core", "linux-defender"):
        if f'name = "{crate}"' not in lock:
            failures.append(f"Cargo.lock missing workspace crate: {crate}")

    if failures:
        print("Build wiring failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} build wiring failure(s)", file=sys.stderr)
        return 1
    print("Build wiring OK: tauri dev -> Vite 1420 -> frontend dist; vendored glib patch present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
