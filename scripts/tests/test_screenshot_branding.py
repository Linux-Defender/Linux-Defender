"""Fail-closed tests for the reviewed screenshot guard."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_screenshot_branding", ROOT / "scripts/check-screenshot-branding.py"
)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class ScreenshotBrandingTests(unittest.TestCase):
    def fixture(self) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="ld-screenshots-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "screenshots").mkdir()
        (root / "scripts").mkdir()
        for name in ("main_view.png", "audit_view.png"):
            (root / "screenshots" / name).write_bytes(b"fake png " + name.encode())
        manifest = {
            "images": {
                f"screenshots/{name}": guard.digest(root / "screenshots" / name)
                for name in ("main_view.png", "audit_view.png")
            }
        }
        (root / "scripts/screenshot-manifest.json").write_text(json.dumps(manifest))
        return root

    def test_real_repository_passes(self) -> None:
        self.assertEqual(guard.check(), [])

    def test_missing_manifest_fails_closed(self) -> None:
        root = self.fixture()
        (root / "scripts/screenshot-manifest.json").unlink()
        self.assertTrue(any("manifest" in f for f in guard.check(root)))

    def test_changed_image_fails_closed(self) -> None:
        root = self.fixture()
        (root / "screenshots/main_view.png").write_bytes(b"claude wrote this")
        failures = guard.check(root)
        self.assertTrue(any("main_view.png changed" in f for f in failures))

    def test_unlisted_image_fails_closed(self) -> None:
        root = self.fixture()
        (root / "screenshots/new_view.png").write_bytes(b"unreviewed")
        self.assertTrue(any("not in the reviewed" in f for f in guard.check(root)))


if __name__ == "__main__":
    unittest.main()
