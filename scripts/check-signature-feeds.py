#!/usr/bin/env python3
"""Verify the product-default URLhaus ClamAV signature feed is reachable and valid.

Reads the Auth-Key from the core source (never from settings or logs), fetches
the .ndb export, and checks it has real ClamAV signature lines. The key is
redacted from every message and error. Network-enabled by design; run in the
weekly Signature Database workflow rather than in the commit hook.
"""
from __future__ import annotations

import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "crates/linux-defender-core/src/urlhaus.rs"
NDB_LINE = re.compile(r"^[^:]+:\d+:[^:]*:[0-9A-Fa-f*?]{4,}")
REDACTED = "***REDACTED***"


def load_key() -> tuple[str, str]:
    text = SOURCE.read_text(encoding="utf-8")
    prefix = re.search(r'URLHAUS_FEED_PREFIX:\s*&str\s*=\s*"([^"]+)"', text)
    suffix = re.search(r'URLHAUS_FEED_SUFFIX:\s*&str\s*=\s*"([^"]+)"', text)
    key = re.search(r'URLHAUS_DEFAULT_AUTH_KEY:\s*&str\s*=\s*"([^"]+)"', text)
    if not (prefix and suffix and key):
        raise RuntimeError("cannot read URLhaus feed constants from urlhaus.rs")
    return f"{prefix.group(1)}{key.group(1)}{suffix.group(1)}", key.group(1)


def main() -> int:
    try:
        url, key = load_key()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    def redact(message: str) -> str:
        return message.replace(key, REDACTED)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "linux-defender-signature-check"})
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read(256 * 1024).decode("utf-8", errors="replace")
            status = response.status
    except Exception as exc:
        print(f"FAIL: URLhaus feed request failed: {redact(str(exc))}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"FAIL: URLhaus feed returned HTTP {status}", file=sys.stderr)
        return 1

    lines = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")]
    signatures = [line for line in lines if NDB_LINE.match(line)]
    print(f"URLhaus feed: HTTP {status}, {len(signatures)} valid .ndb signature line(s)")
    if len(body) < 100 or len(signatures) < 1:
        snippet = redact(body[:200].replace("\n", " "))
        print(f"FAIL: feed is empty or not a ClamAV .ndb export: {snippet!r}", file=sys.stderr)
        return 1

    print("SIGNATURE FEEDS OK: product-default URLhaus export is reachable and valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
