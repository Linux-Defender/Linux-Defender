#!/usr/bin/env python3
"""Fail when the custom-signature URL list can regress to a squeezed layout.

The original bug rendered long provider URLs one character per line in a
half-width grid column and squeezed the Remove buttons. These CSS rules are the
fix; a static contract makes deleting or overriding them fail check-all.sh,
pre-commit, and CI instead of silently shipping a broken UI.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = Path(os.environ.get("URL_LIST_CSS", ROOT / "desktop/src/styles.css"))
TSX = Path(
    os.environ.get("URL_LIST_TSX", ROOT / "desktop/src/pages/ConfigPreferences.tsx")
)

RULES = {
    ".url-list": ["grid-column: 1 / -1", "width: 100%"],
    ".url-list .row": ["min-height: 0"],
    ".url-list .row > code": ["min-width: 0", "overflow-wrap: anywhere"],
    ".url-list .row > .button": ["flex: 0 0 auto", "white-space: nowrap"],
}


def css_block(text: str, selector: str) -> str | None:
    match = re.search(
        re.escape(selector) + r"\s*\{([^}]*)\}", text
    )
    return match.group(1) if match else None


def main() -> int:
    failures: list[str] = []
    css = CSS.read_text(encoding="utf-8", errors="replace") if CSS.exists() else ""
    tsx = TSX.read_text(encoding="utf-8", errors="replace") if TSX.exists() else ""

    if tsx.count('className="table url-list"') < 2:
        failures.append("both custom URL lists must use the url-list class")

    for selector, required in RULES.items():
        block = css_block(css, selector)
        if block is None:
            failures.append(f"missing CSS rule: {selector}")
            continue
        for declaration in required:
            if declaration not in block:
                failures.append(f"{selector} must declare {declaration!r}")

    if failures:
        print("URL list layout failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(f"{len(failures)} URL list layout failure(s)", file=sys.stderr)
        return 1
    print("URL list layout OK: full-width rows, wrapped URLs, unsqueezed Remove buttons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
