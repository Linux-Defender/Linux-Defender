#!/usr/bin/env python3
"""Fail when an AI adapter stops reading the canonical enforcement rules.

AI-ENFORCEMENT.md is the single source of truth. This check verifies that the
OpenCode instructions/plugin, the Claude Code hooks, the pointer skill, and the
contributor guides are all wired to it, and that no rules are duplicated in a
plugin or hook. It runs in check-all.sh on every commit.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "AI-ENFORCEMENT.md"
SHELL_DIR = ROOT / "scripts/hooks"


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main() -> int:
    failures: list[str] = []
    if not RULES.exists():
        print("FAIL: AI-ENFORCEMENT.md is missing", file=sys.stderr)
        return 1
    rules_text = RULES.read_text(encoding="utf-8")
    if "Non-negotiable before you reply" not in rules_text:
        failures.append("AI-ENFORCEMENT.md lost its non-negotiable rules section")

    # OpenCode instructions.
    try:
        config = json.loads(read("opencode.json"))
    except json.JSONDecodeError as exc:
        failures.append(f"opencode.json is invalid: {exc}")
        config = {}
    instructions = config.get("instructions", [])
    if "AI-ENFORCEMENT.md" not in instructions:
        failures.append("opencode.json no longer loads AI-ENFORCEMENT.md as instructions")

    # OpenCode plugin must read the file at runtime, not embed a copy.
    plugin = read(".opencode/plugins/linux-defender-enforcement/index.ts")
    if not plugin:
        failures.append("OpenCode enforcement plugin is missing")
    if "AI-ENFORCEMENT.md" not in plugin or "readFile" not in plugin:
        failures.append("OpenCode plugin does not read AI-ENFORCEMENT.md at runtime")
    if 'const RULES = `LINUX' in plugin:
        failures.append("OpenCode plugin duplicates rules instead of reading the canonical file")

    # Claude Code hooks.
    try:
        settings = json.loads(read(".claude/settings.json"))
    except json.JSONDecodeError as exc:
        failures.append(f".claude/settings.json is invalid: {exc}")
        settings = {}
    hooks = settings.get("hooks", {})
    session = json.dumps(hooks.get("SessionStart", []))
    if "ai-enforcement-context.py" not in session or "SessionStart" not in session:
        failures.append("Claude Code SessionStart hook does not inject the canonical rules")
    user_prompt = json.dumps(hooks.get("UserPromptSubmit", []))
    if "ai-enforcement-context.py" not in user_prompt:
        failures.append("Claude Code UserPromptSubmit reminder hook is missing")
    stop = json.dumps(hooks.get("Stop", []))
    if "check-all.sh" not in stop:
        failures.append("Claude Code Stop hook no longer runs check-all.sh")

    # The context emitter must read the canonical file and emit valid JSON for
    # both events; never duplicate the rules in the script.
    emitter = read("scripts/hooks/ai-enforcement-context.py")
    if "AI-ENFORCEMENT.md" not in emitter or "json.dumps" not in emitter:
        failures.append("ai-enforcement-context.py is not wired to the canonical file")
    for event in ("SessionStart", "UserPromptSubmit"):
        result = subprocess.run(
            [sys.executable, str(SHELL_DIR / "ai-enforcement-context.py"), event],
            cwd=ROOT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            failures.append(f"ai-enforcement-context.py {event} failed: {result.stderr.strip()}")
            continue
        try:
            payload = json.loads(result.stdout)
            context = payload["hookSpecificOutput"]["additionalContext"]
            if not context or len(context) > 10_000:
                failures.append(f"ai-enforcement-context.py {event} emitted empty/oversized context")
        except (ValueError, KeyError) as exc:
            failures.append(f"ai-enforcement-context.py {event} emitted invalid JSON: {exc}")

    # Pointer skill and contributor guides must name the canonical file/skill.
    skill = read(".agents/skills/linux-defender-enforcement/SKILL.md")
    if "AI-ENFORCEMENT.md" not in skill:
        failures.append("pointer skill does not point to AI-ENFORCEMENT.md")
    if not (ROOT / ".claude/skills/linux-defender-enforcement").is_symlink():
        failures.append("Claude Code compatibility link for the enforcement skill is missing")
    for guide in ("AGENTS.md", "CLAUDE.md", "CONTEXT.md",
                  "website/src/content/docs/docs/contributing/development.md"):
        if "AI-ENFORCEMENT.md" not in read(guide):
            failures.append(f"{guide} does not reference AI-ENFORCEMENT.md")
    if "linux-defender-enforcement" not in read("AGENTS.md"):
        failures.append("AGENTS.md does not list the enforcement skill")
    if "check-ai-enforcement-wiring.py" not in rules_text:
        failures.append("AI-ENFORCEMENT.md does not document its own wiring check")

    if failures:
        print("AI enforcement wiring failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} wiring failure(s)", file=sys.stderr)
        return 1
    print("AI enforcement wiring OK: all adapters read AI-ENFORCEMENT.md; no duplicated rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
