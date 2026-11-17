# Source consolidation

This directory is the sole development checkout: `/home/kiras/Linux-Defender`. The app at the repository root is the one product UI. The ClamTk Perl reference tree (`reference/clamtk/`) was retired on 2026-11-16 after its behavior parity was captured in this directory; ClamTk behavior and remaining gaps are documented in [CLAMTK-ISSUE-PR-TRACKER.md](CLAMTK-ISSUE-PR-TRACKER.md) and [RELATED-PROJECT-REVIEW.md](RELATED-PROJECT-REVIEW.md).

## Downloaded repositories accounted for

| Source | Snapshot included here | Integration status |
| --- | --- | --- |
| `Linux-Defender/Linux-Defender` | Public repository; `main` contains merged PR #1 and the latest local topic branch is based on current `main` | The current local branding/update pass is not yet pushed; no Linux Defender release is published. The main branch also has competing GitHub Pages workflows that need a maintainer choice. |
| `linx-systems/clamui` | Its Rust, Tauri, React, packaging, docs, and translations form the app at the repository root. Upstream base `32270d5`. | Selected as the single UI foundation. Product identity still says ClamUI in many assets. |
| Local `ClamUI-REBORN` | Its only source commit beyond ClamUI upstream, YARA rules commit `f648f9d`, is integrated here as `ec133dc`. | Its redundant checkout has no unique app source after that port. |
| `dave-theunsub/clamtk` | Base `694833d` is the parent of the active revival branch. | Its source is represented by the more complete ClamTk revival tree below. |
| `Linux-Defender/clamtk-REBORN` (formerly SAFETY-CHAT) | Branch snapshot `4c55d73` was the retired `reference/clamtk/` tree. The unique research log is preserved as [CLAMTK-RESEARCH.md](CLAMTK-RESEARCH.md); the repository itself is not published. | Reference snapshot retired after parity capture; behavior and remaining gaps stay documented here. |
| ClamTk KDE/GNOME/Nemo/Thunar integrations, ClamUI forks/issues/PRs, and MidnightBSD packaging references | Findings are recorded in `RELATED-PROJECT-REVIEW.md` and `CLAMTK-ISSUE-PR-TRACKER.md`. | Reviewed as references; not all are merged or implemented. |

ClamTk issue/PR details and the exact reviewed snapshots are in the linked ledgers. The ClamTk branch includes fixes and integrations for scanner argument handling, path discovery, FreshClam controls, YARA, VirusTotal API v3, and urlscan. Linux Defender has ported local YARA rule loading and now offers VirusTotal URL analysis plus urlscan in the Website URL mode beside file scanning. ClamUI's VirusTotal file scanning remains available with keyring-backed credentials. The system's ClamAV/FreshClam database remains the local engine's signature set; third-party feeds are not managed, and urlscan/VirusTotal are remote services. URL scanning requires real desktop/keyring validation; many other ClamTk features still need parity work. Do not describe the product as feature-complete.

## Cleanup status

Kira removed the four redundant checkout folders after the source inventory was consolidated here. The verified current development folder is `/home/kiras/Linux-Defender`. The preserved ClamTk and ClamUI source/history needed for the revival is represented in this repo as described above; generated build caches from the deleted checkouts are not required.
