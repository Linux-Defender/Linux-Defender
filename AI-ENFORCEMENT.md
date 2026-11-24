# Linux Defender — mandatory rules for every AI model

This file is injected into every agent context (OpenCode plugin hook, Claude
Code hook, and `opencode.json` instructions) and is referenced by `AGENTS.md`.
It exists because prose advice alone is ignored. The checks below are wired
into hooks and CI; you cannot claim "done" while they fail.

## Non-negotiable before you reply "done"

1. **Run `bash scripts/check-all.sh`. Fix EVERY failure.** It blocks broken doc
   links, orphaned/dead files, cross-layer drift, version/identity drift,
   stale/missing signature databases, gettext drift, stale branding, dead
   frontend modules, unwired website components, and skill drift. It is the
   single source of truth for static checks — do not invent a parallel check.
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
   linked from an existing index; new modules must be imported; new skills must
   be named in `AGENTS.md`, `CLAUDE.md`, and the website development guide; new
   website pages must be in the Starlight sidebar. The checkers enforce all of
   this automatically.
5. **Read the whole request.** Do not reduce a multi-part request to one easy
   part. Re-read it, enumerate every requirement, and satisfy each one. Never
   say "all done" while any named item is unaddressed.
6. **Never rebrand compatibility contracts.** `clamui-*` executable names,
   `~/.config/clamui`, `~/.local/share/clamui`, `clamui.log*`, cron markers, and
   Nautilus fallbacks are upgrade contracts with tests. Keep them.
7. **Exercise the real app and site**, not just unit tests: headless CLI
   (`status --json`, `history`, EICAR `scan`), logs, and a production-preview
   Lighthouse run for site changes. `scripts/check-signatures.py` verifies the
   host database is current and detects EICAR; `scripts/check-signature-feeds.py`
   verifies the product-default URLhaus export (Auth-Key redacted). The host
   engine and signature database are NEVER bundled by any package format.
8. **For full verification** run `bash scripts/audit-consistency.sh` (adds
   builds, clippy, tests, git/CI sync). Pre-commit runs all static checks;
   pre-push runs the full audit. Do not bypass hooks to "save time."

## Automatic enforcement (already installed)

- `scripts/hooks/pre-commit` → all static checks + Rust fmt + TS type-check.
- `scripts/hooks/pre-push` → the full audit.
- `.github/workflows/consistency.yml` → the same checks on every push/PR and
  weekly on `main`; CI runs both `check-all.sh` and `audit-consistency.sh`.
- `.github/workflows/signature-database.yml` → weekly host ClamAV database,
  EICAR, and URLhaus feed health check.
- `.github/workflows/upstream-freshness.yml` → weekly skill drift detection.
- OpenCode plugin `.opencode/plugins/linux-defender-enforcement/` injects these
  rules into every model context; `opencode.json` loads this file as instructions.
- `.claude/settings.json` runs the static checks on every Claude Code `Stop`.

If you bypass a hook, you must still run the check it replaced and report the
result. There is no "trust me" path.
