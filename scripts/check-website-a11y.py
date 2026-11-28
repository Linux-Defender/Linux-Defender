#!/usr/bin/env python3
"""Guard the site fixes found by the production-preview Lighthouse audit.

Two regressions are guarded here:

  * Starlight's search button shows "Search documentation Ctrl K" but ships a
    static aria-label of only "Search documentation". On every navigation the
    head script must realign the accessible name with the visible label, and
    hide the keyboard badge from assistive technology.
  * The light-header hover utilities are overridden by the blanket light-mode
    rules, so scoped hover colors must stay present or the nav becomes hard to
    read on light backgrounds.
  * Light mode must not repaint the intentionally-dark terminal/preview with
    dark ink, and small secondary text and FAQ number bubbles must keep AA
    contrast. These were found by a light-mode Lighthouse run.

A duplicate copy in Base.astro is rejected too: the head script already runs
on every page, and a second copy is dead code that drifts independently.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    config = root / "website/astro.config.mjs"
    css = root / "website/src/styles/global.css"
    base = root / "website/src/layouts/Base.astro"

    if not config.exists():
        failures.append("website/astro.config.mjs is missing")
    else:
        text = config.read_text(encoding="utf-8")
        for marker in (
            'tag: "script"',
            'button[data-open-modal]',
            "astro:page-load",
            "aria-label",
            "kbd",
            "aria-hidden",
        ):
            if marker not in text:
                failures.append(f"Starlight head lost search-label fix ({marker})")
        if "aria-label', 'Search documentation Ctrl K'" in text:
            failures.append(
                "search-label script hardcodes a name that does not match the visible label"
            )

    if not css.exists():
        failures.append("website/src/styles/global.css is missing")
    else:
        text = css.read_text(encoding="utf-8")
        for marker in (
            'html.light header.sticky [class~="hover:text-white"]:hover',
            'html.light header.sticky #theme-toggle:hover',
            'html.light .term [class~="text-guard-sage"]',
            'html.light .product-preview [class~="text-guard-sage"]',
            'text-white/50"] { color: rgba(20, 32, 26, 0.72); }',
            'text-white/45"] { color: rgba(20, 32, 26, 0.72); }',
            'text-white/40"] { color: rgba(20, 32, 26, 0.70); }',
            'html.light footer a:hover,',
            'color: #116932;',
        ):
            if marker not in text:
                failures.append(f"light-header hover rule lost ({marker})")

    if base.exists() and "syncSearchLabel" in base.read_text(encoding="utf-8"):
        failures.append("Base.astro duplicates the Starlight search-label script")

    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Website accessibility contract failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Website a11y OK: search label and light-header hover guarded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
