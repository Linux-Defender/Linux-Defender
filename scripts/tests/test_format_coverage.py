"""Fail-closed tests for the six-format documentation guard."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "check_format_coverage", ROOT / "scripts/check-format-coverage.py"
)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class FormatCoverageTests(unittest.TestCase):
    def test_real_repository_passes(self) -> None:
        self.assertEqual(guard.check(), [])

    def test_missing_format_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ld-format-") as tmp:
            root = Path(tmp)
            for rel in guard.MASTER_DOCS:
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("all six: deb rpm appimage flatpak snap aur\n")
            for directory in guard.PACKAGING.values():
                (root / directory).mkdir(parents=True, exist_ok=True)
            (root / "RELEASE_NOTES.md").write_text(
                "deb rpm appimage flatpak snap aur; signed; built and verified by CI; source recipes\n"
            )
            self.assertEqual(guard.check(root), [])
            security = root / "SECURITY.md"
            security.write_text(security.read_text().replace("snap", ""))
            failures = guard.check(root)
            self.assertTrue(any("SECURITY.md does not mention: snap" in f for f in failures))


if __name__ == "__main__":
    unittest.main()
