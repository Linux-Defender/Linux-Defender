#!/usr/bin/env python3
"""Fail when the custom-signature URL list regresses to a squeezed layout."""
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
    ".url-list .row > code": ["min-width: 0", "overflow-wrap: anywhere"],
    ".url-list .row > .button": ["flex: 0 0 auto", "white-space: nowrap"],
}


def main() -> int:
    failures: list[str] = []
    css = CSS.read_text(errors="replace") if CSS.exists() else ""
    tsx = TSX.read_text(errors="replace") if TSX.exists() else ""
    if tsx.count('className="table url-list"') < 2:
        failures.append("both custom URL lists must use the url-list class")
    for selector, required in RULES.items():
        match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
        if not match:
            failures.append(f"missing CSS rule: {selector}")
            continue
        for declaration in required:
            if declaration not in match.group(1):
                failures.append(f"{selector} must declare {declaration!r}")
    if failures:
        print("URL list layout failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("URL list layout OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
