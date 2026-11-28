"""Fail-closed tests for the workspace release profile guard."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_release_profile", ROOT / "scripts/check-release-profile.py"
)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class ReleaseProfileTests(unittest.TestCase):
    def fixture(self, text: str) -> Path:
        tmp = tempfile.TemporaryDirectory(prefix="ld-release-profile-")
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "Cargo.toml").write_text(text, encoding="utf-8")
        return root

    def test_real_workspace_passes(self) -> None:
        self.assertEqual(guard.check(), [])

    def test_missing_section_fails_closed(self) -> None:
        root = self.fixture("[workspace]\nmembers = []\n")
        self.assertTrue(any("no [profile.release]" in f for f in guard.check(root)))

    def test_removed_panic_fails_closed(self) -> None:
        text = (ROOT / "Cargo.toml").read_text(encoding="utf-8").replace('panic = "abort"\n', "")
        root = self.fixture(text)
        self.assertTrue(any("lost panic" in f for f in guard.check(root)))

    def test_weakened_strip_fails_closed(self) -> None:
        text = (ROOT / "Cargo.toml").read_text(encoding="utf-8").replace("strip = true", "strip = false")
        root = self.fixture(text)
        self.assertTrue(any("strip=false" in f for f in guard.check(root)))


if __name__ == "__main__":
    unittest.main()
