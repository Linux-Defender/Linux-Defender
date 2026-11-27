---
title: Installation and testing
description: Current development-build status and how to run Linux Defender on CachyOS or Arch Linux.
---

## Release status

Linux Defender **0.6.0 is a development snapshot**. It has no signed Linux Defender installer, Flatpak, AppImage, DEB, RPM, or published AUR package yet. AUR source recipes live in the repository's `aur/` directory but have not been submitted to the AUR; use the source checkout or those recipes to test it. An upstream app package is a different product build.

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

Linux Defender has no published release or signed installer packages yet, so none of those application-update paths is currently available. There is no universal in-app self-updater, and CachyOS/Arch has local AUR source recipes but no published AUR package or update channel yet. The project is not yet validated across all distributions.

## Compatibility status

| Target | Current project status |
| --- | --- |
| CachyOS / Arch | AUR `PKGBUILD` recipes for the app and the matching helper exist in `aur/`, but are not published to the AUR and have no desktop validation claim yet. Sway is expected to work with a tray watcher such as `waybar`. |
| Debian / Ubuntu | DEB build workflow targets amd64 and arm64; no Linux Defender package release yet. |
| Fedora | RPM workflow packages the privileged helper only, not the full desktop app. |
| Flatpak | CI build target for x86_64 and aarch64; not published on Flathub or another update remote. |
| AppImage | x86_64 build target; the release workflow prepares a signed GitHub zsync feed, but no release/feed is published yet. |
| Other distributions | No compatibility claim until build, install, update, desktop, and scanner behavior are tested there. |

The Rust/Tauri UI is shared, but GTK/WebKitGTK versions, helper packages, ClamAV paths, services, desktop menus, and release channels differ. A successful source build alone does not establish distribution support.

File-manager integrations ship in two format-correct variants: native packages use `linux-defender ...` launchers, while Flatpak uses `flatpak run io.github.linuxdefender.linuxdefender ...`. Both sets contain the same eight Nautilus, Nemo, Dolphin, and Thunar actions, checked by `scripts/check-integration-parity.py` on every commit. Dolphin and Konqueror service menus cover all file types and directories, so text files, images, and archives also offer the scan actions. Every action passes all selected paths to the scanner; VirusTotal folder analysis submits up to 100 files individually; the file-manager action submits only the first selected file.

## Build and run on CachyOS / Arch

Install Tauri's current Arch build dependencies, Rust, and Bun:

```bash
sudo pacman -S --needed rust bun webkit2gtk-4.1 base-devel curl wget file openssl appmenu-gtk-module libappindicator-gtk3 librsvg xdotool
```

From the Linux Defender checkout:

```bash
cd Linux-Defender
git switch main
cargo test --workspace --locked
cd desktop
bun install --frozen-lockfile
bun run tauri dev
```

The full Rust workspace suite (`cargo test --workspace --locked`) passes locally with zero failures. Two environment-gated tests stay ignored by design: the GTK clipboard test (needs `xvfb-run`) and the signed-RPM bootstrap test (needs a built signed helper RPM). A successful app launch does not replace interactive desktop validation.

### AUR source build (CachyOS / Arch)

From a checkout, build and install the application recipe, then the optional
version-matched helper recipe:

```bash
cd aur && makepkg -si
cd linux-defender-privileged-helper && makepkg -si
```

Both recipes pin the same source commit and verify its SHA-256. Install
`clamav` separately; no engine or signature database is bundled. On Sway,
install `waybar` with a tray module and `xdg-desktop-portal-wlr` for native
dialogs. See the [tray guide](/Linux-Defender/docs/guides/tray/) and the `aur/README.md`
in your repository checkout.

## Other Linux distributions

Tauri's native desktop build needs Rust, Bun, GTK 3, WebKitGTK 4.1, and the distribution's build tools. Package names and available versions differ. See the [Tauri Linux prerequisites](https://v2.tauri.app/start/prerequisites/) and the [development guide](/Linux-Defender/docs/contributing/development/). A distribution is not supported until its build, package, and desktop behavior have been tested.

## Safe testing

- Use the built-in EICAR test or another harmless test fixture; do not download real malware.
- Keep VirusTotal and urlscan checks opt-in. Read the confirmation each time; submitted files or URLs may be retained or shared by those services.
- Test quarantine and restore with disposable files before trusting it with important data.
- Back up the legacy ClamUI directories before upgrading: startup merges them into the Linux Defender locations and renames the old directory `<name>.migrated` (nothing is deleted). Importing ClamTk preferences, history, schedules, and quarantine is still incomplete.
