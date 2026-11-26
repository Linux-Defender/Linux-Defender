#!/usr/bin/env python3
"""Emit AI-ENFORCEMENT.md as Claude Code hook additionalContext.

SessionStart: inject the full canonical rules file (frontmatter stripped).
UserPromptSubmit: inject a short reminder pointing at the canonical file.
Never duplicate the rules here; this script only reads AI-ENFORCEMENT.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "AI-ENFORCEMENT.md"
EVENT = sys.argv[1] if len(sys.argv) > 1 else "SessionStart"


def rules_text() -> str:
    try:
        text = RULES.read_text(encoding="utf-8")
    except OSError as exc:
        return f"ENFORCEMENT ERROR: cannot read {RULES}: {exc}"
    return text.replace("---\n", "", 2) if text.startswith("---\n") else text


if EVENT == "SessionStart":
    context = (
        "Linux Defender canonical AI rules (AI-ENFORCEMENT.md, injected by hook):\n"
        + rules_text()
    )
elif EVENT == "UserPromptSubmit":
    context = (
        "Linux Defender reminder: follow AI-ENFORCEMENT.md (canonical rules). "
        "Before saying done run bash scripts/check-all.sh and fix every failure; "
        "for multi-layer or audit tasks use the linux-defender-parity skill."
    )
else:
    context = ""

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": EVENT,
        "additionalContext": context,
    }
}, ensure_ascii=False))
