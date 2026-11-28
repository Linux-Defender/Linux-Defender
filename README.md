<div align="center">

<img src="icons/io.github.linuxdefender.linuxdefender.svg" alt="Linux Defender" width="120" height="120" />

# Linux Defender

A modern Linux desktop interface for ClamAV, built with Rust, Tauri, and a React frontend.

[Get Linux Defender](website/src/content/docs/docs/download.md) (published at `/Linux-Defender/docs/download/` on the site) · [Website](https://linux-defender.github.io/Linux-Defender/) · [Documentation](https://linux-defender.github.io/Linux-Defender/docs/) · [Issues](https://github.com/Linux-Defender/Linux-Defender/issues) · [Security](SECURITY.md)

[![Build AppImage](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-appimage.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-appimage.yml)
[![Build AUR](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-aur.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-aur.yml)
[![Build Debian Package](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-deb.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-deb.yml)
[![Build Flatpak](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-flatpak.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-flatpak.yml)
[![Build RPM Helper Package](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-rpm.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-rpm.yml)
[![Build Snap](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-snap.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-snap.yml)
[![Test](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/test.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/test.yml)
[![Lint](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/lint.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/lint.yml)
[![CodeQL](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/codeql.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/codeql.yml)
[![Translations](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/i18n.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/i18n.yml)
[![Packaging Sync](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/packaging-sync.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/packaging-sync.yml)
[![Signature Database](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/signature-database.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/signature-database.yml)
[![Doc Links](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/doc-links.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/doc-links.yml)
[![Upstream Freshness](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/upstream-freshness.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/upstream-freshness.yml)
[![Consistency Audit](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/consistency.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/consistency.yml)
[![Dependency Audit](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependency-audit.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependency-audit.yml)
[![Validate Website](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/website.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/website.yml)
[![Deploy website](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/deploy-website.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/deploy-website.yml)
[![Build All Packages](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-all.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/build-all.yml)
[![Refresh Dependabot sources](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependabot-refresh.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependabot-refresh.yml)
[![Dependency Review](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependency-review.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/dependency-review.yml)
[![Proof HTML](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/proof-html.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/proof-html.yml)
[![Release](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/release.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/release.yml)
[![Auto Assign](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/auto-assign.yml/badge.svg)](https://github.com/Linux-Defender/Linux-Defender/actions/workflows/auto-assign.yml)

</div>

## Development status

Linux Defender 0.6.0 is a development snapshot (Rust core, Tauri desktop runtime, React/TypeScript UI). Legacy application, executable, helper, and data identifiers remain temporarily so existing settings and integrations are not lost while migration is designed. No Linux Defender signed installer packages are published; do not treat this branch as a finished or guaranteed protection product.

## Host ClamAV boundary

Every package format uses **host** ClamAV. Install host `clamscan` and `freshclam`; daemon scans also require host `clamd` and `clamdscan`.

```bash
# Debian or Ubuntu
sudo apt install clamav clamav-freshclam

# Arch / CachyOS
sudo pacman -S --needed clamav

# Fedora Workstation
sudo dnf install clamav clamav-freshclam

# Fedora Atomic (then reboot)
sudo rpm-ostree install clamav clamav-freshclam

# openSUSE Tumbleweed / Leap
sudo zypper install clamav
```

Linux Defender does not bundle an engine or signature database. Scanning, quarantine, scheduling, database status, and optional VirusTotal/urlscan lookups are one desktop app; the host **FreshClam** service owns database updates.

## Design goals

- Ship one desktop app and one primary UI; do not require users to launch a separate Perl/GTK ClamTk app.
- Keep ClamAV and FreshClam installed and updated by the Linux distribution; never bundle an engine or signatures.
- Preserve useful ClamTk/ClamUI workflows through tested ports; keep compatibility identifiers only as migration contracts.
- Keep local YARA rules opt-in and user-managed. Never download arbitrary signature feeds automatically.
- Make VirusTotal file sharing and urlscan submissions explicit; report remote services separately from local antivirus verdicts.
- Use the same Linux Defender identity and host-ClamAV boundary in every package format.

## Current integration status

- The Rust/Tauri/React foundation provides scanning, quarantine, scheduling, history, database controls, a system audit, and VirusTotal/urlscan integration.
- Scan supports Files & Folders and Website URL modes with explicit consent before any online submission.
- Protected host settings go through the version-matched `linux-defender-apply-preferences` helper and Polkit policy; source builds can install the locally built helper from the blocked-settings dialog.
- File-manager integrations (Nautilus/Nemo/Dolphin/Thunar) and a native SNI/DBusMenu tray ship in every format. The in-app **Preferences → Behavior → Configure Integration** manager is available only in the Flatpak build. DEB, RPM, Snap, AppImage, and AUR stage the same file-manager actions through their package or builder scripts; AppImage bundles the native launcher assets under `usr/share/linux-defender/integrations`.
- Remaining parity work is tracked in [the revival records](docs/revival/RELATED-PROJECT-REVIEW.md) and [the fork status](docs/clamui-fork/STATUS.md).

## For source development

Clone `main` (the active development branch). The Rust/Tauri desktop uses WebKitGTK 4.1, GTK 3, a native StatusNotifierItem tray, and no Python application runtime. Protected host ClamAV configuration remains behind the version-matched `linux-defender-apply-preferences` helper and Polkit policy.

```bash
git clone https://github.com/Linux-Defender/Linux-Defender.git
cd Linux-Defender
cargo test --workspace --locked
( cd desktop && bun install --frozen-lockfile && bun run build )
bun run --cwd desktop tauri dev
```

Run `./scripts/deep-audit.sh` for the canonical exhaustive audit, or `/deep-audit` in Claude Code. See the [development guide](website/src/content/docs/docs/contributing/development.md) for the full validation and packaging workflow. Run `bash scripts/audit-consistency.sh` for a single full local consistency audit.

## Documentation

- [Installation](website/src/content/docs/docs/installation.md) — runtime and package requirements.
- [First scan](website/src/content/docs/docs/getting-started.md) — get a local scan running.
- [User guides and troubleshooting](website/src/content/docs/docs/) — scanning, quarantine, schedules, privacy, recovery.
- [Development, architecture, and packaging](website/src/content/docs/docs/contributing/development.md) — source, validation, packaging.
- [Visual identity and screenshot regeneration](docs/DESIGN.md) — color tokens, components, brand assets.
- [Contributor rules](AGENTS.md) and [canonical enforcement](AI-ENFORCEMENT.md) — AI/tool-neutral rules and the single source of truth.
- [Script inventory](docs/documentation/SCRIPTS.md) — every maintenance script and checker, including `update-all.sh` and `capture-all.sh`.
- [Generated documentation map](docs/DOC-MAP.md) — every tracked project document.
- [Translation workflow](docs/translations/README.md) and [translation guide](website/src/content/docs/docs/contributing/translating.md) — catalogs, plural forms, human review.
- [Revival research index](docs/revival/README.md), [upstream inventory](docs/revival/UPSTREAM-REPOSITORIES.md), [parity matrix](docs/revival/RELATED-PROJECT-REVIEW.md), and [fork status](docs/clamui-fork/STATUS.md) — what was ported, deferred, or superseded.
- [Full requirement ledger](docs/revival/CHAT-AND-PROJECT-AUDIT.md) — every request and where it is satisfied.
- [Security policy](SECURITY.md) and [rebrand audit](docs/revival/REBRAND-AUDIT.md) — private reporting and retained upstream notices.

## One product, one choice made for you

All six formats ship the same core, version, app id, host-ClamAV boundary and integration assets — there is no feature fragmentation. Run `./scripts/recommend-format.sh` for a read-only recommendation based on this host; it never installs or downloads anything. Native DEB/RPM give the deepest OS integration, while Flatpak, AppImage and Snap are the cross-distro paths. See [the installation guide](website/src/content/docs/docs/installation.md) for details.

## Scanner boundary

The app controls host-installed `clamscan`, `clamdscan`, and `freshclam`. FreshClam updates the shared system signature database (`main`, `daily`, `bytecode`). Linux Defender also supports local, user-managed YARA rules for standalone `clamscan`; YARA adds to the shared signatures rather than replacing them. The suggested custom-feed list only fills the draft — the user reviews and saves it, and database updates remain the host FreshClam service's job. Third-party feeds with registration or restrictive policies are not auto-configured.

## Upstream credits and relationship

Linux Defender is led by project owner and maintainer [Kira (Linux-Defender)](https://github.com/Linux-Defender). This project is independent and not affiliated with Microsoft, Cisco Talos, ClamAV, ClamTk, or ClamUI. Portions of the Rust/Tauri/React source derive from an MIT-licensed upstream foundation; its license and notices are retained in `LICENSE`. ClamAV and ClamTk have their own licenses and copyrights. Review every imported or ported component's license before distribution.

## License

MIT. See [LICENSE](LICENSE).
