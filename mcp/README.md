# Linux Defender assist MCP server

`linux-defender-assist/` is a local, stdio MCP server that gives an AI client
read-only or proposal-only tools for the checks a human usually performs. It is
**not** part of the application runtime and adds no dependency to the shipped
desktop app.

OpenCode loads it from `opencode.json`; other MCP clients can start it with:

```bash
bun run mcp/linux-defender-assist/src/index.ts
```

## Tools

| Tool | What it does | Boundary |
| --- | --- | --- |
| `ld_repo_status` | Reports HEAD, sync, and working-tree state. | Read-only |
| `ld_translation_candidates` | Lists identical-English strings for a locale from `po/TRANSLATION-REVIEW.md`. | Read-only |
| `ld_translation_suggest` | Asks a **local** LM Studio model for a translation proposal; never writes catalogs. | Proposal only; human applies |
| `ld_desktop_capture` | Focuses the desktop app and saves a PNG screenshot. | Writes `/tmp` image only |
| `ld_tray_probe` | Checks Sway/waybar/grim and app process readiness. | Read-only |
| `ld_helper_probe` | Checks helper path, root ownership, executable bit, and policy presence. | Read-only; never invokes `pkexec` |
| `ld_online_preflight` | Checks whether a service key exists in the OS keyring without revealing it, and shows what a submission would disclose. | No network submission |

This server deliberately does **not** install packages, start services, invoke
`pkexec`, write catalogs, or submit files/URLs to VirusTotal or urlscan. Those
actions stay with the user or the application, which has the explicit consent
and Rust-side validation.

Build check: `(cd mcp/linux-defender-assist && bun run build)`.
