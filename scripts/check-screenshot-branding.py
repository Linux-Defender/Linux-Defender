#!/usr/bin/env python3
"""Fail when a shipped screenshot changes without a branding review.

Every image in `screenshots/` is a rendering of the current Linux Defender UI,
not upstream ClamUI material. A SHA-256 manifest makes any pixel change fail
the static gate until someone reviews it and refreshes the manifest. When
Tesseract is available the checker also OCRs each PNG and rejects the old
`ClamUI` / `Dashboard` branding outright.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/screenshot-manifest.json"
IMAGE_DIR = ROOT / "screenshots"
FORBIDDEN = ("clamui", "linx systems", "dashboard")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    manifest_path = root / "scripts/screenshot-manifest.json"
    image_dir = root / "screenshots"
    if not manifest_path.exists():
        return ["scripts/screenshot-manifest.json is missing"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected: dict[str, str] = manifest.get("images", {})
    images = sorted(p for p in image_dir.glob("*.png"))

    for path in images:
        rel = f"screenshots/{path.name}"
        if rel not in expected:
            failures.append(f"{rel} is not in the reviewed screenshot manifest")
        elif digest(path) != expected[rel]:
            failures.append(f"{rel} changed; review the branding and refresh the manifest")

    for rel in expected:
        if not (root / rel).exists():
            failures.append(f"manifest lists missing screenshot {rel}")

    if shutil.which("tesseract"):
        for path in images:
            try:
                text = subprocess.run(
                    ["tesseract", str(path), "stdout"], capture_output=True, text=True, check=True
                ).stdout.lower()
            except subprocess.CalledProcessError:
                failures.append(f"Tesseract could not read {path}")
                continue
            for word in FORBIDDEN:
                if word in text:
                    failures.append(f"{path.name} still shows stale branding ({word})")

    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Screenshot branding failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(f"Screenshot branding OK: {len(list((ROOT / 'screenshots').glob('*.png')))} reviewed images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
