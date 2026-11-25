---
name: linux-defender-integrations
description: Maintain Linux Defender's native and external integrations — file-manager actions (Nautilus/Nemo/Dolphin/Thunar), tray/D-Bus, privileged host ClamAV, safe open/export/clipboard helpers, VirusTotal/urlscan, and scheduled scans. Use when changing integration assets, packaging, IPC boundaries, or when auditing "integrations".
---

# Linux Defender integrations

Integrations are the seams between Linux Defender and the host desktop/ClamAV.
They are security-sensitive: keep every crossing narrow, explicit, and tested.

## Inventory

| Integration | Owner | Notes |
|---|---|---|
| File-manager actions | `data/`, `assets/integrations-native/`, `crates/linux-defender-core/assets/integrations/`, `scripts/install-nemo-actions.sh`, `scripts/linux-defender-*-nautilus.sh`, `crates/linux-defender-core/src/platform.rs` | Nautilus scripts, Nemo actions, Dolphin `.desktop`; pre-rename `clamui` launcher fallback is a compatibility contract. |
| Tray / D-Bus | `desktop/src-tauri/src/tray.rs`, `crates/linux-defender-core/src/platform.rs` | Rust SNI/DBusMenu; no Python tray runtime. |
| Host ClamAV | `crates/linux-defender-core/src/{scanner,host,host_probe,updater,urlhaus}.rs` | `clamscan`, `clamdscan`, `freshclam`; Flatpak uses `flatpak-spawn --host`. Never bundle an engine or database. `scripts/check-signatures.py` verifies database age and EICAR detection; `scripts/check-signature-feeds.py` verifies the product-default URLhaus export with the Auth-Key redacted; the `Signature Database` workflow runs both weekly. |
| Privileged helper | `crates/linux-defender-core/src/privileged.rs`, `data/*.policy`, `debian/*helper*`, `rpm/` | protocol-v4, destination allowlists, `PKEXEC_UID`; pre-rename helper path accepted. |
| Native open/export/clipboard | `desktop/src-tauri/src/runtime.rs` (`open_with_desktop`, `save_export`, `copy_text`) | Explicit user requests only; snap routes `xdg-open` through the host environment. |
| Online reputation | `crates/linux-defender-core/src/{virustotal,urlscan,network}.rs`, `desktop/src/pages/Scan.tsx`, `Urlscan.tsx` | Explicit submission; keys stay in the OS keyring, never in settings/errors/logs. |
| Scheduling | `crates/linux-defender-core/src/scheduler.rs`, `desktop/src/pages/Preferences.tsx` | systemd user timers or cron; snap/AppImage/Flatpak launchers are revision-independent. |

## Rules

1. **No new runtime dependencies.** Do not add Python/GTK application code or
   a second tray implementation. All behavior lands in the Rust core or Tauri.
2. **Validate at the Rust boundary.** Frontend checks are UX, not authorization.
   Paths, URLs, operation IDs, and value bounds are sanitized in Rust before
   any host command, IPC reply, or persistence.
3. **Scoped host execution.** Use `common::host_command`/`watched_host_command`.
   They strip host-library transform variables, Flatpak/snap/AppImage leakage,
   and snap runtime variables so the host's ClamAV/Polkit tools run cleanly.
4. **Asset parity.** When adding/changing an integration, update every relevant
   location: `data/`, `assets/integrations-native/`, `crates/linux-defender-core/assets/integrations/`, `scripts/` Nautilus helpers, and
   the Rust `include_bytes!` in `platform.rs`. Keep the rebranded IDs:
   `io.github.linuxdefender.linuxdefender`.
5. **Test the integration.** Add tests beside `platform.rs`/`privileged.rs`
   (asset bytes, trusted-path checks, staging containment) and verify the
   generated desktop files with `msgfmt`/desktop-file tooling where relevant.
6. **Document changes.** Update `docs/clamui-fork/STATUS.md` and the published
   configuration/integration docs under `website/src/content/docs/docs/`.

## Validation

```bash
cargo test -p linux-defender-core --test platform
cargo test -p linux-defender-core --test privileged
cargo test -p linux-defender-core --test snap
bash scripts/audit-consistency.sh
```

Legacy identifiers in these integrations (`clamui` fallback, pre-rename
desktop names, `.cache/clamui/privileged-staging`) are accepted only under the
same root-owned/immutable trust checks and have dedicated tests. Do not remove
them before their migration contract is retired.
