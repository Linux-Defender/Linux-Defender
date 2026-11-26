# Linux Defender — ClamUI Fork

Linux Defender is a rebranded fork of [ClamUI](https://github.com/linx-systems/clamui),
a ClamAV-based desktop frontend. This folder documents the fork itself: why it
exists, what was ported from the ClamUI upstream, the rebrand state, and the
parity matrix.

- The upstream repository: <https://github.com/linx-systems/clamui>
- This product: <https://github.com/Linux-Defender/Linux-Defender>

## Why a fork?

Linux Defender continues the ClamUI feature set — and improves on it — while
rebranding everything user-facing to **Linux Defender**. The upstream project
remains available for reference; it is not a second application shipped here.
All upstream repos/features referenced here are listed in the canonical
[upstream repository inventory](../revival/UPSTREAM-REPOSITORIES.md), which
covers ClamUI, ClamTk, Lenspect, their plugin repos, and the ClamAV bytecode compiler.

## What was ported from ClamUI

| Area | Status |
|---|---|
| Rust core: audit module (`acknowledgements`, `opensnitch`, `firewall`, tests) | ✅ Ported |
| Rust core: `scanner/host_count.rs` | ✅ Ported |
| Rust core: `network.rs` (`listener_snapshot`, `listener_snapshot_from_output`) | ✅ Ported |
| Rust core: `privileged.rs` (helper install from local builds via pkexec) | ✅ Ported |
| Desktop: `accent_color.rs`, `clipboard.rs` (GTK) | ✅ Ported |
| Desktop: new modules (`accentColor`, `configAuthorize`, `configDraft`, `savePlan`, `ScanProgressPanel`, …) | ✅ Ported and wired |
| Desktop: upstream `Dashboard.tsx` / `ScanOverview.tsx` / `scanHistory.ts` | Superseded by Linux Defender's richer `Overview` and removed; see [STATUS.md](STATUS.md) |
| Packaging/distro: `snapcraft`, icons, `.gitar` policy, `install-nemo-actions.sh`, integrations | ✅ Ported |
| Translations: POT and all 10 active catalogs (`de en es fr hu it nb pt_BR vi zh_CN`) kept in sync; human review of remaining untranslated entries is open | ✅ Synced, review open |

## Rebrand state

- Product name: **Linux Defender** (Tauri, CLI `linux-defender`).
- App ID: `io.github.linuxdefender.linuxdefender`.
- No `clamui`, `ClamUI`, `linx_systems`, or upstream URL is used as a **user-facing
  product name**. Compatibility identifiers (`clamui-apply-preferences`, the
  pre-rename config/data paths, `clamui.log*`, cron markers, Nautilus fallbacks)
  are deliberately retained with tests; see
  [STATUS.md](STATUS.md). Host-tool execution references ClamAV commands
  (`clamscan`, `clamdscan`, `freshclam`) — correct, since Linux Defender runs
  host-installed ClamAV.

## Parity matrix

See [docs/revival/RELATED-PROJECT-REVIEW.md](../revival/RELATED-PROJECT-REVIEW.md)
for the live ClamUI/ClamTk/Lenspect parity matrix — status of each
upstream feature, whether ported, and why.
