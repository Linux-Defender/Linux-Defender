"""Negative tests for the declarative support-parity guard."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CHECKER = ROOT / "scripts" / "check-support-parity.py"


def run_checker(contracts: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=ROOT,
        env={"SUPPORT_PARITY_CONTRACTS": str(contracts)},
        capture_output=True,
        text=True,
    )


class SupportParityTests(unittest.TestCase):
    def test_real_contracts_pass(self):
        result = run_checker(ROOT / "scripts" / "support-parity-contracts.json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_pattern_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contracts.json"
            path.write_text(json.dumps({"rules": [{
                "name": "negative-missing",
                "files": ["crates/linux-defender-core/src/urlscan.rs"],
                "patterns": ["THIS_PATTERN_MUST_NEVER_EXIST"],
            }]}))
            result = run_checker(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("negative-missing", result.stderr)

    def test_forbidden_pattern_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "contracts.json"
            path.write_text(json.dumps({"rules": [{
                "name": "negative-forbidden",
                "files": ["crates/linux-defender-core/src/urlscan.rs"],
                "patterns": ["pub fn validate_url"],
                "forbidden": ["Policy::none()"],
            }]}))
            result = run_checker(path)
            self.assertEqual(result.returncode, 1)
            self.assertIn("forbidden", result.stderr)


if __name__ == "__main__":
    unittest.main()
