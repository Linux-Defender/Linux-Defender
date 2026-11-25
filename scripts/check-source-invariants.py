#!/usr/bin/env python3
"""Fail when a hard-won behavior or security contract is silently reverted.

These are small, explicit source-level invariants that no generic linter can
see and that unit tests do not cover (the affected code is a React effect or a
Tauri config value). Each entry records *why* it exists so a future change can
either keep it or deliberately update this file with a reviewed decision.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"node_modules", "target", "dist", ".git", ".astro"}

# (name, roots, suffixes, pattern, reason)
FORBIDDEN = (
    (
        "URLhaus feed written without an explicit apply",
        ("desktop/src",),
        (".ts", ".tsx"),
        re.compile(r"urlhausApplyPending"),
        "the feed is added to the freshclam draft only; Save & Apply is the single write path",
    ),
    (
        "URLhaus notification claims automatic application",
        ("desktop/src", "po"),
        (".ts", ".tsx", ".po"),
        re.compile(r"applied automatically"),
        "the draft is not applied until the user chooses Save & Apply",
    ),
    (
        "retired event channel",
        ("desktop/src", "crates"),
        (".ts", ".tsx", ".rs"),
        re.compile(r"clamui-event"),
        "the core emits linux-defender-event; clamui-event is retired",
    ),
)

# The Tauri CSP must stay restrictive; these substrings are the reviewed policy.
CSP_FILE = ROOT / "desktop/src-tauri/tauri.conf.json"
CSP_REQUIRED = (
    "default-src 'self'",
    "script-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "frame-ancestors 'none'",
    "form-action 'none'",
)
CSP_FORBIDDEN = (
    re.compile(r"script-src[^;\"]*'unsafe-(?:inline|eval)'"),
    re.compile(r"'unsafe-eval'"),
)


def iter_files(roots: tuple[str, ...], suffixes: tuple[str, ...]):
    for root in roots:
        base = ROOT / root
        candidates = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in candidates:
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if SKIP_PARTS & set(path.relative_to(ROOT).parts):
                continue
            yield path


def main() -> int:
    failures: list[str] = []

    for name, roots, suffixes, pattern, reason in FORBIDDEN:
        for path in iter_files(roots, suffixes):
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                if line.lstrip().startswith("#~"):
                    continue  # obsolete gettext entries are history, not behavior
                if pattern.search(line):
                    failures.append(
                        f"{path.relative_to(ROOT)}:{number}: {name} — {reason}"
                    )

    csp = CSP_FILE.read_text(encoding="utf-8")
    for required in CSP_REQUIRED:
        if required not in csp:
            failures.append(
                f"{CSP_FILE.relative_to(ROOT)}: CSP lost '{required}' "
                "(reviewed Tauri policy; update deliberately, not by accident)"
            )
    for pattern in CSP_FORBIDDEN:
        match = pattern.search(csp)
        if match:
            failures.append(
                f"{CSP_FILE.relative_to(ROOT)}: CSP allows {match.group(0)!r} "
                "(inline/eval script is never permitted)"
            )

    if failures:
        print("Source invariant failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1

    print(
        f"Source invariants OK: {len(FORBIDDEN)} behavior rules, "
        f"{len(CSP_REQUIRED)} CSP rules"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
