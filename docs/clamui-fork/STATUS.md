# ClamUI Fork — Status

Written so a successor can continue without loss. As of `9579181`.

## Completed

| Work | Detail |
|---|---|
| **Rust core port** (audit refactor) | `crates/linux-defender-core/src/audit.rs`, `audit/firewall.rs`, `audit/opensnitch.rs`, `audit/acknowledgements.rs`, `audit/tests.rs`, `scanner/host_count.rs` — from upstream `clamui-core/`. `network.rs` `listener_snapshot*` ported. `privileged.rs` gets dev-build helper install via pkexec. |
| **Desktop port** | `accent_color.rs`, `clipboard.rs` (GTK) wired; `Dashboard.tsx`, `ScanOverview.tsx` pages; modules `accentColor.ts`, `configAuthorize.ts`, `configDraft.ts`, `initialMountedPages.ts`, `pageId.ts`, `pathList.ts`, `savePlan.ts`, `scanHistory.ts`, `ScanProgressPanel.tsx`; tests in `desktop/tests/`. |
| **Desktop wiring** | `main.rs` (module decls), `runtime.rs` (`manage(AccentColor)`, `accent_color::init` in setup, `startup.accent`), `model.rs` (`StartupState.accent`), `Cargo.toml` (deps: `gtk`, `tokio`, `zbus`, `futures-util`), `clipboard`-based `copy_text` on Linux. |
| **Distro/packaging** | `snap/` (snapcraft), `icons/`, `.gitar/` policy, `scripts/install-nemo-actions.sh`, `data/` WebExtensions, `website/public/CNAME`, screenshots. |
| **Docs** | `docs/clamui-fork/` (README, REPOS), `docs/documentation/`, `docs/README.md`, `docs/translations/`. |
| **Validation (all green)** | `cargo fmt --check`, `cargo clippy -- -D warnings`, `cargo test` (163), `bun check/build/test` (28), `check-translations.sh`, `msgcmp` |

## Blocked (Translations CI fails)

`update-pot.sh --check`: POT stale — the audit refactor added 32 new strings not in
the catalogs (see [`../../po/MISSING_TRANSLATIONS.txt`](../../po/MISSING_TRANSLATIONS.txt)).

- German translations of those 32 are documented there (from `/tmp/translations.json`).
- es/fr/hu/it/nb/pt_BR/vi/zh_CN need them too; English fallback is acceptable.
- Recipe + polib instructions: [`docs/translations/README.md`](../translations/README.md).

## Known-good end state

```sh
./scripts/update-pot.sh && for l in de en es fr hu it nb pt_BR vi zh_CN; do
  msgmerge --update po/$l.po po/linux-defender.pot
done
# fill new entries with translations (see docs/translations/README.md)
./scripts/update-pot.sh --check && ./scripts/check-translations.sh
```

## Notes for the next model

- The committed catalogs pass `check-translations.sh` (the active catalogs contain all
  of the OLD strings; the POT is ahead). Do NOT regenerate the catalogs with msgmerge
  blindly — `msgattrib --no-obsolete --no-fuzzy` first if needed, and `msgfmt -c` after.
- The `/tmp/translations.json` on this machine is a backup of the German translations.
- Hand-rolled PO editors have been tried and are unreliable; use polib or regenerate.
