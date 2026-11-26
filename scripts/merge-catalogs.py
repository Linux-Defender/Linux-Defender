#!/usr/bin/env python3
"""Regenerate the POT and merge it into all active catalogs safely.

Runs `update-pot.sh`, `msgmerge` for every po/LINGUAS locale, and fills only
newly added empty msgstr entries with the English source as fallback (the
documented first-pass convention in docs/translations/README.md). Existing
translations are never overwritten. Verify with check-translations.sh after.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PO = ROOT / "po"


def unquote(value: str) -> str:
    return value.replace('\\"', '"').replace("\\\\", "\\")


def quoted(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def msgids(path: Path) -> set[str]:
    result: set[str] = set()
    for block in path.read_text(encoding="utf-8").split("\n\n"):
        lines = block.splitlines()
        for index, line in enumerate(lines):
            if not line.startswith("msgid "):
                continue
            parts = [] if line == 'msgid ""' else [re.match(r'msgid "(.*)"$', line).group(1)]
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].startswith('"'):
                parts.append(re.match(r'"(.*)"$', lines[cursor]).group(1))
                cursor += 1
            result.add(unquote("".join(parts)))
            break
    return result


def main() -> int:
    pot = PO / "linux-defender.pot"
    before = msgids(pot) if pot.exists() else set()
    subprocess.run(["bash", "scripts/update-pot.sh"], cwd=ROOT, check=True)
    new = msgids(pot) - before

    linguas = [line.strip() for line in (PO / "LINGUAS").read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.strip().startswith("#")]
    for locale in linguas:
        catalog = PO / f"{locale}.po"
        subprocess.run(["msgmerge", "--update", "--no-fuzzy-matching", str(catalog), str(pot)],
                       cwd=ROOT, check=True)
        blocks = catalog.read_text(encoding="utf-8").split("\n\n")
        for block_index, block in enumerate(blocks):
            lines = block.splitlines()
            try:
                msgid_line = next(i for i, line in enumerate(lines) if line.startswith("msgid "))
            except StopIteration:
                continue
            parts = [] if lines[msgid_line] == 'msgid ""' else [
                re.match(r'msgid "(.*)"$', lines[msgid_line]).group(1)
            ]
            cursor = msgid_line + 1
            while cursor < len(lines) and lines[cursor].startswith('"'):
                parts.append(re.match(r'"(.*)"$', lines[cursor]).group(1))
                cursor += 1
            msgid = unquote("".join(parts))
            if msgid not in new:
                continue
            while cursor < len(lines) and not lines[cursor].startswith("msgstr"):
                cursor += 1
            if cursor >= len(lines):
                continue
            start = cursor + 1
            end = start
            while end < len(lines) and lines[end].startswith('"'):
                end += 1
            if unquote("".join(re.match(r'"(.*)"$', line).group(1) for line in lines[start:end])):
                continue
            lines[cursor:end] = [f'msgstr "{quoted(msgid)}"']
            blocks[block_index] = "\n".join(lines)
        catalog.write_text("\n\n".join(blocks), encoding="utf-8")

    print(f"Merged POT into {len(linguas)} catalogs; filled {len(new)} new entries with English fallback")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
