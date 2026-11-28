---
description: Run the canonical Linux Defender deep audit across repo, app, site, all formats and upstream parity.
---

Run the single deep-audit entry point and report every failure with file:line and a concrete fix:

```bash
${CLAUDE_PROJECT_DIR}/scripts/deep-audit.sh
```

For a static-only pass (safe from a chat turn), use `--quick`. For the exhaustive
read-only agent fleet brief, use `--fleet` and spawn one agent per domain listed
there: Rust core, Tauri/IPC, React/a11y, website/gettext, all six package formats,
workflows/guards, docs, upstream ClamUI/ClamTk/Lenspect, advisories, images,
CLI/data compatibility, scheduler/privacy, tests, MCP, install guidance, licensing,
release readiness, cross-layer contracts, and universal-entry parity. Agents must
never edit, commit, push, create tags, or dispatch Release. Record fixes with
fail-closed guards in `scripts/check-all.sh` and the ledger in
`docs/revival/CHAT-AND-PROJECT-AUDIT.md`.
