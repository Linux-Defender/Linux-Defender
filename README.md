# Linux Defender

A community revival project for a single, maintainable Linux malware-scanning desktop app. The goal is one interface that carries forward useful ClamTk workflows and ClamUI features while using the system's supported ClamAV tools and signature database.

**Development status:** Linux Defender 0.6.0 development snapshot, based on ClamUI 0.6.0 (Rust core, Tauri desktop runtime, React/TypeScript UI). Internal application identifiers remain ClamUI temporarily to preserve installed data while migration is designed. ClamTk parity, CachyOS packaging, and desktop validation remain in progress. No Linux Defender signed installer packages are published; do not treat this branch as a finished or guaranteed protection product.

## Design goals

- Ship one desktop app and one primary UI; do not require users to launch a separate Perl/GTK ClamTk app.
- Keep Cisco Talos ClamAV and FreshClam installed and updated by the Linux distribution; do not bundle an engine or signatures.
- Preserve useful ClamTk features and behavior through tested ports. The original ClamTk tree may be kept temporarily as a migration reference; it is not a second runtime or a packaged UI.
- Keep optional local YARA rules opt-in and user-managed. Never download arbitrary signature feeds automatically.
- Make VirusTotal file sharing and urlscan submissions explicit; report remote services separately from local antivirus verdicts.
- Test on CachyOS/Arch first, then establish and test a distribution support matrix.

## Current integration status

- The upstream ClamUI Rust/Tauri/React app is the local foundation and its existing scanner, quarantine, scheduling, history, database controls, and VirusTotal integration are retained.
- ClamTk profile engine options now apply to the scan. Supported limits, PUA/heuristic alerts, recursion, hidden files, and symlink choices are validated; unsupported options fail closed. Automatic mode chooses standalone `clamscan` when an option or local YARA rule needs it, while daemon-only mode reports an error. Local YARA scans pass both the configured ClamAV signature directory and each YARA file, so YARA adds to the official/shared signatures rather than replacing them.
- Scan now has Files & Folders and Website URL modes. Website URL mode supports both VirusTotal URL analysis and urlscan.io, with explicit provider-specific sharing warnings and confirmation. urlscan defaults to Private; VirusTotal public API submissions and lookups are added to its dataset and can be shared.
- VirusTotal file scans now show hashing/upload/analysis progress and an early analysis link. A separate VirusTotal folder action previews all included files before confirmation, skips symlinks, revalidates file identity, limits traversal to 10,000 entries and uploads to 100 files/1 GiB, and reports each result. This feature passed mocked backend tests but still needs real desktop and transport validation on CachyOS. Local ClamAV folder scanning remains a separate option. See [the Lenspect issue and PR review](docs/revival/LENSPECT-REVIEW.md).
- Remaining ClamTk parity work includes one-time import of legacy preferences, history, schedules, quarantine payloads, and restore records; app self-update behavior remains owned by the distro package manager. Review `docs/revival/CHAT-AND-PROJECT-AUDIT.md` for all known parity gaps, release constraints, and CachyOS checks.
- The visible window, About screen, tray tooltip, browser title, file-manager labels, schedule labels, and shield icon use Linux Defender. Internal bundle, protocol, data, and CLI identifiers still use ClamUI until a safe migration is implemented.

## Scanner boundary

The app controls host-installed clamscan, clamdscan, and freshclam. FreshClam updates the shared system signature database, including official `main`, `daily`, and `bytecode` definitions. ClamTk uses ClamAV's databases too; its per-user mode copies those definitions rather than adding a separate malware engine. Linux Defender also supports local user-managed YARA rules for standalone `clamscan`. ClamAV can load other compatible signature formats, but Linux Defender does not install or update third-party feeds such as SaneSecurity automatically; provider trust, compatibility, false positives, and update policy need a separate design. VirusTotal and urlscan are optional online services, not extra local signature databases.

The Database page lists recognized files in the configured ClamAV database directory. This inventory is informational: it cannot confirm which files a running `clamd` process loaded. A detected file is not automatically trusted, enabled, or updated by Linux Defender.

## Build and test

See the [development guide](website/src/content/docs/docs/contributing/development.md). Typical source checks are:

- cargo test --workspace --locked
- cargo fmt --check --all
- cargo clippy --workspace --all-targets --locked -- -D warnings
- cd desktop && bun install --frozen-lockfile && bun run build
- cd desktop && bun run tauri dev

The Rust desktop build needs the GTK 3 and WebKitGTK 4.1 development libraries. Test the actual window, dark/light themes, Wayland/X11, FreshClam status, scan/cancel flows, quarantine restore, YARA rules, and package install on CachyOS before calling this stable.

## Upstream credits and relationship

This project is independent and not affiliated with Microsoft, Cisco Talos, ClamAV, ClamTk, or ClamUI. The current application source is derived from linx-systems/clamui, licensed under MIT; retain its license and notices. ClamAV and ClamTk have their own licenses and copyrights. Review every imported or ported component's license before distribution. The name Linux Defender is a project name chosen by the maintainer; it does not indicate a Microsoft product or endorsement.

Source integration and the remaining parity work are mapped in [the consolidation inventory](docs/revival/SOURCE-CONSOLIDATION.md).
