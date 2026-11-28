"""Fail-closed tests for the YARA boundary guard."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_yara", ROOT / "scripts/check-yara-boundary.py")
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class YaraBoundaryTests(unittest.TestCase):
    def test_real_repository_passes(self) -> None:
        self.assertEqual(guard.check(), [])

    def test_bundled_rule_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "rules.yar").write_text("rule x { condition: true }")
            failures = guard.check(root)
            self.assertTrue(any("must not be bundled" in f for f in failures))

    def test_missing_bound_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            core = root / "crates/linux-defender-core/src"
            core.mkdir(parents=True)
            (core / "settings.rs").write_text('"yara_rules_directory": ""\n')
            (core / "scanner.rs").write_text("MAX_LOCAL_YARA_FILES MAX_LOCAL_YARA_FILE_BYTES MAX_LOCAL_YARA_TOTAL_BYTES\n")
            for rel in (
                "website/src/content/docs/docs/reference/scan-backends.md",
                "website/src/content/docs/docs/guides/settings.md",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ClamAV subset and host database are required.\n")
            desktop = root / "desktop/src"
            desktop.mkdir(parents=True, exist_ok=True)
            (desktop / "suggestedYara.ts").write_text(
                "SUGGESTED_YARA_SOURCES; nothing is downloaded or enabled automatically\n"
            )
            (root / "scripts").mkdir()
            (root / "scripts/cross-layer-contracts.json").write_text('{"id": "yara"}')
            self.assertEqual(guard.check(root), [])
            (core / "scanner.rs").write_text("no bounds\n")
            failures = guard.check(root)
            self.assertTrue(any("MAX_LOCAL_YARA_FILES" in f for f in failures))


if __name__ == "__main__":
    unittest.main()
