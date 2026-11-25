---
name: ai-enforcement
description: Mandatory Linux Defender rules injected into every AI model context. Use before saying "done", for any multi-layer change, audit, parity, dead/stale/sync check, or when a visual bug is reported. It is the canonical single source of truth; all adapters read this file at runtime.
---

# Linux Defender — mandatory rules for every AI model

This is the **canonical** rules file for **every** assistant, not for one tool.
The universal path is `AGENTS.md`, the git hooks, and CI; they work identically
in Claude Code, OpenCode, Aider, Cursor, Continue, Zed, or any other assistant.
Optional tool adapters only add convenience: Claude Code `SessionStart`/`Stop`
hooks, an Aider config, and a thin `linux-defender-enforcement` skill all read
this file at runtime. Do **not**
copy these rules into a plugin or hook — adapters must read this file. The
checks below are wired into hooks and CI; you cannot claim "done" while they
fail.

## Non-negotiable before you reply "done"

1. **Run `bash scripts/check-all.sh`. Fix EVERY failure.** It blocks broken doc
   links, orphaned/dead files, cross-layer drift, version/identity drift,
   dev/build wiring drift (tauri dev -> Vite -> dist, patched vendored glib),
   unused Rust dependencies (cargo machete), all-format packaging drift,
   stale/missing signature databases,
   gettext drift, stale branding, dead frontend modules, unwired website
   components, skill drift, dead external links, stale doc phrases, and a stale
   documentation map. It is the single source of truth for static checks — do
   not invent a parallel check.
2. **Load the `linux-defender-parity` skill** for any task touching more than
   one layer (core, Tauri runtime, React frontend, translations, docs, packaging,
   CI) or any "audit / parity / dead / stale / sync / verify everything" request.
3. **Cross-layer parity is mandatory.** A feature added to one scanner, runtime,
   or doc layer must be added to ALL layers that consume it. The contracts live
   in `scripts/cross-layer-contracts.json`; add an entry for every new
   cross-cutting feature. `scripts/check-cross-layer.py` derives Tauri commands
   from `generate_handler!`, CLI subcommands from `cli.rs`, and locales from
   `po/LINGUAS`, then asserts each appears everywhere it is consumed.
4. **No dead links, no dead files, no stale docs/skills/site.** New docs must be
   linked from an existing index **and** the generated `docs/DOC-MAP.md`
   (regenerate with `python3 scripts/generate-doc-map.py`); new modules must be
   imported; new skills must be named in `AGENTS.md`, `CLAUDE.md`, and the
   website development guide; new website pages must be in the Starlight
   sidebar. The checkers enforce all of this automatically.
5. **Read the whole request.** Do not reduce a multi-part request to one easy
   part. Re-read it, enumerate every requirement, and satisfy each one. Never
   say "all done" while any named item is unaddressed.
6. **Never rebrand compatibility contracts.** `clamui-*` executable names,
   `~/.config/clamui`, `~/.local/share/clamui`, `clamui.log*`, cron markers, and
   Nautilus fallbacks are upgrade contracts with tests. Keep them.
7. **Exercise the real app and site**, not just unit tests: headless CLI
   (`status --json`, `history`, EICAR `scan`), logs, and a production-preview
   Lighthouse run for site changes. For visual bugs, use the browser harness
   (`desktop/visual-harness.html`) AND focus the real Tauri window and run
   `bash scripts/capture-app-window.sh`, then read the PNG — WebKitGTK is not
   Chromium. `scripts/check-signatures.py` verifies the host database is current
   and detects EICAR; `scripts/check-signature-feeds.py` verifies the
   product-default URLhaus export (Auth-Key redacted). The host engine and
   signature database are NEVER bundled by any package format.
8. **For full verification** run `bash scripts/audit-consistency.sh` (adds
   builds, clippy, tests, git/CI sync, and every external documentation link).
   Pre-commit runs all static checks; pre-push runs the full audit. Do not
   bypass hooks to "save time."

## Automatic enforcement (already installed)

- `scripts/hooks/pre-commit` → all static checks + Rust fmt + TS type-check.
- `scripts/hooks/pre-push` → the full audit.
- `.github/workflows/consistency.yml` → the same checks on every push/PR and
  weekly on `main`; CI runs both `check-all.sh` and `audit-consistency.sh`.
- `.github/workflows/signature-database.yml` → weekly host ClamAV database,
  EICAR, and URLhaus feed health check.
- `.github/workflows/upstream-freshness.yml` → weekly skill drift detection.
- `.github/workflows/doc-links.yml` → weekly external documentation link check.
- Claude Code: `.claude/settings.json` runs `check-all.sh` on `Stop` and injects
  this file at `SessionStart` through `scripts/hooks/ai-enforcement-context.py`.
- Aider: `.aider.conf.yml` reads `AGENTS.md` and this file into every chat.
- OpenCode: instructions and a configured adapter read this file at runtime.
- Cursor / Continue / Zed: the universal `AGENTS.md` baseline applies directly.
- The thin `.agents/skills/linux-defender-enforcement/` skill points here, so
  assistants that discover skills can find and load the rules. An optional
  Claude Code plugin package at `.claude/plugins/linux-defender-enforcement/`
  bundles a pointer skill, a capture command, and a reviewer agent; it declares
  **no hooks**, so enforcement still comes only from the always-on settings
  hooks. `claude plugin validate` validates that package.

If you bypass a hook, you must still run the check it replaced and report the
result. There is no "trust me" path.

## Keeping this file honest

`scripts/check-ai-enforcement-wiring.py` verifies in every commit that all
adapters still read this file (no duplicated rules, all hooks/commands/skill
wired). Editing the rules here is enough; do not edit copies elsewhere.
