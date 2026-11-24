# Arch / AUR packaging

These are **source recipes** for Arch Linux and derivatives (including
CachyOS). They are not yet submitted to the AUR; review and build them locally
first. Linux Defender 0.6.0 is a development snapshot, so a successful build is
not a release or a distribution-support claim.

```bash
cd aur
makepkg -si                       # desktop application
cd linux-defender-privileged-helper
makepkg -si                       # optional matching helper package
```

The two recipes share one pinned source commit and a checked SHA-256. Keep
`pkgver` in both equal to the workspace `Cargo.toml` version, and update the
commit, tarball hash, and `.SRCINFO` together when bumping the snapshot.

## What is installed

- Application: `linux-defender`, `linux-defender-scheduled-scan`, desktop and
  AppStream metadata, icons, Nemo/KIO file-manager actions, Nautilus helpers,
  and compiled gettext catalogs.
- Helper: root-owned `/usr/bin/linux-defender-apply-preferences` and the
  PolicyKit policy at `/usr/share/polkit-1/actions/`. The GUI only offers
  protected configuration writes when this version-matched helper is trusted.
- Neither recipe bundles ClamAV, its engine, or its signature database. Install
  `clamav` with `pacman`; FreshClam owns the host database.

## Sway and other wlroots desktops

The tray is an in-process Rust StatusNotifierItem/DBusMenu implementation, so
no Python tray process or `libdbusmenu` binding is required. On Sway you still
need a tray **watcher** in your bar (for example `waybar` with a `tray` module)
and normally `xdg-desktop-portal-wlr` for native dialogs. These are listed as
`optdepends`, not hard dependencies: the app works without a visible tray.

See the [installation guide](/Linux-Defender/docs/installation/) and
[tray guide](/Linux-Defender/docs/guides/tray/) for validation status and
desktop-specific notes.
