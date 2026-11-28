"""Fail-closed tests for host-ClamAV upgrade guidance."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("check_clamav_upgrade", ROOT / "scripts/check-clamav-upgrade-guidance.py")
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class ClamavUpgradeTests(unittest.TestCase):
    def test_real_repository_passes(self) -> None:
        self.assertEqual(guard.check(), [])

    def test_missing_guidance_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "website/src/content/docs/docs"
            doc.mkdir(parents=True)
            (doc / "troubleshooting.md").write_text("## Still stuck?\n")
            failures = guard.check(root)
            self.assertTrue(any("engine" in f for f in failures))

    def test_detection_rate_claim_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "website/src/content/docs/docs"
            doc.mkdir(parents=True)
            text = (ROOT / "website/src/content/docs/docs/troubleshooting.md").read_text()
            text = text.replace("does **not** claim a higher malware detection rate", "claims a higher detection rate")
            (doc / "troubleshooting.md").write_text(text)
            failures = guard.check(root)
            self.assertTrue(any("higher detection rate" in f for f in failures))
