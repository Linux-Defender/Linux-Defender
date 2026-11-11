# Linux Defender

A community revival project for a single, maintainable Linux malware-scanning desktop app. The goal is one interface that carries forward useful ClamTk workflows and ClamUI features while using the system's supported ClamAV tools and signature database.

**Development status:** early integration. The current source is based on ClamUI 0.5.1 (Rust core, Tauri desktop runtime, React/TypeScript UI). ClamTk parity, app identity migration, CachyOS packaging, and desktop validation are still in progress. Do not treat this branch as a finished or guaranteed protection product.

## Design goals

- Ship one desktop app and one primary UI; do not require users to launch a separate Perl/GTK ClamTk app.
- Keep Cisco Talos ClamAV and FreshClam installed and updated by the Linux distribution; do not bundle an engine or signatures.
- Preserve useful ClamTk features and behavior through tested ports. The original ClamTk tree may be kept temporarily as a migration reference; it is not a second runtime or a packaged UI.
- Keep optional local YARA rules opt-in and user-managed. Never download arbitrary signature feeds automatically.
- Make VirusTotal file sharing and urlscan submissions explicit; report remote services separately from local antivirus verdicts.
- Test on CachyOS/Arch first, then establish and test a distribution support matrix.

## Current integration status

- The upstream ClamUI Rust/Tauri/React app is the local foundation and its existing scanner, quarantine, scheduling, history, database controls, and VirusTotal integration are retained.
- The first ClamTk parity port adds local YARA rule-directory selection for standalone clamscan; rules are not loaded in explicitly forced daemon mode.
- The ClamTk scheduler, quarantine behavior, whitelist, URL reputation controls, translations, plugins, open issues, and PR-derived fixes still need a line-by-line parity and validation pass.
- Package identity still uses the upstream ClamUI identifiers. Linux Defender branding and package IDs must be changed consistently before a release.

## Scanner boundary

The app controls host-installed clamscan, clamdscan, and freshclam. FreshClam updates the shared system signature database. ClamUI is an on-demand scanning UI and does not by itself guarantee real-time protection. VirusTotal and urlscan are optional online reputation/submission services, not extra local antivirus engines; uploads require informed consent.

## Build and test

See the upstream development guide in website/src/content/docs/docs/contributing/development.md. Typical source checks are:

- cargo test --workspace --locked
- cargo fmt --check --all
- cargo clippy --workspace --all-targets --locked -- -D warnings
- cd desktop && bun install --frozen-lockfile && bun run build
- cargo run -p clamui from desktop/src-tauri after building the frontend

The Rust desktop build needs the GTK 3 and WebKitGTK 4.1 development libraries. Test the actual window, dark/light themes, Wayland/X11, FreshClam status, scan/cancel flows, quarantine restore, YARA rules, and package install on CachyOS before calling this stable.

## Upstream credits and relationship

This project is independent and not affiliated with Microsoft, Cisco Talos, ClamAV, ClamTk, or ClamUI. The current application source is derived from linx-systems/clamui, licensed under MIT; retain its license and notices. ClamAV and ClamTk have their own licenses and copyrights. Review every imported or ported component's license before distribution. The name Linux Defender is a project name chosen by the maintainer; it does not indicate a Microsoft product or endorsement.
