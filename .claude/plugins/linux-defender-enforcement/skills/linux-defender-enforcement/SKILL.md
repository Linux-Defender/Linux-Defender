---
name: linux-defender-enforcement
description: Read and follow the canonical Linux Defender AI rules before saying "done", for multi-layer changes, audits, parity/dead/stale checks, visual bugs, or when starting work in this repository. The rules live in AI-ENFORCEMENT.md at the project root; this skill is a pointer, not a copy.
---

# Linux Defender enforcement (plugin skill)

Read `${CLAUDE_PROJECT_DIR}/AI-ENFORCEMENT.md` at the project root and follow
every rule. Do **not** treat this file as the rules source — the canonical file
is the only source of truth, and the always-on hooks in
`${CLAUDE_PROJECT_DIR}/.claude/settings.json` already enforce it.

Before saying done:

1. Run `bash scripts/check-all.sh` from the project root and fix every failure.
2. For full verification run `bash scripts/audit-consistency.sh`.
3. For multi-layer, parity, or audit work, also load the `linux-defender-parity`
   skill; for integrations use `linux-defender-integrations`; for gettext use
   `linux-defender-gettext`.

`scripts/check-ai-enforcement-wiring.py` verifies that all adapters still read
the canonical file and that no rules are duplicated.
