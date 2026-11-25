#!/usr/bin/env python3
"""Fail when tracked Markdown/MDX contains dead external HTTP(S) links.

Inline code spans and fenced code blocks are stripped first: placeholder URLs
such as `https://.../exports/<auth-key>/...` are documentation examples, not
links to visit. Imported skill payloads under `.agents/` are omitted because
they are upstream-owned and hash-locked. Transport errors are retried and then reported/skipped so offline checks work;
transient 5xx/429 outages are retried three times before being skipped, while
403/404/410 fail — a link to a challenge page or nowhere is not usable. Kept separate from check-all.sh because it performs network requests;
audit-consistency.sh and a weekly CI job run it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "node_modules", "target", "dist", ".astro", "vendor", "__pycache__", ".agents"}
URL_RE = re.compile(r"https?://[^\s)>\]]+")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)
WORKFLOW_URL_RE = re.compile(
    r"github\.com/[^/]+/[^/]+/actions/workflows/([A-Za-z0-9_.-]+\.yml)(?:/badge\.svg)?"
)
BLOB_URL_RE = re.compile(
    r"github\.com/[^/]+/[^/]+/blob/main/(.+?)(?:#.*)?$"
)


def tracked_docs() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [ROOT / p for p in out.stdout.splitlines()
            if p.endswith((".md", ".mdx")) and not any(part in SKIP_PARTS for part in Path(p).parts)]


def check(url: str) -> tuple[str, str, str]:
    req = urllib.request.Request(url, method="GET", headers={
        "User-Agent": "linux-defender-doc-link-check",
        "Range": "bytes=0-0",
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                return (url, "ok", str(resp.status))
        except urllib.error.HTTPError as exc:
            workflow = WORKFLOW_URL_RE.search(url)
            if exc.code == 404 and workflow and (ROOT / ".github/workflows" / workflow.group(1)).exists():
                return (url, "skip", "workflow exists locally; not yet published")
            blob = BLOB_URL_RE.search(url)
            if exc.code == 404 and blob and (ROOT / blob.group(1)).exists():
                return (url, "skip", "file exists locally; not yet published")
            if exc.code in {429, 500, 502, 503, 504}:
                if attempt < 2:
                    time.sleep(1 + attempt)  # transient upstream outage, retry
                    continue
                return (url, "skip", f"HTTP {exc.code} after 3 attempts (upstream outage)")
            return (url, "dead", str(exc.code))  # 403/404/410 are dead links
        except Exception as exc:
            if attempt < 2:
                time.sleep(1 + attempt)  # transient DNS/TLS/timeout, retry
                continue
            return (url, "skip", type(exc).__name__)
    return (url, "skip", "unknown")


def main() -> int:
    docs = tracked_docs()
    locations: dict[str, set[str]] = {}
    for doc in docs:
        text = CODE_RE.sub(" ", doc.read_text(encoding="utf-8", errors="replace"))
        for url in URL_RE.findall(text):
            url = url.rstrip(".,;:")
            locations.setdefault(url, set()).add(doc.relative_to(ROOT).as_posix())

    dead: list[str] = []
    skipped: list[str] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(check, url) for url in sorted(locations)]
        for future in as_completed(futures):
            url, status, detail = future.result()
            where = ", ".join(sorted(locations[url]))
            if status == "dead":
                dead.append(f"{url} -> HTTP {detail} ({where})")
            elif status == "skip":
                skipped.append(f"{url} -> {detail} ({where})")

    for item in sorted(skipped):
        print(f"SKIP (offline?): {item}", file=sys.stderr)
    if dead:
        print("Dead external links:", file=sys.stderr)
        for item in sorted(dead):
            print(f"  {item}", file=sys.stderr)
        print(f"{len(dead)} dead external link(s)", file=sys.stderr)
        return 1
    print(f"External links OK: {len(locations)} URL(s) checked in {len(docs)} docs, {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
