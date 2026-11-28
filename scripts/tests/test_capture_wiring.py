"""Guard the documented run/capture paths for contributors and coding agents."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class CaptureWiringTests(unittest.TestCase):
    def test_both_capture_paths_exist_and_are_combined(self) -> None:
        for rel in (
            "scripts/capture-all.sh",
            "scripts/capture-app-window.sh",
            "scripts/capture-browser.mjs",
        ):
            self.assertTrue((ROOT / rel).exists(), rel)
        combined = read("scripts/capture-all.sh")
        self.assertIn("capture-app-window.sh", combined)
        self.assertIn("capture-browser.mjs", combined)

    def test_every_app_view_is_captured(self) -> None:
        script = read("scripts/capture-browser.mjs")
        for view in (
            "overview", "scan", "database", "logs", "components", "quarantine",
            "statistics", "audit", "network", "profiles", "results", "preferences",
        ):
            self.assertIn(f'"{view}"', script)

    def test_docs_show_the_run_flow_and_all_capture_commands(self) -> None:
        guide = read("website/src/content/docs/docs/contributing/development.md")
        for phrase in (
            "git pull --ff-only",
            "bun run tauri dev",
            "capture-all.sh",
            "capture-app-window.sh",
            "capture-browser.mjs",
        ):
            self.assertIn(phrase, guide)
        self.assertIn("DESIGN.md#ui-screenshots", guide)

    def test_scripts_index_and_design_guide_are_linked(self) -> None:
        index = read("docs/documentation/SCRIPTS.md")
        for rel in (
            "scripts/capture-all.sh",
            "scripts/capture-app-window.sh",
            "scripts/capture-browser.mjs",
        ):
            self.assertIn(rel, index)
        self.assertIn("UI screenshots", read("docs/DESIGN.md"))


if __name__ == "__main__":
    unittest.main()
