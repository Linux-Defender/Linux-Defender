#!/usr/bin/env python3
"""Fail when a built static site has broken links, anchors, or malformed structure.

In addition to local links/anchors, this owns the structural checks that used
to come from proof-html's HTML/CSS validators (v1) or its v2 Nu validator:
DOCTYPE, unique IDs, image alt text, well-formed inline style declarations,
and balanced CSS blocks. Those validators reject Starlight/Shiki generated
custom properties, so this site-local check is the enforced equivalent.
"""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

CANONICAL_HOSTS = {"linux-defender.github.io"}
BASE_PATH = "/Linux-Defender"
IGNORED_SCHEMES = {"data", "javascript", "mailto", "tel"}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: set[str] = set()
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.links: list[str] = []
        self.has_doctype = False
        self.images_without_alt: list[str] = []
        self.bad_inline_styles: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)
        for anchor in (element_id, attributes.get("name")):
            if anchor:
                self.anchors.add(anchor)
        if _tag == "img" and "alt" not in attributes:
            self.images_without_alt.append(attributes.get("src", "<no src>"))
        if style := attributes.get("style"):
            for declaration in style.split(";"):
                if declaration.strip() and ":" not in declaration:
                    self.bad_inline_styles.append(declaration.strip())
        for attribute in ("href", "src"):
            if value := attributes.get(attribute):
                self.links.append(value)
        if srcset := attributes.get("srcset"):
            self.links.extend(
                candidate.strip().split(maxsplit=1)[0]
                for candidate in srcset.split(",")
                if candidate.strip()
            )


def public_path(site: Path, page: Path) -> str:
    relative = page.relative_to(site).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return f"/{relative.removesuffix('index.html')}"
    return f"/{relative}"


def target_path(site: Path, target_url: str) -> Path | None:
    path = unquote(urlsplit(target_url).path).lstrip("/")
    path = path.removeprefix(f"{BASE_PATH.lstrip('/')}/")
    if path == BASE_PATH.lstrip("/"):
        path = ""
    if not path:
        return site / "index.html"

    direct = site / path
    clean_path = path.rstrip("/")
    candidates = [direct]
    if clean_path:
        candidates.append(site / f"{clean_path}.html")
    candidates.append(site / clean_path / "index.html")

    return next((candidate for candidate in candidates if candidate.is_file()), None)


def is_local(url: str) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme.lower() in IGNORED_SCHEMES:
        return False
    if parsed.scheme in {"http", "https"} or parsed.netloc:
        return parsed.netloc.lower().split(":", 1)[0] in CANONICAL_HOSTS
    return not parsed.scheme


def check_site(site: Path) -> list[str]:
    pages: dict[Path, PageParser] = {}
    public_urls: dict[Path, str] = {}
    for page in site.rglob("*.html"):
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        parser.close()
        pages[page] = parser
        public_urls[page] = public_path(site, page)

    errors: list[str] = []
    for page, parser in pages.items():
        label = page.relative_to(site)
        if not parser.has_doctype:
            errors.append(f"{label}: missing <!DOCTYPE html>")
        for duplicate in sorted(parser.duplicate_ids):
            errors.append(f"{label}: duplicate id '{duplicate}'")
        for source in parser.images_without_alt:
            errors.append(f"{label}: img without alt: {source}")
        for declaration in parser.bad_inline_styles:
            errors.append(f"{label}: malformed inline style declaration: {declaration}")
        base_url = f"https://linux-defender.github.io{BASE_PATH}{public_urls[page]}"
        for link in parser.links:
            if not is_local(link):
                continue
            target_url = urljoin(base_url, link)
            target = target_path(site, target_url)
            reference = f"{page.relative_to(site)} -> {link}"
            if target is None:
                errors.append(f"{reference}: missing local target")
                continue

            fragment = unquote(urlsplit(target_url).fragment)
            target_parser = pages.get(target)
            if fragment and target_parser and fragment not in target_parser.anchors:
                errors.append(f"{reference}: missing anchor #{fragment}")

    # CSS blocks must be balanced. Modern at-rules and custom properties are
    # valid here; only structural corruption is rejected (a third-party Nu
    # validator would reject the generator's @property rules).
    for stylesheet in site.rglob("*.css"):
        css = re.sub(r"/\*.*?\*/", "", stylesheet.read_text(encoding="utf-8", errors="replace"), flags=re.S)
        if css.count("{") != css.count("}"):
            errors.append(
                f"{stylesheet.relative_to(site)}: unbalanced CSS blocks "
                f"({css.count('{')} open, {css.count('}')} close)"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site", type=Path, help="built site directory")
    args = parser.parse_args()
    site = args.site.resolve()
    if not site.is_dir():
        parser.error(f"not a directory: {site}")

    errors = check_site(site)
    if not errors:
        print(f"Validated local links, anchors, and HTML/CSS structure in {site}")
        return 0

    print("Broken built-site references:")
    print("\n".join(f"- {error}" for error in sorted(set(errors))))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
