# Linux Defender 0.6.0 — development snapshot

This branch adopts the upstream ClamUI v0.6.0 source baseline, then layers Linux Defender work on top. It is a development build; there are no signed Linux Defender release packages yet.

## Included

- Upstream v0.6.0 scan reliability and responsiveness improvements, including bounded history and quarantine views, complete large-scan findings, progress coalescing, long daemon-path handling, Flatpak host database detection, trusted helper checks, Wayland startup handling, Vietnamese translations, and current dependency locks.
- Local ClamAV scans with the configured host database, selected local YARA rules for standalone scans, scan profiles and options, quarantine, history, scheduling, security audit, tray and file-manager integrations.
- Explicit VirusTotal file, folder, and URL analysis with progress and confirmation, plus urlscan URL checks with visibility selection. These services receive data only after the user confirms; their findings are reputation results, separate from a local ClamAV verdict.
- A supported-database inventory and FreshClam status integration. The host package and service own the shared ClamAV definitions; Linux Defender does not yet install or maintain every third-party signature feed.
- The Linux Defender website and documentation source, rebranded for the SAFETY-CHAT repository.

## Before a public release

- Finish ClamTk feature and data migration, especially legacy preferences, history, scheduled scans, quarantine records, and restore behavior. The ClamTk reference implementation remains in the repository.
- Complete the app-ID, executable, desktop-file, and data-directory migration without overwriting existing ClamUI data. These compatibility identifiers are intentionally retained for now.
- Complete CachyOS desktop validation, package builds, and the full test suite. Prior focused checks passed, but prior runs still reported privileged-helper test failures and CLI integration hangs in this environment.
- Finish licensing and attribution review for the combined repository, verify release signing and update feeds, and provide real screenshots of the Linux Defender UI.

Do not treat this snapshot as a guarantee of complete ClamTk parity, support for every distribution, or comprehensive malware protection. No file or URL was submitted to VirusTotal or urlscan during development checks.
