# Chat and project coverage audit

Audit date: 2026-11-11. This consolidates Kira's requests in the Linux Defender revival chat with the current local checkout. Research counts and upstream state refer to the dated snapshots in the linked ledgers, not live GitHub status.

## What the project now contains

| Request | Current evidence | Status |
|---|---|---|
| Keep one project folder/app and remove duplicate checkouts | `/home/kiras/Linux-Defender` is the active checkout; the other four previously verified duplicate folders were removed by Kira. ClamTk's source/history is inside `reference/clamtk`; ClamUI is the one packaged UI foundation. | Consolidated locally; reference source intentionally remains in-repo. |
| Bring ClamTk and ClamUI together | Full ClamTk revival tree/history and selected ClamUI master history are present. ClamTk is a migration reference; ClamUI Rust/Tauri/React remains the runtime. | Partial feature migration; not a completed rewrite or feature-equivalent merge. |
| Keep tray behavior and compare left/right click | Candidate tray toggles the window on primary click and offers Show, Quick/Full Scan, Update, profiles, and Quit in the secondary-click menu. ClamTk had no tray implementation; issue #142 requests one. | Code present; KDE/GNOME click behavior not desktop-tested. |
| Combine desktop/file-manager actions | Dolphin, Nautilus, and Nemo actions come from ClamUI; Thunar Send To scan and VirusTotal actions have now been added to the Flatpak integration manager. Launchers pass `%F`; integration tests cover Thunar installation/removal and both action definitions. | Code/test coverage added; real multi-selection on each desktop remains unverified. |
| Keep ClamAV and automatic definition updates manageable | Host ClamAV/FreshClam own engine and shared definitions. ClamTk reference has controls for the known Arch/CachyOS FreshClam timer when installed. UI software updates remain the OS/package manager's job. | Partial; no universal auto-installer/updater, and no independent signature feed downloader. CachyOS service interaction needs desktop validation. |
| Merge other scanner engines, feeds, and safety tools | Local YARA rules are ported for standalone `clamscan`; arbitrary feeds are not auto-downloaded. `clamd` remains an optional host backend. Audit/firewall tools are separate from malware verdicts. | No multi-engine merger. No claim of complete protection. |
| Preserve VirusTotal and add urlscan | VirusTotal API v3 exists with keyring-backed credentials, mocked tests, and user consent in the existing flow. ClamTk reference includes urlscan handling, but it is not ported to Linux Defender. | VirusTotal local path exists; no live external submissions were made. urlscan is open. |
| Fix the listed issues and PRs | Point-in-time ClamTk review: 23 open issues and 4 open PRs. ClamUI review: 60 open and 12 closed issues, 2 open PRs. ClamTk fixes/PR dispositions are tracked; some fixes live only in the reference subtree. | Reviews and selected local fixes exist; not all issues are fixed, not all PRs applied, and nothing was submitted upstream. |
| Review all forks and history | Default branches and identified related repos were compared. The separate ClamUI revival checkout's YARA change is preserved as a branch and ported. | Not every historical commit/branch of every fork has been audited. |
| Support CachyOS/Arch and other Linux desktops | CachyOS setup/test steps are in `CACHYOS-TEST-SETUP.md`; compatibility plan covers distro packaging and GNOME/KDE/Wayland testing. | No release package or all-distro guarantee yet; desktop validation is still required. |
| Publish as Linux Defender | Git remote points to SAFETY-CHAT/Linux-Defender. Many app/package identifiers still say ClamUI; a public release also needs license/attribution review and inherited VirusTotal key/history handling. | Not release-ready; no push made. |

## Verification in this checkout

- `cargo fmt --check --all` passed.
- `cargo test -p clamui-core --test platform --locked`: 7 passed, including Thunar integration coverage.
- The frontend TypeScript check and Vite production build passed.
- Workspace run: desktop unit tests passed (17), core tests passed after excluding four host-dependent helper cases (103 passed, 1 ignored). The full run fails those four due this environment's filesystem/tool assumptions. With those skipped, multiple CLI subprocess tests remained running beyond 60 seconds, so the run was stopped before the remaining workspace suites.
- Earlier focused checks recorded in the project ledger: mocked VirusTotal tests 8 passed; translation checks passed for 10 locales / 1,275 messages.
- Not tested here: actual Linux Defender window, KDE/GNOME tray behavior, Thunar/Nautilus/Dolphin/Nemo menu interaction on Kira's CachyOS, live FreshClam timer actions, package installation, real VirusTotal/urlscan requests, or a real malware sample. The EICAR/YARA smoke result in the tracker is a harmless local fixture test, not a guarantee of detection coverage.

## Next work, in order

1. Run the app on Kira's CachyOS desktop; verify tray left/right click, file-manager actions and multi-select, FreshClam status/update controls, themes, and scan/update errors.
2. Resolve the four test environment assumptions and the CLI subprocess test hang; rerun all workspace checks without skips.
3. Port and validate the highest-impact ClamTk issue fixes into the one runtime, starting with data migration, update/scheduler clarity, and scan responsiveness. Keep issue and PR dispositions in the tracker.
4. Implement urlscan only with explicit privacy/visibility choices and tests; retain VirusTotal confirmation and never send files/URLs during automated tests.
5. Rename package/app/CLI identity, complete license and secret-history review, build the CachyOS/Arch package, then add distro CI before any public release.

Supporting evidence: [issue/PR tracker](CLAMTK-ISSUE-PR-TRACKER.md), [related project review](RELATED-PROJECT-REVIEW.md), [source consolidation](SOURCE-CONSOLIDATION.md), and [CachyOS setup](CACHYOS-TEST-SETUP.md).
