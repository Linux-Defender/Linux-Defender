# Linux Defender — ClamUI Fork

Linux Defender is a rebranded fork of [ClamUI](https://github.com/linx-systems/clamui),
a ClamAV-based desktop frontend. This folder documents the fork itself: why it
exists, what was ported from the ClamUI upstream, the rebrand state, and the
parity matrix.

- The upstream repository: <https://github.com/linx-systems/clamui>
- This product: <https://github.com/Linux-Defender/Linux-Defender>

## Why a fork?

ClamUI was deprecated upstream. Linux Defender continues the feature set — and
improves on it — while rebranding everything user-facing to **Linux Defender**.
All upstream repos/features referenced here are the [REPOS.md](./REPOS.md)
inventories.

## What was ported from ClamUI

| Area | Status |
|---|---|
| Rust core: audit module (`acknowledgements`, `opensnitch`, `firewall`, tests) | ✅ Ported |
| Rust core: `scanner/host_count.rs` | ✅ Ported |
| Rust core: `network.rs` (`listener_snapshot`, `listener_snapshot_from_output`) | ✅ Ported |
| Rust core: `privileged.rs` (helper install from local builds via pkexec) | ✅ Ported |
| Desktop: `accent_color.rs`, `clipboard.rs` (GTK) | ✅ Ported |
| Desktop: `Dashboard.tsx`, `ScanOverview.tsx`, new modules (`accentColor`, `configAuthorize`, …) | ✅ Ported |
| Packaging/distro: `snapcraft`, icons, `.gitar` policy, `install-nemo-actions.sh`, integrations | ✅ Ported |
| Translations: new/changed strings translated in `po/` (de done, others English fallback) | ⏳ In progress |

## Rebrand state

- Product name: **Linux Defender** (Tauri, CLI `linux-defender`).
- App ID: `io.github.linuxdefender.linuxdefender`.
- No references to `clamui`, `ClamUI`, `linx_systems`, or the upstream URLs as
  product names remain. Host-tool execution still references upstream ClamAV
  commands (`clamscan`, `clamdscan`, `freshclam`) — correct, since Linux Defender
  runs host-installed ClamAV.

## Parity matrix

See [docs/revival/RELATED-PROJECT-REVIEW.md](../revival/RELATED-PROJECT-REVIEW.md)
for the live ClamUI/ClamTk/Lenspect/Lensorreview parity matrix — status of each
upstream feature, whether ported, and why.
