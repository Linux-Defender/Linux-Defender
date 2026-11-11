---
title: Installation and testing
description: Current development-build status and how to run Linux Defender on CachyOS or Arch Linux.
---

## Release status

Linux Defender **0.6.0 is a development snapshot**. It has no signed Linux Defender installer, Flatpak, AppImage, DEB, RPM, or Arch package published yet. Use the source checkout to test it; do not install an upstream ClamUI package and assume it is Linux Defender.

The current source still uses transitional ClamUI launch, helper, and data identifiers for compatibility. The native source build and the ClamUI Flatpak use different data locations, but migration from ClamTk's settings, history, schedule, and quarantine is not complete. Keep the existing ClamTk and ClamUI installs and their data backed up while testing this branch.

## Host ClamAV

Linux Defender calls the host-installed ClamAV tools. Install `clamscan` and `freshclam` using your distribution's package manager. Daemon scans also require `clamd` and `clamdscan`. FreshClam owns the shared signature database through the service or timer configured by your distribution; Linux Defender does not bundle a second database or automatically install arbitrary third-party feeds.

On CachyOS or Arch, the package is `clamav`:

```bash
sudo pacman -S --needed clamav
```

If you already enabled `clamav-freshclam-once.timer`, leave updates to that timer. You can confirm its status and check the ClamAV database version from the Linux Defender Database page.

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
- Keep the ClamTk and ClamUI user-data directories untouched until migration tooling is implemented and verified.
