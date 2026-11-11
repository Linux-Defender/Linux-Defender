# Source consolidation

This directory is the sole development checkout: `/home/kiras/Linux-Defender`. The app at the repository root is the one product UI. `reference/clamtk/` is the full ClamTk revival tree used to check behavior while features move into the Rust/Tauri/React app; it is not built or packaged as another application.

## Downloaded repositories accounted for

| Source | Snapshot included here | Integration status |
| --- | --- | --- |
| `SAFETY-CHAT/Linux-Defender` | This checkout; local branch `revival/unified-app` | Local work, not pushed. |
| `linx-systems/clamui` | Its Rust, Tauri, React, packaging, docs, and translations form the app at the repository root. Upstream base `32270d5`. | Selected as the single UI foundation. Product identity still says ClamUI in many assets. |
| Local `ClamUI-REBORN` | Its only source commit beyond ClamUI upstream, YARA rules commit `f648f9d`, is integrated here as `ec133dc`. | Its redundant checkout has no unique app source after that port. |
| `dave-theunsub/clamtk` | Base `694833d` is the parent of the active revival branch. | Its source is represented by the more complete ClamTk revival tree below. |
| `SAFETY-CHAT/clamtk-REBORN` | Active branch snapshot `4c55d73` under `reference/clamtk/`. Includes the local issue/PR code changes and integration modules. | Reference copy preserved; most features have not yet been ported to the Linux Defender UI. |
| ClamTk KDE/GNOME/Nemo/Thunar integrations, ClamUI forks/issues/PRs, and MidnightBSD packaging references | Findings are recorded in `RELATED-PROJECT-REVIEW.md` and `CLAMTK-ISSUE-PR-TRACKER.md`. | Reviewed as references; not all are merged or implemented. |

ClamTk issue/PR details and the exact reviewed snapshots are in the linked ledgers. The ClamTk branch includes fixes and integrations for scanner argument handling, path discovery, FreshClam controls, YARA, VirusTotal API v3, and urlscan. Only YARA is currently a ClamTk parity feature in the Linux Defender UI. ClamUI already supplies VirusTotal file scanning with keyring-backed credentials. urlscan is not yet a native Linux Defender feature. Do not describe the product as feature-complete.

## Cleanup status

Kira removed the four redundant checkout folders after the source inventory was consolidated here. The verified current development folder is `/home/kiras/Linux-Defender`. The preserved ClamTk and ClamUI source/history needed for the revival is represented in this repo as described above; generated build caches from the deleted checkouts are not required.
