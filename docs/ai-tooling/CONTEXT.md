# Shared vocabulary for assistants

Use these terms exactly so every assistant and human means the same thing.

- **Canonical rules:** `AI-ENFORCEMENT.md`, read through `AGENTS.md`; adapters only add convenience.
- **Static gate:** `bash scripts/check-all.sh` — every commit and PR runs it.
- **Full audit:** `bash scripts/audit-consistency.sh` — adds builds, tests, clippy, git/CI sync and external links.
- **Regeneration:** `./scripts/update-all.sh` (`--check` verifies only, `--full` refreshes locked packaging sources).
- **Deep audit:** `./scripts/deep-audit.sh` — the exhaustive review: regenerated-artifact checks, every gate, parity/signature/image guards, CI status, and the 23-domain agent-fleet brief (`--quick` static-only, `--fleet` brief only).
- **Activation phrase:** **"yk the drill"** — run the deep audit (default full mode), read its report, fix every failure with a fail-closed guard in `check-all.sh`, update the ledger in `docs/revival/CHAT-AND-PROJECT-AUDIT.md`, then re-run until zero failures and report the final state.

The same phrase activates the workflow in Claude Code (`/deep-audit`), OpenCode (`/deep-audit`), the read-only MCP tool `ld_deep_audit`, Aider/Cursor/Continue/Zed (through `AGENTS.md`), and any other assistant that reads the repository instructions. It never creates a tag, dispatches Release, invokes `pkexec`, or submits data externally.
