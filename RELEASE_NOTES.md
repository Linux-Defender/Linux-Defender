# Linux Defender 0.6.0 — development snapshot

This branch builds on the upstream v0.6.0 Rust/Tauri/React source baseline, then adds Linux Defender work. It is a development build; there are no signed Linux Defender release packages yet.

Distribution note: draft release assets currently include DEB (app + helper), the signed RPM helper, and the signed AppImage. Flatpak and Snap are built and verified by CI (including on `v*` tags and in `Build All Packages`) but are not attached as release assets; neither has a published remote or store yet. Source recipes and per-format READMEs are in the repository.

## Included

- Upstream v0.6.0 scan reliability and responsiveness improvements, including bounded history and quarantine views, complete large-scan findings, progress coalescing, long daemon-path handling, Flatpak host database detection, trusted helper checks, Wayland startup handling, and current dependency locks. Vietnamese (`vi`) is active in both desktop and CLI catalogs.
- Upstream native build maintenance: Debian, RPM, and AppImage CI uses authenticated HTTPS Ubuntu Jammy mirrors and fails on repository update errors while retaining the Ubuntu 22.04 baseline, dependencies, and package signing.
- Local ClamAV scans with the configured host database, selected local YARA rules for standalone scans, scan profiles and options, quarantine, history, scheduling, security audit, tray and file-manager integrations.
- Explicit VirusTotal file, folder, and URL analysis with progress and confirmation, plus urlscan URL checks with visibility selection. VirusTotal and urlscan.io API keys can both be managed from Preferences. These services receive data only after the user confirms; their findings are reputation results, separate from a local ClamAV verdict.
- A supported-database inventory and FreshClam status integration. The host package and service own the shared ClamAV definitions; Linux Defender does not yet install or maintain every third-party signature feed.
- The canonical application identity is now `linux-defender` for the GUI and CLI, including `linux-defender-cli`, `linux-defender-scheduled-scan`, `/usr/bin/linux-defender-apply-preferences`, the event channel, keyring service, systemd units, logs, scheduler caches, and desktop integration. Pre-rename `clamui*` executables, units, cron entries, keyring entries, and `~/.config/clamui`/`~/.local/share/clamui` data are still read as compatibility aliases during upgrade.
- The Linux Defender website and documentation source, rebranded for the Linux-Defender repository, with validated upstream website dependency updates.
- The Guardian visual identity across the app, brand marks, and website: ink and paper surfaces with a single safety-green accent, documented in `docs/DESIGN.md`.
- An Overview dashboard that opens on launch and stays reachable with `Ctrl+0`: protection posture, all-time totals, engine and definition checks, the quarantine count, and quick actions into the existing views.
- The upstream updater inactivity fix, including a configurable timeout, UI, regression coverage, and updated docs/catalogs.

## Before a public release

- Finish ClamTk feature and data migration, especially legacy preferences, history, scheduled scans, quarantine records, and restore behavior. Reviewed issue/PR lists are not all fixed; keep the linked ledgers current. The Perl reference tree was retired after its parity capture, so the remaining behavior notes live in `docs/revival/`.
- Keep the application ID `io.github.linuxdefender.linuxdefender` stable for desktop integration while validating the completed executable, desktop-file, and data-directory rename across upgrades.
- Complete CachyOS desktop validation and signed package builds. The full Rust workspace suite passes locally with zero failures; two environment-gated tests (GTK clipboard under `xvfb-run`, signed-RPM bootstrap) remain ignored by design.
- Finish licensing and attribution review, replace the inherited package maintainer contact with an owner-controlled address, and verify release signing/update feeds.

Do not treat this snapshot as a guarantee of complete ClamTk parity, support for every distribution, or comprehensive malware protection. No file or URL was submitted to VirusTotal or urlscan during development checks.
