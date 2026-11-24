#!/usr/bin/env python3
"""Fail when source or documentation files are orphaned (dead files).

A file is live when another tracked file references it by path or by module
name, or when it is a known convention entry point. This catches the common
drift where a module, doc, or skill is added but never wired to a caller.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {".git", "node_modules", "target", "dist", ".astro", "vendor", ".svelte-kit"}

# Convention entry points and generated/legacy files that are intentionally
# not referenced by any other source file.
ALLOWED = {
    "README.md", "CHANGELOG.md", "RELEASE_NOTES.md", "LICENSE", "AGENTS.md",
    "CLAUDE.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    "index.md", "index.mdx", "404.md", "SKILL.md", "cheat-sheet.md",
    "main.rs", "lib.rs", "main.tsx", "index.ts", "index.tsx", "App.tsx",
    "vite-env.d.ts", "setupTests.ts", "middleware.ts",
}


def tracked_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    return [ROOT / p for p in out]


def is_live(path: Path, all_text: str, rel: str) -> bool:
    name = path.name
    if name in ALLOWED:
        return True
    stem = path.stem
    # Path reference (with or without extension) or module/basename reference.
    for needle in (rel, rel.rsplit(".", 1)[0], name, stem):
        if needle and needle in all_text:
            return True
    return False


def main() -> int:
    files = [p for p in tracked_files() if not any(part in SKIP_PARTS for part in p.parts)]
    text_map: dict[Path, str] = {}
    for p in files:
        try:
            text_map[p] = p.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeError):
            text_map[p] = ""
    # Exclude each file's own content from the corpus so self-mentions don't
    # count as being referenced by another file.
    all_text = "\n".join(text_map.values())

    candidates: list[Path] = []
    for p in files:
        if p.suffix not in {".md", ".mdx", ".rs", ".ts", ".tsx", ".astro", ".py", ".sh"}:
            continue
        rel = p.relative_to(ROOT).as_posix()
        # Only docs, Rust modules, and skill assets are checked; build config,
        # scripts, and platform manifests are referenced by tooling by design.
        if not (rel.startswith("docs/") or rel.startswith("website/src/content/")
                or rel.startswith(".agents/skills/") or rel.startswith("crates/")
                or rel.startswith("desktop/src-tauri/src/")):
            continue
        others = all_text.replace(text_map[p], "", 1)
        if not is_live(p, others, rel):
            candidates.append(p)

    if candidates:
        print("Orphaned files (wire to a caller or remove):", file=sys.stderr)
        for p in candidates:
            print(f"  {p.relative_to(ROOT)}", file=sys.stderr)
        print(f"{len(candidates)} orphaned file(s)", file=sys.stderr)
        return 1
    print(f"Checked {len(files)} tracked files: no orphaned docs/modules/skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
