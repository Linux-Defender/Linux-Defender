"""Guard the single regeneration entry point against losing a step."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/update-all.sh"


class UpdateAllTests(unittest.TestCase):
    def test_regenerates_every_derived_artifact(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        for step in (
            "./scripts/update-pot.sh",
            "python3 scripts/merge-catalogs.py",
            "python3 scripts/generate-translation-review.py",
            "python3 scripts/generate-doc-map.py",
        ):
            self.assertIn(step, text)

    def test_full_mode_refreshes_packaging_pins(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--full", text)
        self.assertIn("scripts/generate-flatpak-sources.sh", text)
        self.assertIn("scripts/refresh-dependabot-sources.sh", text)

    def test_always_verifies_after_regeneration(self) -> None:
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("bash scripts/check-all.sh", text)
        self.assertIn("set -euo pipefail", text)


if __name__ == "__main__":
    unittest.main()
