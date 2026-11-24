#!/usr/bin/env python3
"""Fail when repo Markdown/MDX files contain broken relative links.

Checks links that point to local files by path (not http(s), mailto, anchors,
or image assets). Resolves paths relative to the containing document, honoring
the website's /Linux-Defender/docs/... root-relative form.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
IGNORED_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "#")
# Literal placeholder targets appear inside quoted historical upstream issue
# text (e.g. the RELATED-PROJECT-REVIEW quotes). They are not links to repair.
PLACEHOLDER_TARGETS = {"url", "URL", "link", "example", "example.com"}


def resolve(link: str, doc: Path) -> Path | None:
    path = link.strip().strip("<>").split("#", 1)[0].split("?", 1)[0].strip()
    if not path or any(path.startswith(s) for s in IGNORED_SCHEMES) or path.startswith("www."):
        return None
    if path in PLACEHOLDER_TARGETS:
        return None
    # Website root-relative doc links.
    for prefix in ("/Linux-Defender/docs/", "/docs/"):
        if path.startswith(prefix):
            return ROOT / "website/src/content/docs/docs" / path[len(prefix):].rstrip("/")
    if path.startswith("/"):
        # Other absolute paths map to website content root or public assets.
        candidate = ROOT / "website" / path.lstrip("/")
        return candidate if candidate.exists() else ROOT / "website/public" / path.lstrip("/")
    return (doc.parent / path).resolve()


def main() -> int:
    failures: list[str] = []
    docs = sorted(set(ROOT.glob("**/*.md")) | set(ROOT.glob("**/*.mdx")))
    docs = [d for d in docs if not any(part in {".git", "node_modules", "target", "dist", ".astro", "vendor", ".agents"} for part in d.parts)]
    for doc in docs:
        text = doc.read_text(encoding="utf-8", errors="replace")
        for match in LINK_RE.finditer(text):
            link = match.group(1).strip()
            target = resolve(link, doc)
            if target is None:
                continue
            # Directory-style links resolve to index.md / index.mdx.
            candidates = [target, target.with_suffix(".md"), target.with_suffix(".mdx"),
                          target / "index.md", target / "index.mdx"]
            if not any(c.exists() for c in candidates):
                rel = doc.relative_to(ROOT)
                failures.append(f"{rel}: {link}")
    if failures:
        print("Broken doc links:", file=sys.stderr)
        for f in failures[:100]:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} broken link(s)", file=sys.stderr)
        return 1
    print(f"Checked {len(docs)} Markdown/MDX files: no broken relative links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
