#!/usr/bin/env python3
"""Report when a reviewed packaging reference has moved upstream.

Like the skill freshness checker, this never auto-merges: it prints JSON with
`drift` and `errors` so the weekly Packaging Sync workflow can open a review
issue. A changed upstream commit means the parity note and any adopted behavior
must be reviewed again, not blindly copied.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "packaging-lock.json"


def fetch(url: str) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "linux-defender-packaging-freshness",
               "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))["sources"]
    drift: list[dict[str, str]] = []
    errors: list[str] = []
    for name, meta in sorted(lock.items()):
        expected = meta.get("commit")
        if not expected:
            continue
        try:
            data = fetch(f"https://api.github.com/repos/{meta['source']}/commits?per_page=1")
            actual = data[0]["sha"]
            if actual != expected:
                drift.append({
                    "source": name,
                    "repository": meta["source"],
                    "reviewed": expected,
                    "current": actual,
                    "url": f"https://github.com/{meta['source']}/commits/{actual}",
                })
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")

    print(json.dumps({"drift": drift, "errors": errors}, indent=2))
    if drift or errors:
        print(f"\n{len(drift)} packaging reference(s) drifted, {len(errors)} fetch error(s). "
              "Review before updating packaging-lock.json or the AUR recipes.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
