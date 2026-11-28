# AI and coding-assistant tooling (internal)

This is the internal index for the repository's optional AI tooling. It is a
contributor aid, not part of the application runtime, build, or published
website. Keep its details here rather than in user-facing docs.

## Universal rules

- `AGENTS.md` — canonical contributor guide, tool-neutral.
- `AI-ENFORCEMENT.md` — canonical rules file with skill-style frontmatter. Every
  adapter reads it; no rules are duplicated.
- `CLAUDE.md` — short discoverability stub for Claude Code.
- `CONTEXT.md` — shared vocabulary for assistants.

Supported assistants listed in the universal entry points: **Claude Code,
OpenCode (Open Code), Codex, Aider, Cursor, Continue, Zed**, and any other
assistant that reads `AGENTS.md`. Git hooks and CI enforce the same checks for
all of them; adapters only add convenience.

## Adapters

| Adapter | Location | Notes |
| --- | --- | --- |
| OpenCode | `opencode.json`, `.editor-adapters/enforcement/` | Instructions, a configured context-hook adapter that reads the canonical rules at runtime, and `/deep-audit`. |
| All assistants | `docs/ai-tooling/CONTEXT.md` | Shared vocabulary; the phrase **"yk the drill"** activates the full deep audit everywhere. |
| Claude Code | `.claude/settings.json`, `.claude/commands/`, `.claude/skills/` | `SessionStart`/`UserPromptSubmit` context, `Stop` checks, pointer skill, capture command. |
| Claude plugin package | `.claude/plugins/linux-defender-enforcement/` | Optional pointer skill, capture command, reviewer agent; declares **no hooks**. |
| Aider | `.aider.conf.yml` | Loads `AGENTS.md` and `AI-ENFORCEMENT.md` into every chat. |
| Cursor / Continue / Zed | `AGENTS.md` convention | Universal baseline applies directly. |
| Skills | `.agents/skills/`, linked from `.claude/skills/` | `linux-defender-parity`, `linux-defender-integrations`, `linux-defender-gettext`, `linux-defender-enforcement`, plus imported base skills. |
| MCP server | `mcp/linux-defender-assist/` | Local stdio tools for translation review, desktop capture, tray/helper probing, online-service preflight, and read-only cross-layer support-parity reporting. Never performs privileged installs, catalog writes, or external submissions. |

`scripts/check-ai-enforcement-wiring.py` verifies that every adapter still
reads the canonical file, that no rules are duplicated, that all supported
assistants are listed, and that hooks/commands/skills are wired.
`scripts/check-all.sh` verifies the MCP server type-checks.

## Conventions

- Do not copy rules into plugins, hooks, or this index. Point to
  `AI-ENFORCEMENT.md`.
- Keep tool-specific files in dot-directories; do not add AI branding to the
  published website or user-facing app.
- When adding an assistant, update **all** universal entry points and the
  wiring checker in the same change.

## Support-parity guard

`scripts/check-support-parity.py` enforces the declarative behavioral contracts in
`scripts/support-parity-contracts.json` (online-service symmetry, frontend
validators, scheduler cleanup, quarantine confinement, least-privilege
capabilities, helper bounds, and untrusted-input sanitization). It runs in
`check-all.sh`, the pre-commit gate, and CI; the read-only MCP tool
`ld_support_parity` reports the same result without changing any file. New
contracts require a negative test in `scripts/tests/test_support_parity.py`.
