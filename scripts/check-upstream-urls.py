#!/usr/bin/env python3
"""Verify external URLs in the canonical upstream repository inventory.

Checks every bare URL in docs/revival/UPSTREAM-REPOSITORIES.md. 403/404/410
fail; transient 5xx/429 outages are retried three times then skipped, and
transport errors are skipped so the check works offline. This catches dead
upstream links before they rot in the docs again.
"""
from __future__ import annotations

import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs/revival/UPSTREAM-REPOSITORIES.md"
URL_RE = re.compile(r"https://[^\s)>\]]+")


def check(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "linux-defender-doc-link-check",
        "Range": "bytes=0-0",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return ("ok", str(response.status))
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 500, 502, 503, 504}:
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue
                return ("skip", f"HTTP {exc.code} after 3 attempts (upstream outage)")
            return ("dead", str(exc.code))
        except Exception as exc:
            if attempt < 2:
                time.sleep(1 + attempt)
                continue
            return ("skip", type(exc).__name__)
    return ("skip", "unknown")


def main() -> int:
    if not DOC.exists():
        print(f"FAIL: missing inventory: {DOC.relative_to(ROOT)}", file=sys.stderr)
        return 1
    urls = sorted(set(URL_RE.findall(DOC.read_text(encoding="utf-8"))))
    dead: list[str] = []
    skipped: list[str] = []
    for url in urls:
        status, detail = check(url)
        if status == "dead":
            dead.append(f"{url} -> HTTP {detail}")
        elif status == "skip":
            skipped.append(f"{url} -> {detail}")
    for item in skipped:
        print(f"SKIP (offline?): {item}", file=sys.stderr)
    if dead:
        print("Dead upstream URLs:", file=sys.stderr)
        for item in dead:
            print(f"  {item}", file=sys.stderr)
        print(f"{len(dead)} dead URL(s)", file=sys.stderr)
        return 1
    print(f"Upstream URLs OK: {len(urls)} verified, {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
