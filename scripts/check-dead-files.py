#!/usr/bin/env python3
"""Fail when tracked files are orphaned (dead files) anywhere in the repo.

A file is live when another tracked file references it by path, basename, or
module name, or when it lives in a directory that tooling discovers by
convention (GitHub metadata, tests, published assets, packaging, etc.). This
covers the whole repository: source, docs, skills, workflows, scripts, site,
and packaging.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "node_modules", "target", "dist", ".astro", "vendor", ".svelte-kit", "__pycache__"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".mo", ".pdf", ".zip"}

# Files that are entry points by convention and need no in-repo reference.
ALLOWED_NAMES = {
    "README.md", "CHANGELOG.md", "RELEASE_NOTES.md", "LICENSE", "AGENTS.md",
    "CLAUDE.md", "CONTEXT.md", "AI-ENFORCEMENT.md", "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "index.md", "index.mdx", "404.md",
    "SKILL.md", "main.rs", "lib.rs", "main.tsx", "index.ts", "index.tsx",
    "App.tsx", "vite-env.d.ts", "middleware.ts", ".gitignore", ".tldrignore",
    "content.config.ts", "astro.config.mjs",
}

# Directories whose contents are discovered by tooling rather than by an
# explicit reference to each file name.
CONVENTION_DIRS = {
    ".github", "tests", "screenshots", "hooks", "rules", "references",
    "assets", "public", "icons", "data", "debian", "flathub", "appimage",
    "snap", "capabilities",
}


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [ROOT / p for p in out]


def main() -> int:
    files = [p for p in tracked_files() if not any(part in SKIP_PARTS for part in p.parts)]
    texts: dict[Path, str] = {}
    for p in files:
        try:
            texts[p] = p.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            texts[p] = ""
    corpus = "\n".join(texts.values())

    orphans: list[Path] = []
    checked = 0
    for path in files:
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        rel = path.relative_to(ROOT).as_posix()
        name = path.name
        if name in ALLOWED_NAMES:
            continue
        parent_names = set(path.parts[:-1])
        if parent_names & CONVENTION_DIRS:
            continue
        others = corpus.replace(texts[path], "", 1)
        needles = {rel, rel.rsplit(".", 1)[0], name, path.stem}
        if any(n and n in others for n in needles):
            continue
        checked += 1
        orphans.append(path)

    if orphans:
        print("Orphaned files (wire to a caller or remove):", file=sys.stderr)
        for p in orphans:
            print(f"  {p.relative_to(ROOT)}", file=sys.stderr)
        print(f"{len(orphans)} orphaned file(s)", file=sys.stderr)
        return 1
    print(f"Checked {len(files)} tracked files ({checked} strictly): no orphaned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
