---
title: Use the system tray
description: Run Linux Defender in the background when the desktop supports SNI.
---

Linux Defender's tray is optional. It uses an in-process, pure-Rust StatusNotifierItem and DBusMenu implementation. It does not run the retired Python tray subprocess and does not require a GTK or `libdbusmenu` tray binding. KDE Plasma, Cinnamon, MATE, and Budgie generally provide an SNI watcher; GNOME requires [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/) or another compatible watcher. On Sway and other wlroots compositors, add a tray watcher to your bar (for example `waybar` with a `tray` module); the tray does not need a Python process or a `libdbusmenu` binding. Native dialogs there normally need `xdg-desktop-portal-wlr`. Sway behavior still needs a real desktop validation pass.

## Configure behavior

In **Preferences → Behavior**:

- **When closing window:** choose minimize to tray, quit, or ask. Without a tray, closing quits.
- **Start in System Tray:** hides ordinary launches after the native SNI item is accepted. Launches with a scan target stay visible.
- `minimize_to_tray` is a JSON-only setting for the window-manager minimize button.

Verify that your desktop actually shows the icon before relying on background startup. A tray failure does not prevent normal GUI use.

## Tray actions

Right-click the icon to show/hide the window, run Quick Scan or Full Scan, select a saved profile, update definitions, or quit. The normal protected state uses Linux Defender's bundled official logo, so source, AppImage, Flatpak, and Debian installs do not depend on a host icon-theme asset. Temporary warning, scanning, and threat states retain their desktop status indicators. Scans continue when the window is hidden; quitting cancels them.

## Autostart

Enable **Start in System Tray**, then create a user autostart entry if you want launch-on-login. Keep path scans separate: passing a file or folder deliberately opens the window.

### Validate on Sway

Sway wiring is checked in every commit (Rust SNI tray, AUR `waybar`/`sway`/
`xdg-desktop-portal-wlr` optdepends, and these guides), but a real Sway session
still needs a human pass. From a running Sway session with `waybar`'s `tray`
module configured:

```bash
bash scripts/validate-sway.sh
```

The helper requires `sway`, `waybar`, `grim`, and `dbus-send`; it launches the
app, captures the screen, and prints a checklist: tray icon visible, right-click
menu actions, minimize/restore with scans continuing, native dialogs through the
portal, and an EICAR scan with a clean debug log. A green repository check does
not replace that pass.

For design, native event handling, lifecycle, and security limits, see [Rust/Tauri desktop and tray architecture](/Linux-Defender/docs/contributing/architecture/).