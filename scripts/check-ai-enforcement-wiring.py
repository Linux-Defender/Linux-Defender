#!/usr/bin/env python3
"""Fail when an AI adapter stops reading the canonical enforcement rules.

AI-ENFORCEMENT.md is the single source of truth. This check verifies that the
OpenCode instructions/plugin, the Claude Code hooks, the pointer skill, and the
contributor guides are all wired to it, and that no rules are duplicated in a
plugin or hook. It runs in check-all.sh on every commit.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES = ROOT / "AI-ENFORCEMENT.md"
SHELL_DIR = ROOT / "scripts/hooks"
PLUGIN_ROOT = ROOT / ".claude/plugins/linux-defender-enforcement"
EDITOR_ADAPTER = ROOT / ".editor-adapters/enforcement/index.ts"


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

    # Optional editor adapter must be loaded from its neutral path and read the
    # canonical file at runtime; it must never embed a copy of the rules.
    plugin = EDITOR_ADAPTER.read_text(errors="replace") if EDITOR_ADAPTER.exists() else ""
    if not plugin:
        failures.append("optional editor adapter is missing")
    if "AI-ENFORCEMENT.md" not in plugin or "readFile" not in plugin:
        failures.append("editor adapter does not read AI-ENFORCEMENT.md at runtime")
    if 'const RULES = `LINUX' in plugin:
        failures.append("editor adapter duplicates rules instead of reading the canonical file")
    plugins = config.get("plugins", [])
    if not any(".editor-adapters/enforcement" in json.dumps(item) for item in plugins):
        failures.append("editor adapter is not loaded from its neutral configured path")
    if (ROOT / ".opencode").exists():
        failures.append("old adapter directory still exists; current tree should stay neutral")

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

    # Optional Claude Code plugin package. It must add components, never
    # duplicate the always-on settings hooks or the rules themselves.
    manifest_path = PLUGIN_ROOT / ".claude-plugin/plugin.json"
    if not manifest_path.exists():
        failures.append("Claude Code plugin manifest is missing")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"plugin.json is invalid: {exc}")
            manifest = {}
        if manifest.get("name") != "linux-defender-enforcement":
            failures.append("plugin name is not linux-defender-enforcement")
        if "hooks" in manifest or (PLUGIN_ROOT / "hooks/hooks.json").exists():
            failures.append("plugin declares hooks that would duplicate the always-on settings hooks")
        for component in ("skills/linux-defender-enforcement/SKILL.md",
                          "commands/capture-app.md", "agents/enforcement-reviewer.md"):
            if not (PLUGIN_ROOT / component).exists():
                failures.append(f"plugin component missing: {component}")
        plugin_skill = (PLUGIN_ROOT / "skills/linux-defender-enforcement/SKILL.md").read_text(errors="replace") if (PLUGIN_ROOT / "skills/linux-defender-enforcement/SKILL.md").exists() else ""
        if "AI-ENFORCEMENT.md" not in plugin_skill or "Non-negotiable before you reply" in plugin_skill:
            failures.append("plugin skill must point to, not copy, the canonical rules")
        plugin_command = (PLUGIN_ROOT / "commands/capture-app.md").read_text(errors="replace") if (PLUGIN_ROOT / "commands/capture-app.md").exists() else ""
        if "capture-app-window.sh" not in plugin_command:
            failures.append("plugin capture command is not wired to the capture script")
        plugin_agent = (PLUGIN_ROOT / "agents/enforcement-reviewer.md").read_text(errors="replace") if (PLUGIN_ROOT / "agents/enforcement-reviewer.md").exists() else ""
        if "AI-ENFORCEMENT.md" not in plugin_agent:
            failures.append("plugin reviewer agent does not point to the canonical rules")
        if shutil.which("claude"):
            result = subprocess.run(
                ["claude", "plugin", "validate", str(PLUGIN_ROOT)],
                cwd=ROOT, capture_output=True, text=True,
            )
            if result.returncode != 0:
                failures.append(f"claude plugin validate failed: {result.stdout.strip() or result.stderr.strip()}")

    # Aider is a first-class, tool-neutral adapter.
    aider = read(".aider.conf.yml")
    if "AGENTS.md" not in aider or "AI-ENFORCEMENT.md" not in aider:
        failures.append(".aider.conf.yml does not load AGENTS.md and AI-ENFORCEMENT.md")

    # The guides must present the universal path, not privilege one tool.
    agents_doc = read("AGENTS.md")
    if "tool-agnostic" not in agents_doc or "Universal baseline" not in agents_doc:
        failures.append("AGENTS.md does not document the tool-agnostic universal baseline")
    # Every supported assistant must be named in the tool-neutral guides, with
    # Claude Code first. No tool is dropped or presented as privileged.
    tools = ["Claude Code", "OpenCode", "Codex", "Aider", "Cursor", "Continue", "Zed"]
    for guide in ("AGENTS.md", "CLAUDE.md", "AI-ENFORCEMENT.md"):
        text = read(guide)
        for tool in tools:
            if tool not in text:
                failures.append(f"{guide} does not list supported assistant: {tool}")
        positions = [text.find(tool) for tool in tools]
        if -1 not in positions and positions != sorted(positions):
            failures.append(f"{guide} lists assistants in a biased order")

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
    for guide in ("AGENTS.md", "CLAUDE.md",
                  "website/src/content/docs/docs/contributing/development.md"):
        if "linux-defender-enforcement" not in read(guide):
            failures.append(f"{guide} does not list the enforcement skill")
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
