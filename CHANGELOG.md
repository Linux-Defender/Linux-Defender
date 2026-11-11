# Changelog

## [Unreleased]

### Added

- Updated the repository and contribution guidance for the `Linux-Defender/Linux-Defender` organization, corrected CI branch filters to `main`, and aligned public website/release links with the renamed repository.
- Branded AppImage artifacts as Linux Defender and routed their signed zsync update metadata to this repository. The release workflow now attaches the AppImage and zsync sidecar; no signed release/feed exists yet, and this does not add a universal in-app updater.
- Ported the upstream post-v0.6.0 updater fix for long-running FreshClam updates. Manual/forced updates now stop only after a configurable period without output (10-minute default; 1–1,440 minutes), rather than a fixed total runtime limit. Added settings UI, docs, regression tests, and translation catalog entries. Vietnamese strings are translated; other catalogs use English fallback pending human review.
- Adopted upstream PR #298 website dependency updates. Deferred PR #299 TypeScript 7.0.2 because Astro 7.4.5's checker rejects TypeScript 7.


## [0.6.0] - 2026-11-11

### Added

- Vietnamese translation: Vietnamese (`vi`) joins the active desktop and CLI catalogs.
- Added VirusTotal URL analysis and urlscan as explicit, consent-based online checks alongside local scanning.
- Added upload/analysis progress and bounded, confirmed VirusTotal folder uploads; remote reputation results remain separate from local ClamAV detections.
- Added a visible inventory of compatible ClamAV database/signature files and combined local YARA rules with the configured host ClamAV database for standalone scans.
- Added recognition of CachyOS's `clamav-freshclam-once.timer` in the Security Audit.

### Changed

- Reduced historical-log loading to the requested entries using a validated, recoverable metadata index, retaining legacy JSON history, privacy migration, corruption recovery, external-file changes, and stable ordering; statistics now reuse parsed timestamps and aggregate trend buckets in one pass.
- Inactive log, quarantine, and statistics views now defer completion-triggered refreshes until shown, keeping retained page state and coalescing pending refreshes without losing invalidations received during an in-flight request.
- Coalesced ordinary desktop scan-progress snapshots at the native bridge while preserving every threat delta, the latest pending snapshot, terminal events, and operation-scoped cleanup; core and CLI progress remain unchanged.
- Standalone ClamAV scans now count files without retaining unused file-path lists; daemon scan inputs, pre-counted totals, and progress estimates are unchanged.
- Desktop quarantine browsing now retrieves bounded date/ID cursor pages with locale-aware literal Unicode search, stable insertion anchors, and stale-response guards; storage totals remain global and the headless CLI retains its complete legacy list.
- Updated Rust dependencies: `glib` to 0.22.10, bundled `rusqlite` to 0.41.1, `base64` to 0.23.1, `rfd` to 0.17.2, and the locked `tauri` resolution to 2.12.5. The `rfd` update removes its `ashpd` portal chain (`async-fs`, `async-net`, and `urlencoding`) without altering existing `zbus` consumers, Flatpak permissions, or the native GTK 3/WebKitGTK 4.1 dependency boundary.
- Updated desktop tooling: `@tauri-apps/cli` to 2.12.4 and TypeScript to 7.0.2. Gettext extraction now uses the locked Babel parser because TypeScript 7 does not provide its former compiler API, and the desktop configuration declares Vite client types so stylesheet side-effect imports remain type-checkable.
- Updated Rust dependencies: `signal-hook` to 0.4.6, `globset` to 0.4.21, `icu_locale_core` to 2.4.0, `ksni` to 0.3.7, `log` to 0.4.35, `open` to 5.4.5, `tauri-plugin-notification` to 2.8.0, `tauri-plugin-single-instance` to 2.5.5, `uuid` to 1.29.1, and `zip` to 9.4.1.
- Updated desktop tooling: `@babel/parser` to 8.1.0, `@vitejs/plugin-react` to 6.2.1, and Vite to 8.3.5; refreshed the Bun, Yarn, and Flatpak dependency sources.

### Fixed

- Fixed trusted native privileged helpers being marked unavailable when automatic installation or installed-package metadata is unavailable; accepted conventional numeric-leading Debian revisions after the exact application upstream version while retaining strict Flatpak package checks and signed-download and trusted-helper verification. (#278)
- Fixed Flatpak scans being blocked by a false missing-virus-database warning when definitions are present on the host; scan preflight now inspects host-side database files while preserving configured directories and metadata. (#279)
- Fixed Flatpak helper installation to support trusted system-tool symlinks, such as Ubuntu's uutils `sha256sum` wrapper, while retaining resolved-target regular-file, root-ownership, safe-write-permission, and execute checks. (#280)
- Fixed Flatpak Wayland startup compatibility by disabling WebKitGTK's DMA-BUF renderer path by default while preserving explicit environment overrides. (#282)
- Fixed large scans losing threats, skipped files, warnings, and summary counts after the 64 MiB output limit; final results and history now retain complete scan evidence for both ClamAV backends while keeping displayed output bounded, preserving exact filename identities, and preventing the CLI from reporting an infected scan as clean. (#285)
- Fixed daemon scans splitting long file-list paths or reporting spurious errors by routing paths of 1,023 bytes or more through the existing protected stdin transport; preserved shorter-path batching, exact filenames, exclusions, progress, and cancellation. (#286)
- Rejected VirusTotal uploads when the original pathname is substituted after lookup, retaining no-follow descriptor identity checks.
- Fixed CodeQL Rust analysis configuration to use no manual build mode.
- Regenerated the stale gettext template used by translation validation.
- Restored Clippy by using a Clippy-compatible chunking form and building the frozen Bun frontend before linting so production `generate_context!` can embed `desktop/dist`.
- Preserved native tray pixel ordering while updating its zero-copy chunk iteration for Rust 1.99 Clippy.
- Fixed ordinary AppImage CI builds passing empty update metadata to `linuxdeploy`; release update information and `.zsync` sidecars remain intact.

### Maintenance

- Switched Debian, RPM, and AppImage CI builds to authenticated HTTPS Ubuntu Jammy mirrors and made repository update errors fatal while retaining the Ubuntu 22.04 baseline, dependencies, and package signing.
- Updated GitHub Actions artifact upload to 7.0.2 and artifact download to 8.0.2.
- Added concise GitHub bug report, feature request, and pull request templates.
- Switched Dependabot's JavaScript projects to Bun, grouped weekly minor and patch updates, and automated the related Bun/Yarn and Flatpak dependency source refresh.
- Enabled verbose Tauri AppImage logs to keep `linuxdeploy` failures actionable.
- Made the escaped-writer deadline regression fixture wait for process readiness, eliminating a CI startup race without relaxing the deadline.

[Unreleased]: https://github.com/Linux-Defender/Linux-Defender/compare/main...HEAD
[Upstream history archive](https://github.com/Linux-Defender/Linux-Defender/blob/main/docs/revival/UPSTREAM-CHANGELOG.md) preserves the source project's earlier release notes for provenance; they are not Linux Defender releases.
