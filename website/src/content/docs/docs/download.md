---
title: Get Linux Defender
description: One starting point for every Linux desktop — one product, six formats, no feature fragmentation.
---

Linux Defender is **one product**. DEB, RPM, AppImage, Flatpak, Snap, and AUR all ship the same Rust core, the same version, the same application id, the same host-ClamAV boundary, and the same file-manager actions. There is no reduced "universal" build and no format with extra features.

## One path that works everywhere

Linux Defender 0.6.0 is a development snapshot; no signed release packages are published yet. The single reproducible route on every distro is a source build from the repository:

```bash
git clone https://github.com/Linux-Defender/Linux-Defender.git
cd Linux-Defender
./scripts/local-run.sh --deps --run
```

The development guide has the [full source-build and validation workflow](/Linux-Defender/docs/contributing/development/).

## Which packaged format when releases exist

You do not have to compare feature lists. Run `./scripts/recommend-format.sh` from a source checkout for a read-only recommendation for this host — it makes no changes, downloads nothing, and requires no root. It detects the distribution and prints one answer plus a universal alternative.

- **DEB** (Debian/Ubuntu) and **AUR** (Arch/CachyOS): deepest native integration, including systemd timers and package-installed file-manager actions.
- **RPM helper + AppImage** (Fedora/RHEL): signed privileged helper, portable app.
- **AppImage**: universal single file on any distro; bundles GTK 3 and WebKitGTK 4.1, uses host ClamAV.
- **Flatpak**: sandboxed and distributed through Flathub; host tools via `flatpak-spawn --host`.
- **Snap**: classic confinement for hosts managed by snapd.

Every format keeps host ClamAV outside the package — the engine and signature database are never bundled.

## After installation

Install ClamAV with your distribution's package manager, then start with [the first scan](/Linux-Defender/docs/getting-started/) and [the overview](/Linux-Defender/docs/guides/overview/). See [installation](/Linux-Defender/docs/installation/) for per-distro host commands and [troubleshooting](/Linux-Defender/docs/troubleshooting/) if an action or tray icon is missing.
