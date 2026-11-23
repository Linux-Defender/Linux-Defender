# CLAUDE.md

The AI-assistant guide for this repository lives in [`AGENTS.md`](AGENTS.md). That file is the canonical source and is also auto-read by Cursor, Aider, OpenCode, Continue, and Zed.

**Edit `AGENTS.md`, not this file.** This stub exists only so Claude Code's CLAUDE.md auto-discovery still finds guidance.

Project-local coding-agent skills live in `.agents/skills` (`accessibility`, `linux-defender-gettext`, `linux-defender-parity`, `linux-defender-integrations`, `rust-best-practices`, `vercel-react-best-practices`); Claude Code and other assistants can use them directly. Use `linux-defender-parity` for any "audit everything / check parity / find dead or stale code / verify sync" task and `linux-defender-integrations` for native/desktop/host integrations. Both point to `AGENTS.md` and `docs/clamui-fork/STATUS.md` as the canonical records.
