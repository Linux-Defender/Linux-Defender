#!/usr/bin/env python3
"""Fail when declared cross-layer and cross-service support drifts apart.

Derives support from `support-parity-contracts.json`: every rule names the files
that must implement a set of patterns (or the union of files, for rules that
spread one invariant across modules). This is a second, declarative guard next
to check-cross-layer.py: the latter derives Tauri/CLI/locale contracts from
code, while this one locks the *behavioral* symmetry that a partial fix would
silently break (e.g. VirusTotal hardened but urlscan left behind).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = Path(
    os.environ.get("SUPPORT_PARITY_CONTRACTS", ROOT / "scripts" / "support-parity-contracts.json" )
)


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    failures: list[str] = []
    try:
        data = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read support parity contracts: {exc}", file=sys.stderr)
        return 1

    rules = data.get("rules", [])
    if len(rules) < 10:
        failures.append(f"support-parity contract has only {len(rules)} rules (expected at least 10)")
    for rule in rules:
        name = rule.get("name", "<unnamed>")
        files = rule.get("files", [])
        patterns = rule.get("patterns", [])
        forbidden = rule.get("forbidden", [])
        mode = rule.get("mode", "per-file")
        if not files or not patterns:
            failures.append(f"rule {name}: missing files or patterns")
            continue
        sources = {rel: read(rel) for rel in files}
        for rel, source in sources.items():
            if not source:
                failures.append(f"rule {name}: source file missing or empty: {rel}")
        for forbidden_text in forbidden:
            for rel, source in sources.items():
                if forbidden_text in source:
                    failures.append(
                        f"rule {name}: forbidden pattern in {rel}: {forbidden_text!r}"
                    )
        if mode == "union":
            corpus = "\n".join(sources.values())
            for pattern in patterns:
                if pattern not in corpus:
                    failures.append(f"rule {name}: pattern missing from all files: {pattern!r}")
        else:
            for rel, source in sources.items():
                for pattern in patterns:
                    if pattern not in source:
                        failures.append(f"rule {name}: {pattern!r} missing from {rel}")

    if failures:
        print("Support parity failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(f"{len(failures)} support parity failure(s)", file=sys.stderr)
        return 1
    print(f"Support parity OK: {len(data.get('rules', []))} cross-layer invariants hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
