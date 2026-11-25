#!/usr/bin/env python3
"""Report when imported skills have drifted from the reviewed upstream content.

This is the auto-update detector for project skills: it fetches the current
upstream SKILL.md for each entry in skills-lock.json, hashes it, and compares to
the recorded `upstreamHash`. Drift is reported (not failed) so the weekly
Upstream Freshness workflow can open a review issue; never auto-merge unreviewed
upstream content into this MIT-licensed project.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "skills-lock.json"
PARITY_LOCK = ROOT / "parity-lock.json"


def fetch(url: str) -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"User-Agent": "linux-defender-freshness"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def default_branch(source: str) -> str:
    url = f"https://api.github.com/repos/{source}"
    data = json.loads(fetch(url))
    branch = data.get("default_branch")
    if not isinstance(branch, str) or not branch:
        raise RuntimeError(f"no default_branch for {source}")
    return branch


def main() -> int:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))["skills"]
    drift: list[dict[str, str]] = []
    errors: list[str] = []
    for name, meta in sorted(lock.items()):
        expected = meta.get("upstreamHash")
        if not expected:
            continue
        try:
            branch = default_branch(meta["source"])
            url = (f"https://raw.githubusercontent.com/{meta['source']}/{branch}/"
                   f"{meta['skillPath']}")
            actual = hashlib.sha256(fetch(url).encode("utf-8")).hexdigest()
            if actual != expected:
                drift.append({
                    "skill": name,
                    "source": meta["source"],
                    "skillPath": meta["skillPath"],
                    "branch": branch,
                    "expected": expected,
                    "actual": actual,
                    "url": url,
                })
        except Exception as exc:  # network failures are reported, not fatal
            errors.append(f"{name}: {exc}")

    # Reviewed upstream parity snapshots. A moved head means the parity matrix
    # and STATUS need a fresh review; never auto-merge upstream code.
    if PARITY_LOCK.exists():
        parity = json.loads(PARITY_LOCK.read_text(encoding="utf-8"))["sources"]
        for name, meta in sorted(parity.items()):
            expected = meta.get("commit")
            if not expected:
                continue
            try:
                data = json.loads(fetch(f"https://api.github.com/repos/{meta['source']}/commits?per_page=1"))
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

    report = {"drift": drift, "errors": errors}
    print(json.dumps(report, indent=2))
    if drift or errors:
        print(f"\n{len(drift)} reviewed upstream reference(s) drifted, {len(errors)} fetch error(s). "
              "Review before refreshing skills-lock.json, parity-lock.json, or the imported payloads.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
