"""Negative tests for the URL-list layout contract."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "scripts" / "check-url-list-layout.py"


class UrlListLayoutTests(unittest.TestCase):
    def test_real_contract_passes(self):
        result = subprocess.run([sys.executable, str(CHECKER)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_rule_fails_closed(self):
        css = (ROOT / "desktop/src/styles.css").read_text()
        tsx = (ROOT / "desktop/src/pages/ConfigPreferences.tsx").read_text()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "desktop/src/pages").mkdir(parents=True)
            (root / "desktop/src/styles.css").write_text(css.replace("grid-column: 1 / -1", ""))
            (root / "desktop/src/pages/ConfigPreferences.tsx").write_text(tsx)
            env = {
                "URL_LIST_CSS": str(root / "desktop/src/styles.css"),
                "URL_LIST_TSX": str(root / "desktop/src/pages/ConfigPreferences.tsx"),
            }
            result = subprocess.run([sys.executable, str(CHECKER)], cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("grid-column", result.stderr)


if __name__ == "__main__":
    unittest.main()
