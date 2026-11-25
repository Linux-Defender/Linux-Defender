#!/usr/bin/env python3
"""Regression tests for scripts/check-external-links.py link classification."""
from __future__ import annotations

import importlib.util
import io
import unittest
import urllib.error
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-external-links.py"
spec = importlib.util.spec_from_file_location("check_external_links", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ExternalLinkTests(unittest.TestCase):
    def test_transient_502_is_retried_and_then_ok(self):
        calls = []

        def fake_urlopen(_req, timeout=25):
            calls.append(timeout)
            if len(calls) < 3:
                raise urllib.error.HTTPError("u", 502, "Bad Gateway", {}, io.BytesIO(b""))
            return FakeResponse()

        original = module.urllib.request.urlopen
        original_sleep = module.time.sleep
        module.urllib.request.urlopen = fake_urlopen
        module.time.sleep = lambda _seconds: None
        try:
            status, detail = module.check("https://example.test/page")[1:]
            self.assertEqual((status, detail), ("ok", "200"))
            self.assertEqual(len(calls), 3)
        finally:
            module.urllib.request.urlopen = original
            module.time.sleep = original_sleep

    def test_unpublished_workflow_badge_is_skipped(self):
        def fake_urlopen(_req, timeout=25):
            raise urllib.error.HTTPError("u", 404, "Not Found", {}, io.BytesIO(b""))

        original = module.urllib.request.urlopen
        module.urllib.request.urlopen = fake_urlopen
        try:
            url = "https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-aur.yml/badge.svg"
            status, detail = module.check(url)[1:]
            self.assertEqual(status, "skip")
            self.assertIn("not yet published", detail)
        finally:
            module.urllib.request.urlopen = original

    def test_403_is_dead(self):
        def fake_urlopen(_req, timeout=25):
            raise urllib.error.HTTPError("u", 403, "Forbidden", {}, io.BytesIO(b""))

        original = module.urllib.request.urlopen
        module.urllib.request.urlopen = fake_urlopen
        try:
            status, detail = module.check("https://example.test/forbidden")[1:]
            self.assertEqual((status, detail), ("dead", "403"))
        finally:
            module.urllib.request.urlopen = original


if __name__ == "__main__":
    unittest.main(verbosity=2)
