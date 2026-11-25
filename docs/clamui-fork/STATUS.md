# ClamUI Fork — Status

Written so a successor can continue without loss.

## Completed

| Work | Detail |
|---|---|
| **Rust core port** (audit refactor) | `crates/linux-defender-core/src/audit.rs`, `audit/firewall.rs`, `audit/opensnitch.rs`, `audit/acknowledgements.rs`, `audit/tests.rs`, `scanner/host_count.rs` — from upstream `clamui-core/`. `network.rs` `listener_snapshot*` ported. `privileged.rs` helper install via pkexec + ancestor-chain local-tool validation. |
| **Snap runtime support** | `common.rs` `is_snap()`/`snap_root()`/`without_snap_entries()` + host-command snap-variable stripping; `scheduler.rs` `is_snap_scheduled_scan_command`/`snap_launcher_command`; `runtime.rs` `open_with_desktop` snap xdg-open routing; `tests/snap.rs`; `.github/workflows/build-snap.yml`; `snap/local/linux-defender-launch`. |
| **Config elevation probe** | `config.rs` `config.needs_elevation` dispatch action (`needs_elevation_check`) matching upstream. |
| **Stability** | `host_probe.rs` `reap_limited_child()` — off-thread child reaping so a stuck host command never blocks the request thread. |
| **Desktop port** | `accent_color.rs`, `clipboard.rs` (GTK), `Dashboard`/`ScanOverview` superseded by LD's `Overview`; modules `accentColor.ts`, `configAuthorize.ts`, `configDraft.ts`, `initialMountedPages.ts`, `pageId.ts`, `pathList.ts`, `savePlan.ts`, `ScanProgressPanel.tsx` — all wired; tests in `desktop/tests/`. |
| **Desktop wiring** | `main.rs`, `runtime.rs` (accent + clipboard + snap opener), `model.rs` (`StartupState.accent`), `Cargo.toml` deps. |
| **Packaging/distro** | `snap/`, `icons/`, `scripts/install-nemo-actions.sh`, `data/` WebExtensions, screenshots, `.github/FUNDING.yml`, `build-snap.yml`, `flathub/cargo-sources.json` refreshed for cookie 0.18.3. |
| **Translations** | POT regenerated; all 10 catalogs merged with all source messages and passing `check-translations.sh`, `msgcmp`, `msgfmt -c`, `update-pot.sh --check`. Human review of remaining identical-English candidates is open (`po/TRANSLATION-REVIEW.md`). |
| **Docs** | `docs/clamui-fork/` (README, STATUS; the former REPOS inventory now lives in `docs/revival/UPSTREAM-REPOSITORIES.md`), `docs/documentation/`, `docs/README.md`, `docs/translations/`, `po/MISSING_TRANSLATIONS.txt`. |
| **Packaging matrix** | All six formats are checked together by `scripts/check-packaging-consistency.py` (version, rebranded app id, workflow, README badge, helper path, host-ClamAV boundary, release asset patterns): DEB (app + helper), RPM (helper), AppImage, Flatpak, Snap, and AUR (app + helper). Host-tool component guides are aligned between app and website and checked against the reviewed upstream snapshot by `scripts/check-host-tool-guidance.py`; `Build AUR` is a standalone peer of `Build Snap`/`Build Debian Package`; `Build All Packages` calls all six build workflows, `check-integration-parity.py` verifies format-correct launcher variants, and `Packaging Sync` runs weekly. None of the formats bundle an engine or signature database. |
| **Arch/AUR + Sway support** | `aur/PKGBUILD` + `aur/linux-defender-privileged-helper/PKGBUILD` + generated `.SRCINFO` build the Rust/Tauri app, scheduled-scan CLI, and version-matched root-owned helper from one pinned source commit; rebranded assets and ten gettext catalogs installed; host ClamAV/database never bundled; Sway/wlroots tray and portal `optdepends` documented in the installation and tray guides; `scripts/check-packaging-consistency.py` enforces all six formats in `check-all.sh`; reference `Estemobs/aur-clamui` reviewed and independently reimplemented, not copied. Not published to the AUR, and no Sway desktop validation claim. |
| **Agent tooling** | `linux-defender-parity` + `linux-defender-integrations` skills; `scripts/check-all.sh` single source of truth for static checks and `scripts/audit-consistency.sh` full audit; pre-commit/pre-push hooks and `.github/workflows/consistency.yml` enforce them; `scripts/cross-layer-contracts.json` + `check-cross-layer.py` enforce feature parity across layers; `check-repo-consistency.py` enforces version/app-id/inventory agreement; `check-signatures.py` + `check-signature-feeds.py` and the `Signature Database` workflow verify host database, EICAR, and the product-default URLhaus feed (key redacted, nothing bundled); `AI-ENFORCEMENT.md` injected via tool adapters and `.claude/settings.json`, with git hooks and CI as the tool-neutral path; `Upstream Freshness` workflow auto-detects skill drift; imported skills locally adapted; `AGENTS.md` / `CLAUDE.md` / `CONTEXT.md` updated for all assistants (Claude, OpenCode, Cursor, Aider, Continue, Zed). |
| **Validation** | `cargo fmt/clippy/test`, `bun check/build/test`, and `bash scripts/audit-consistency.sh` pass. Historical counts and environment-dependent helper/CLI failures are recorded in `docs/revival/CHAT-AND-PROJECT-AUDIT.md`; they are not re-claimed as passing here. |

## Deliberate deferral (documented, not forgotten)

`crates/linux-defender-core/src/scanner.rs`: upstream added concurrent daemon
scan sharding (`run_daemon_file_lists`, `daemon_worker_count`,
`merge_daemon_worker_outputs`, `combined_clamdscan_exit_code`) and cumulative
multi-target progress (`ProgressReporter` fields). This is a ~760-line behavioral
change in a scanner that has **diverged** from upstream (LD adds YARA rules,
engine options in profiles, Thunar integration). Porting it blindly risks scan
correctness regressions in an antivirus engine, so it is intentionally deferred.
The upstream-independent scan features in LD are preserved and tested.

Also intentionally not ported: cosmetic `desktop/src/assets/linux-defender-logo.svg`
(LD uses the shield icon in `App.tsx`), and `docs/issue-325-screenshots/*` (upstream
issue-specific screenshots).

Upstream's **autosave/batched "Flush" flow** remains deliberately deferred as a
full UI change: `ConfigPreferences.tsx` still uses the explicit **Save & Apply**
button, not upstream's direct-on-section-leave/full-on-close flush. However the
shared helpers are now **live and tested**: `savePlan.ts` (`pendingProposals`)
computes the Save & Apply proposals, `configDraft.ts` supplies the dirty check,
`configAuthorize.ts` (`mergeAuthorizedConfig`) fixes issue #343 so authorizing a
config read no longer discards unsaved edits, `pathList.ts` handles URL-list
drafting, `accentColor.ts` applies the native system accent, and
`ScanProgressPanel.tsx` renders live scan progress. `CONTEXT.md` therefore still
documents "Save & Apply", not "Flush".

`Dashboard.tsx`, `pages/ScanOverview.tsx` and `scanHistory.ts` were **removed**:
upstream's Dashboard is a thin wrapper around `ScanOverview`, but Linux Defender
has an independent, richer `pages/Overview.tsx` that serves the same role with
its own history handling. Nothing referenced them; their tests covered only the
removed helper. Superseded, not lost.

## Docs adopted from upstream (rebranded)

- `AGENTS.md`: "Security first" (least privilege, CSP/navigation, IPC trust
  boundary, scoped native access, isolation), "Native commands and state", and
  "Release builds and dependency hygiene" sections.
- `CONTRIBUTING.md`: git-hooks install step (`./scripts/hooks/install-hooks.sh`).
- `.github/workflows/auto-assign.yml` from the Linux-Guardians org demo repo.
- `README.md`: CI status badges (org demo pattern), adapted to our workflows.

The demo repo's `package.json`/`index.html`/demo `README.md`/`proof-html.yml` were
reviewed and intentionally not copied: they are demo scaffolding, redundant with
our real manifests/site link checker, or would duplicate our project README.

## Compatibility contracts (kept deliberately, per AGENTS.md)

Legacy identifiers — `clamui-apply-preferences`, `clamui-scheduled-scan`,
`~/.config/clamui`, `~/.cache/clamui/privileged-staging`, `clamui.log*`, the
`clamui` Nautilus-script fallback, `uninstall.sh` pre-rename cleanup, and
`Scheduler` cron markers — are retained only as compatibility/migration
contracts with dedicated tests. Do not "rebrand" these.

## Notes for the next model

- All catalog checks pass; `./scripts/check-translations.sh` is the gate.
- `/tmp/translations.json` is a backup of the German translations used.
- Hand-rolled PO editors are unreliable; prefer `polib` or the documented recipe.
- CI: all workflows green; keep it that way by running `cargo fmt --check`,
  `cargo clippy -- -D warnings`, `cargo test`, `bun check/build/test`, and the
  i18n scripts before committing.
