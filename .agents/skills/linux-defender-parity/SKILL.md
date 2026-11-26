---
name: linux-defender-parity
description: Audit Linux Defender for upstream ClamUI/ClamTk parity, cross-file consistency, dead code, stale branding, and CI sync. Use when porting upstream work, reviewing a change, before release, or when asked to "check parity", "audit everything", "find dead/stale code", "make sure nothing is forgotten", or "verify sync".
---

# Linux Defender parity and consistency audit

Use this skill whenever work touches more than one boundary (Rust core, Tauri
runtime, React frontend, translations, docs, packaging, or CI), when porting a
ClamUI/ClamTk/Lenspect behavior, or before saying a task is done.

## Authoritative records

- `docs/revival/README.md` — index of ALL revival research (ClamUI, ClamTk, Lenspect), including the canonical link-checked `docs/revival/UPSTREAM-REPOSITORIES.md` inventory.
- `docs/revival/CHAT-AND-PROJECT-AUDIT.md` — consolidated revival-chat requirement ledger; every request in the conversation with its satisfaction evidence.
- `docs/revival/RELATED-PROJECT-REVIEW.md` — the live upstream parity matrix
  (repository, reviewed commit/date, issue/PR ids, implemented/deferred/open).
- `docs/clamui-fork/STATUS.md` — what was ported from ClamUI, what is
  deliberately deferred (scanner concurrency, full Flush UI), and what was
  superseded (Dashboard/ScanOverview/scanHistory). Update it when porting.
- `AGENTS.md` — canonical contributor rules (security, IPC, compatibility,
  build/test, Claude/Cursor/Aider/Continue/Zed guidance).
- `AI-ENFORCEMENT.md` — mandatory rules injected into every model context.
- `scripts/cross-layer-contracts.json` — declarative cross-layer feature matrix.
- `scripts/check-all.sh` — single source of truth for all static checks.

## Audit checklist (run all, in order)

1. **Static checks then full audit.** Run `bash scripts/check-all.sh` and fix
   every failure, then `bash scripts/audit-consistency.sh` for builds, clippy,
   tests, git sync, and GitHub Actions status. `check-all.sh` is enforced by the
   pre-commit hook, the pre-push hook runs the full audit, and Consistency Audit
   CI runs both. Never declare done while either fails. `cargo test --workspace
   --locked` passes in full; the GTK clipboard test (needs `xvfb-run`) and the
   signed-RPM bootstrap test (needs a built signed helper RPM) are ignored by
   design, so do not report them as failures.
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
   (`de en es fr hu it nb pt_BR vi zh_CN`). A new IPC operation must exist on
   both sides of the dispatcher; `scripts/check-ipc-operations.py` joins every
   literal `request("domain.action")` under `desktop/src` with the
   `domain -> module::dispatch` table and each module's handled actions, so a
   renamed or misspelled operation fails here instead of at runtime.
5. **Dead code.** Every ported frontend module must be imported by a live
   caller or removed/superseded. Use the dead-module section of the audit
   script. Rust dead code is caught by `cargo clippy -- -D warnings`.
6. **Stale references.** The audit script greps for
   `clamui.com|linx.systems|clamui@|rooki.xyz|io.github.linx`. Only intentional
   historical/compat references (docs/revival, docs/clamui-fork, CHANGELOG,
   LICENSE, migration constants and their tests) are allowed.
6b. **Dead links and dead files.** `scripts/check-doc-links.py` fails on broken
   relative links in every Markdown/MDX file; `scripts/check-dead-files.py`
   fails on orphaned docs, modules, and skills. Link every new doc from an
   existing index and import every new module from a live caller.
6c. **Cross-layer feature matrix.** Any new cross-cutting feature (e.g. a new
   scanner backend, online service, or config area) must get an entry in
   `scripts/cross-layer-contracts.json` listing every layer that consumes it.
   `scripts/check-cross-layer.py` also derives Tauri commands, CLI subcommands,
   and locales from source and asserts they are wired in all consuming layers.
6d. **Whole-repo consistency.** `scripts/check-repo-consistency.py` asserts the
   version agrees across the workspace manifest, Tauri crate, desktop package,
   AppStream metadata, and Flatpak release notes; that the public app id is used
   in every package format; and that every workflow and maintenance script is
   referenced somewhere. `scripts/check-dead-files.py` now covers all tracked
   files, not just a few directories.
6e. **Signature database health.** `scripts/check-signatures.py` verifies the
   host ClamAV database is present, current, and detects EICAR;
   `scripts/check-signature-feeds.py` verifies the product-default URLhaus
   export with the Auth-Key redacted. The host engine and signature database
   are never bundled. The `Signature Database` workflow runs these weekly.
6f. **External upstream links.** `scripts/check-upstream-urls.py` verifies every
   URL in `docs/revival/UPSTREAM-REPOSITORIES.md`; a 404 fails the check. Fix
   dead links at the source and keep the inventory the single canonical list.
   `scripts/check-external-links.py` extends this to every external link in all
   tracked Markdown/MDX (code examples and imported skills excluded; 403 fails; repeated 429/5xx are
   retried then skipped); it runs in the full audit and in the weekly `Doc Links`
   workflow. `scripts/check-stale-phrases.py` fails when any of the stale
   claims listed in that script (wrong translation status, a misspelled
   project name, the old repository-inventory path) reappear in live docs.
   `scripts/check-doc-indexes.py` requires every internal document to be linked
   from its folder index, so no document can be forgotten. The generated
   `docs/DOC-MAP.md` links every tracked document; run
   `python3 scripts/generate-doc-map.py` after adding/removing docs, and
   `--check` enforces this in `check-all.sh`.
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
10. **Website exercise.** For site changes, run `bun run --cwd website dev` or
    `preview`, open the home page and a docs page with no console errors, and
    run Lighthouse on the production preview (dev toolbar skews SEO link-text).
    `scripts/audit-consistency.sh` checks build, links, sidebar targets, and
    unused components; current production baseline is 1.0 accessibility,
    1.0 best practices, 1.0 SEO.

## Fail-closed guards (how to add one)

A drift fixed by hand comes back. Every audit finding gets a permanent check
instead. To add one:

1. Write `scripts/check-<topic>.py` (`from __future__ import annotations`,
   a docstring explaining the drift it prevents, `git ls-files` for the tracked
   set, an actionable failure message on stderr, exit 1, and one OK line).
2. Wire it into `scripts/check-all.sh`, the single source of truth. A checker
   that no gate invokes fails `scripts/check-gate-wiring.py`, and so does a gate
   that names a missing script.
3. List it in `docs/documentation/SCRIPTS.md`; `check-scripts-index.py` enforces
   the index.
4. Negative-test it: force the drift, confirm exit 1, restore the tree.
5. If it protects a stale *claim*, add the old wording to
   `scripts/check-stale-phrases.py`.
6. Record the finding and the guard in
   `docs/revival/CHAT-AND-PROJECT-AUDIT.md`.

| Guard | Drift it blocks |
|---|---|
| `check-gate-wiring.py` | a checker no gate runs, or a gate naming a deleted script |
| `check-file-modes.py` | a shebang script or Debian maintainer script losing `100755` |
| `check-source-invariants.py` | URLhaus draft auto-applied, retired `clamui-event` channel, CSP relaxation |
| `check-ipc-operations.py` | frontend `request("domain.action")` missing from the core dispatcher, or a direct `invoke` disagreeing with `generate_handler!` |
| `check-translations.sh` | documented catalog count disagreeing with the real catalogs |
| `check-integration-parity.py` | integration assets/copies drifting or losing the exec bit |
| `check-packaging-consistency.py` | AUR source pin not an ancestor of HEAD, or format drift |
| `check-stale-phrases.py` | a corrected stale claim reappearing |
| `check-cross-layer.py` | Tauri command, CLI subcommand, locale, or feature-matrix drift |
| `check-doc-links.py` / `check-dead-files.py` / `check-doc-indexes.py` | dead links, orphan files, unreachable docs |

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
and cron markers. Each active identifier has dedicated tests. The
`clamui-event` channel name is retired (historical references only; no runtime
code or test depends on it). Do not rebrand the active contracts away.
