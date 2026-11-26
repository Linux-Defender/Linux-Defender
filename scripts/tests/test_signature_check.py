#!/usr/bin/env python3
"""Regression tests for scripts/check-signatures.py host-ClamAV detection."""
from __future__ import annotations

import importlib.util
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-signatures.py"
spec = importlib.util.spec_from_file_location("check_signatures", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class SignatureCheckTests(unittest.TestCase):
    def test_missing_clamscan_skips_instead_of_crashing(self):
        original = module.run

        def missing(*_args, **_kwargs):
            raise FileNotFoundError(2, "No such file or directory", "clamscan")

        module.run = missing
        try:
            self.assertEqual(module.main(), 0)
        finally:
            module.run = original

    def test_timeout_fails_closed(self):
        original = module.run

        def timed_out(*_args, **_kwargs):
            raise subprocess.TimeoutExpired("clamscan", 120)

        module.run = timed_out
        try:
            self.assertEqual(module.main(), 1)
        finally:
            module.run = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
