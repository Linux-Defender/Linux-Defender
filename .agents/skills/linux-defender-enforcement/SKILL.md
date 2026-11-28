---
name: linux-defender-enforcement
description: Read and follow the canonical Linux Defender AI rules before saying "done", for multi-layer changes, audits, parity/dead/stale checks, visual bugs, or when starting work in this repository. This skill is a pointer; the rules themselves live in AI-ENFORCEMENT.md at the repository root.
---

# Linux Defender enforcement (pointer skill)

This skill is deliberately thin: **do not duplicate the rules here**. The
canonical rules file is [`AI-ENFORCEMENT.md`](../../../AI-ENFORCEMENT.md) at the
repository root. Project adapters and hooks inject it into model context at
runtime; this skill exists so assistants that discover skills can find it too.

When invoked:

1. Read `AI-ENFORCEMENT.md` at the repository root and follow every rule.
2. Run `bash scripts/check-all.sh` and fix every failure before declaring done;
   for full verification run `bash scripts/audit-consistency.sh`.
3. For multi-layer, parity, or audit work, also load the `linux-defender-parity`
   skill. For native integrations load `linux-defender-integrations`; for
   gettext load `linux-defender-gettext`.

`scripts/check-ai-enforcement-wiring.py` verifies that every adapter (Claude Code hooks, Aider config, this skill, and
the contributor guides) still reads the canonical file and that no rules are duplicated.

## Activation phrase

Say **"yk the drill"** in any assistant to activate the canonical exhaustive review: `./scripts/deep-audit.sh` (or `/deep-audit`, or the read-only MCP `ld_deep_audit`). It fixes failures with fail-closed guards in `scripts/check-all.sh`, updates the ledger, and repeats until zero failures. Never create a tag, dispatch Release, invoke `pkexec`, or submit data externally.
