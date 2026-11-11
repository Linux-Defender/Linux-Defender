# ClamTk revival issue and PR ledger

Review snapshot: 2026-11-10. Upstream: [dave-theunsub/clamtk](https://github.com/dave-theunsub/clamtk). Development checkout: `/home/kiras/ClamTk-REBORN`, branch `revival/issue-pr-triage`. Changes listed as local are not pushed or submitted upstream.

## Open issues (23)

| Issue | Finding / disposition | State |
|---|---|---|
| [#167](https://github.com/dave-theunsub/clamtk/issues/167) crash on close | Core dump points into Glib/GObject destruction and signal teardown; insufficient reproduction details to identify cause. | Open; not reproduced |
| [#164](https://github.com/dave-theunsub/clamtk/issues/164) missed cron scan when device is off | Cron does not catch up after downtime; an Anacron-like scheduler is a feature request. | Open; not implemented |
| [#163](https://github.com/dave-theunsub/clamtk/issues/163) maintainer retirement | Project status discussion, not a code defect. Kira's fork starts at the same upstream snapshot. | Context reviewed |
| [#159](https://github.com/dave-theunsub/clamtk/issues/159) not responding during scan | Clamscan can reload signatures; clamdscan is suggested where a daemon is available. Needs an optional backend/design and reproducible timing tests. | Open; not fixed |
| [#158](https://github.com/dave-theunsub/clamtk/issues/158) verbose scan log | Optional persistent all-file log; privacy, retention, and disk usage need product decisions. | Open; not implemented |
| [#149](https://github.com/dave-theunsub/clamtk/issues/149) invisible buttons in dark mode | Theme-specific screenshot report; no GUI reproduction available in this headless environment. | Open; not reproduced |
| [#147](https://github.com/dave-theunsub/clamtk/issues/147) toggle automatic DB update / scan on launch | The Assistant now exposes status, enable/disable, and run-now controls for Arch's `clamav-freshclam-once` system timer when that unit is installed. Scheduled scans remain a separate feature. | Local UI control added; system authorization and desktop behavior need CachyOS validation |
| [#146](https://github.com/dave-theunsub/clamtk/issues/146) discussion board | Repository hosting configuration request; community `clamtk/clamtk` has Discussions enabled. | Hosting-level, not app code |
| [#142](https://github.com/dave-theunsub/clamtk/issues/142) tray icon | Requires desktop-shell-specific status/tray support and distro coverage. | Open; not implemented |
| [#140](https://github.com/dave-theunsub/clamtk/issues/140) show scheduled scan time | Current upstream code already displays localized daily-scan status with a zero-padded time. | Appears addressed in code; issue remains open |
| [#139](https://github.com/dave-theunsub/clamtk/issues/139) ClamAV binary paths | `App.pm` now detects `clamscan`, `clamdscan`, `freshclam`, and `sigtool` in common locations or through `PATH`; it also recognizes `/etc/clamav/freshclam.conf`. | Fix committed `854f3e4`; helper tests cover custom `PATH` and missing tools; distro package cases still need validation |
| [#138](https://github.com/dave-theunsub/clamtk/issues/138) update UI glitches | PR #170 handles a redraw after update completion. Local change also checks FreshClam's exit status and leaves failures visible with a retry button. Reported Mint/XFCE layout still needs a GUI reproduction. | Local status fix committed `5ef5282`; GUI layout not verified |
| [#137](https://github.com/dave-theunsub/clamtk/issues/137) Cinnamon window controls | Old Cinnamon/GTK decoration behavior; not reproduced on target desktop. | Open; not reproduced |
| [#127](https://github.com/dave-theunsub/clamtk/issues/127) automatic update confusion | Assistant explains shared vs per-user signatures and now reports/manages the supported Arch daily FreshClam timer. | Clarification committed `7d0bd08`; new controls are local and still need CachyOS UI/auth validation |
| [#125](https://github.com/dave-theunsub/clamtk/issues/125) force quit / not responding | Older long-scan and signature-load reports overlap #159; not reproduced against current local versions. | Open; not fixed |
| [#124](https://github.com/dave-theunsub/clamtk/issues/124) VirusTotal integration | Replaced the source-embedded key in the working tree with a personal key stored through Secret Service, migrated lookups/uploads to API v3, added a confirmation before hash lookup plus a separate confirmation before file upload, and switched hashing to a streaming implementation. | Local implementation and mocked API/keyring tests pass; GUI and live API need desktop validation. The old key remains in inherited Git history and its owner should rotate it if still active. |
| [#121](https://github.com/dave-theunsub/clamtk/issues/121) Timeshift/hard links | Current scanner excludes directories named `timeshift`; general hard-link explanation/support is not added. | Reported scenario appears covered; broader request open |
| [#119](https://github.com/dave-theunsub/clamtk/issues/119) hard-coded source path | Old help request no longer matches current code, which uses `App->get_path`. | Stale against current source |
| [#91](https://github.com/dave-theunsub/clamtk/issues/91) Update Assistant confusion | Added explanatory mode-specific help in the Assistant. | UI clarification committed `7d0bd08`; not GUI-verified |
| [#68](https://github.com/dave-theunsub/clamtk/issues/68) high CPU during scan | Scan UI previously updated detail labels and requested redraw per scanner output line. Locally throttled detail refreshes to 10 Hz. Scanner invocation now uses direct argument passing rather than a shell command, preserving scan paths with spaces and shell metacharacters. | Local fixes; throttling committed `42c6f77`, argument hardening committed `a1f4e6e`; needs desktop CPU/GUI validation |
| [#53](https://github.com/dave-theunsub/clamtk/issues/53) duplicate quarantine names | Quarantine destination previously used only `basename`, allowing collisions and a failure path that could unlink the destination. Local fix now generates a content-specific unique storage name and keeps both restore records. | Local fix committed `b277d85`; 14 related tests pass |
| [#39](https://github.com/dave-theunsub/clamtk/issues/39) scheduled report in tray | Legacy desktop notification feature request. | Open; not implemented |
| [#36](https://github.com/dave-theunsub/clamtk/issues/36) bulk result actions | Blind bulk deletion risks false-positive damage; any batch action needs explicit selection and review. | Open; not implemented |

## Open pull requests (4)

| PR | Decision | State |
|---|---|---|
| [#168](https://github.com/dave-theunsub/clamtk/pull/168) clear icon selection on pointer leave | Cherry-picked exact change to local `lib/GUI.pm` (`ca6a727`); syntax checked, but no desktop GUI runtime available. | Local only; not submitted |
| [#169](https://github.com/dave-theunsub/clamtk/pull/169) reset FreshClam cooldown for PrivateMirror | Cherry-picked (`cd83510`) and added isolated tests (`5a81a5e`). Five tests pass; actual private mirror update not run. | Local only; not submitted |
| [#170](https://github.com/dave-theunsub/clamtk/pull/170) redraw update window after completion | Cherry-picked exact change (`7c27d2c`); syntax checked, GUI behavior not available here. | Local only; not submitted |
| [#141](https://github.com/dave-theunsub/clamtk/pull/141) scheduled time in status text | Not cherry-picked: current upstream already implements the requested status using a localized static message and padded time; PR version is older and less suitable for translation. | Redundant against current code |

## Local verification

- `prove -r t`: 70 tests pass across ten test files; coverage includes custom PATH discovery, literal scanner arguments, YARA-rule discovery, FreshClam timer status parsing, VirusTotal v3/keyring behavior, and urlscan privacy/validation behavior.
- `perl -Ilib -c lib/Scan.pm`: syntax OK.
- `lib/Assistant.pm` syntax check passes using a temporary staged module tree matching the installed Perl module layout.
- ClamAV 1.5.4 local smoke check loaded a test YARA rule alongside `/var/lib/clamav` and detected the matching harmless test string. No rule feed was downloaded.
- Optional urlscan submission now has a separate website page, Secret Service key storage, HTTP(S)-only URL validation, a Private-by-default selector, and explicit per-URL confirmation; API behavior is mocked in tests and no URL was submitted.
- PR-derived `GUI.pm` and `Update.pm` syntax checks passed earlier; GTK emitted sandbox dconf warnings.
- No GUI display is available, so visual behavior, dark themes, Cinnamon/Mint, and CPU impact on Kira's desktop remain unverified.
- Nothing has been pushed to GitHub. No system ClamAV database or services were modified.

## Fork network review

The GitHub forks API returned 55 forks. Compared each fork's default-branch head against upstream base `694833d`; most are identical to or behind that base. This is a default-branch/history comparison, not a review of every private or non-default branch.

| Fork | Finding | Disposition |
|---|---|---|
| [SAFETY-CHAT/clamtk-REBORN](https://github.com/SAFETY-CHAT/clamtk-REBORN) | Default branch is exactly upstream commit `694833d`; no unique changes yet. This is the user's fork. | Correct local starting point; revival work is on `revival/issue-pr-triage` |
| [clamtk/clamtk](https://github.com/clamtk/clamtk) | Same upstream code snapshot; README still says unmaintained. | No newer code to merge |
| [piposeimandi/clamtk](https://github.com/piposeimandi/clamtk) | Four commits ahead. Update UI rewrite points its version check to the fork and reports completion without checking the FreshClam exit status; removed earlier status/error paths. Other changes mostly move modules and update release metadata. | Reviewed; do not merge wholesale; selective fixes may be worthwhile after tests |
| [64BitUniverse/clamtk](https://github.com/64BitUniverse/clamtk) | Three commits of an unfinished PySide6/Python UI experiment; includes generated `__pycache__` binaries. | Not a drop-in fork; do not merge |
| [vitlav/clamtk](https://github.com/vitlav/clamtk) | Recently pushed, but default branch is exactly `694833d`; no unique code changes. | Nothing to merge |
| [datumbox/clamtk](https://github.com/datumbox/clamtk) | One 2020 commit ahead on a much older base; adds `Encrypted.PDF` as a clean scanner status. | Historical one-line change; inspect compatibility before any adoption |
| Other forks | Default branches were the same as or behind the upstream base; some are substantially behind. | No newer implementation identified in default-branch comparisons |
