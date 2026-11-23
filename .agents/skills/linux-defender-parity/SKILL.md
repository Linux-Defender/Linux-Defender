---
name: linux-defender-parity
description: Audit Linux Defender for upstream ClamUI/ClamTk parity, cross-file consistency, dead code, stale branding, and CI sync. Use when porting upstream work, reviewing a change, before release, or when asked to "check parity", "audit everything", "find dead/stale code", "make sure nothing is forgotten", or "verify sync".
---

# Linux Defender parity and consistency audit

Use this skill whenever work touches more than one boundary (Rust core, Tauri
runtime, React frontend, translations, docs, packaging, or CI), when porting a
ClamUI/ClamTk/Lenspect behavior, or before saying a task is done.

## Authoritative records

- `docs/revival/RELATED-PROJECT-REVIEW.md` — the live upstream parity matrix
  (repository, reviewed commit/date, issue/PR ids, implemented/deferred/open).
- `docs/clamui-fork/STATUS.md` — what was ported from ClamUI, what is
  deliberately deferred (scanner concurrency, full Flush UI), and what was
  superseded (Dashboard/ScanOverview/scanHistory). Update it when porting.
- `AGENTS.md` — canonical contributor rules (security, IPC, compatibility,
  build/test, Claude/OpenCode/Cursor/Aider/Continue/Zed guidance).

## Audit checklist (run all, in order)

1. **Full automated check.** Run `bash scripts/audit-consistency.sh`. It
   verifies formatting, clippy, tests, frontend type-check/build/tests, the
   website, gettext extraction/catalogs, stale references, dead frontend
   modules, git sync, and GitHub Actions status. Fix every failure before
   continuing.
2. **Parity matrix.** For the behavior being added/changed, confirm the matrix
   in `docs/revival/RELATED-PROJECT-REVIEW.md` records the upstream source,
   reviewed commit, and status. A merged upstream PR is not proof the behavior
   exists here; verify our code and tests independently.
3. **Port boundary.** Implement behavior in the owning Rust core module, expose
   it through the narrow Tauri command allowlist, then wire the typed frontend
   API. Add a consumer-visible regression test at the owning boundary.
4. **Cross-file consistency.** A new IPC field must appear in the Rust
   `StartupState`, the frontend `StartupState` in `desktop/src/api.ts`, and any
   event payloads. A new user-visible string must be a static `_()` literal in
   source and present in `po/linux-defender.pot` + all 10 catalogs
   (`de en es fr hu it nb pt_BR vi zh_CN`).
5. **Dead code.** Every ported frontend module must be imported by a live
   caller or removed/superseded. Use the dead-module section of the audit
   script. Rust dead code is caught by `cargo clippy -- -D warnings`.
6. **Stale references.** The audit script greps for
   `clamui.com|linx.systems|clamui@|rooki.xyz|io.github.linx`. Only intentional
   historical/compat references (docs/revival, docs/clamui-fork, CHANGELOG,
   LICENSE, migration constants and their tests) are allowed.
7. **Generated artifacts.** Never hand-edit `po/*.mo`, `desktop/dist/`,
   `website/public/` generated assets, or `desktop/src-tauri/gen/`. Refresh the
   POT with `./scripts/update-pot.sh`, merge catalogs with `msgmerge`, strip
   obsolete entries, then `msgfmt -c` / `msgcmp` verify.
8. **CI sync.** All workflows on HEAD must be green. A local "looks fine" is
   not enough. Check with `gh run list --commit $(git rev-parse HEAD)`.
9. **Real-app exercise.** Run the headless CLI (`status --json`, `history`, an
   EICAR `scan`), read `~/.local/share/linux-defender/debug/linux-defender.log`,
   and confirm the Tauri build. Check GitHub tabs (Actions, Security,
   issues/PRs) for anything unresolved. A green unit suite is not proof the
   host ClamAV bridge, helper, or tray work.

## What is deliberately NOT ported (do not "fix" by copying)

- `scanner.rs` concurrent daemon sharding / cumulative multi-target progress
  (upstream's `run_daemon_file_lists`, `daemon_worker_count`,
  `merge_daemon_worker_outputs`, `ProgressReporter`): LD's scanner has
  diverged (YARA rules, engine options, Thunar integration); a blind port risks
  scan correctness regressions. Revisit only with dedicated tests.
- Full autosave/Flush UI: LD uses explicit **Save & Apply**; the shared helpers
  (`savePlan.ts`, `configDraft.ts`, `configAuthorize.ts`) are wired, but the
  direct-on-leave/full-on-close flush is deferred.
- `Dashboard.tsx`/`pages/ScanOverview.tsx`/`scanHistory.ts`: superseded by LD's
  richer `pages/Overview.tsx`. Removed, not lost.
- Cosmetic `desktop/src/assets/linux-defender-logo.svg` (shield icon used
  instead) and `docs/issue-325-screenshots/*` (upstream issue-specific).
- Demo-repo scaffolding (`package.json`, `index.html`, demo `README.md`):
  not additive; recorded in `docs/clamui-fork/STATUS.md`.

## Compatibility contracts (do not rebrand away)

`clamui-apply-preferences`, `clamui-scheduled-scan`, `~/.config/clamui`,
`~/.local/share/clamui`, `~/.cache/clamui/privileged-staging`, `clamui.log*`,
the `clamui` Nautilus-script fallback, `uninstall.sh` pre-rename cleanup,
cron markers, and the `clamui-event` retired channel name. Each has dedicated
tests. Rebranding these breaks migration and upgrade compatibility.
