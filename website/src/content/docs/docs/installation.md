---
title: Installation and testing
description: Current development-build status and how to run Linux Defender on CachyOS or Arch Linux.
---

## Release status

Linux Defender **0.6.0 is a development snapshot**. It has no signed Linux Defender installer, Flatpak, AppImage, DEB, RPM, or Arch package published yet. Use the source checkout to test it; an upstream app package is a different product build.

The current source still uses transitional launch, helper, and data identifiers for compatibility. The native source build and the previous Flatpak install use different data locations, but migration from ClamTk's settings, history, schedule, and quarantine is not complete. Keep existing installs and their data backed up while testing this branch.

## Host ClamAV

Linux Defender calls the host-installed ClamAV tools. Install `clamscan` and `freshclam` using your distribution's package manager. Daemon scans also require `clamd` and `clamdscan`. FreshClam owns the shared signature database through the service or timer configured by your distribution; Linux Defender does not bundle a second database or automatically install arbitrary third-party feeds.

On CachyOS or Arch, the package is `clamav`:

```bash
sudo pacman -S --needed clamav
```

If you already enabled `clamav-freshclam-once.timer`, leave updates to that timer. You can confirm its status and check the ClamAV database version from the Linux Defender Database page.

## Software updates

ClamAV signature updates and Linux Defender software updates use separate channels. FreshClam updates signatures through the service or timer supplied by the Linux distribution. Once releases are available, Linux Defender should update through its installation source: a configured system package repository for native packages, the Flatpak remote for a Flatpak installation, or the external AppImageUpdate tool with signed `.zsync` metadata for an AppImage.

Linux Defender has no published release or signed installer packages yet, so none of those application-update paths is currently available. There is no universal in-app self-updater, and CachyOS/Arch does not yet have a Linux Defender package. The project is not yet validated across all distributions.

## Compatibility status

| Target | Current project status |
| --- | --- |
| CachyOS / Arch | Source-build instructions exist; no PKGBUILD/AUR package and no desktop validation yet. |
| Debian / Ubuntu | DEB build workflow targets amd64 and arm64; no Linux Defender package release yet. |
| Fedora | RPM workflow packages the privileged helper only, not the full desktop app. |
| Flatpak | CI build target for x86_64 and aarch64; not published on Flathub or another update remote. |
| AppImage | x86_64 build target; the release workflow prepares a signed GitHub zsync feed, but no release/feed is published yet. |
| Other distributions | No compatibility claim until build, install, update, desktop, and scanner behavior are tested there. |

The Rust/Tauri UI is shared, but GTK/WebKitGTK versions, helper packages, ClamAV paths, services, desktop menus, and release channels differ. A successful source build alone does not establish distribution support.

## Build and run on CachyOS / Arch

Install Tauri's current Arch build dependencies, Rust, and Bun:

```bash
sudo pacman -S --needed rust bun webkit2gtk-4.1 base-devel curl wget file openssl appmenu-gtk-module libappindicator-gtk3 librsvg xdotool
```

From the Linux Defender checkout:

```bash
cd /home/kiras/Linux-Defender
git switch revival/unified-app
cargo test --workspace --locked
cd desktop
bun install --frozen-lockfile
bun run tauri dev
```

The full workspace test command is included, but this development environment previously had privileged-helper test failures and CLI integration tests that did not finish. A successful app launch does not replace those tests or desktop validation.

## Other Linux distributions

Tauri's native desktop build needs Rust, Bun, GTK 3, WebKitGTK 4.1, and the distribution's build tools. Package names and available versions differ. See the [Tauri Linux prerequisites](https://v2.tauri.app/start/prerequisites/) and the [development guide](/Linux-Defender/docs/contributing/development/). A distribution is not supported until its build, package, and desktop behavior have been tested.

## Safe testing

- Use the built-in EICAR test or another harmless test fixture; do not download real malware.
- Keep VirusTotal and urlscan checks opt-in. Read the confirmation each time; submitted files or URLs may be retained or shared by those services.
- Test quarantine and restore with disposable files before trusting it with important data.
- Keep the legacy app and ClamTk user-data directories untouched until migration tooling is implemented and verified.
