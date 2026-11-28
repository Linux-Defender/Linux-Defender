#!/usr/bin/env bash
# One answer to "which Linux Defender package?" — read-only, no install, no
# download. Detects the host and prints the format with the deepest integration
# that works here, plus the universal fallback. All six formats share the same
# core, version, app id, host-ClamAV boundary and integration assets, so this
# is a presentation choice, not a product split.
set -uo pipefail

ID=""
if [ -r /etc/os-release ]; then
    ID="$(. /etc/os-release && printf '%s' "${ID:-}")"
fi

recommend=""
reason=""
case "$ID" in
    debian|ubuntu|linuxmint|pop|raspbian)
        recommend="DEB (application + privileged helper)"
        reason="native systemd timers, polkit helper and package-installed file-manager actions" ;;
    fedora|rhel|centos|rocky|alma)
        recommend="Fedora/RHEL helper RPM + AppImage app"
        reason="signed helper RPM for privileged configuration; portable AppImage for the GUI" ;;
    arch|cachyos|manjaro|endeavouros)
        recommend="AUR (app + version-matched helper)"
        reason="source recipes pinned to one commit with matching 0.6.0 helper" ;;
    opensuse*|sles)
        recommend="AppImage app + host ClamAV from zypper"
        reason="universal portable app; host tools installed with the distribution package manager" ;;
    *)
        recommend="AppImage"
        reason="portable single file with bundled GTK3/WebKitGTK 4.1 and host ClamAV" ;;
esac

alt=""
if command -v flatpak >/dev/null 2>&1; then
    alt="Flatpak (sandboxed, Flathub) — best when you prefer isolation and automatic updates"
elif command -v snap >/dev/null 2>&1; then
    alt="Snap (classic confinement) — best when snapd is your package layer"
else
    alt="Flatpak or Snap can be added later for sandboxing or store updates"
fi

printf 'Recommended for this host (%s): %s\n' "${ID:-unknown}" "$recommend"
printf 'Why: %s\n' "$reason"
printf 'Universal alternative: %s\n' "$alt"
printf 'All formats are the same product: one core, one version, one app id, host ClamAV never bundled.\n'
printf 'Details: docs/installation.md and the repository README.\n'
