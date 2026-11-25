#!/usr/bin/env bash
# Runtime helper for validating Linux Defender inside a real Sway session.
#
# This script does not pretend to validate Sway from another desktop. Run it
# from an actual Sway session with a tray watcher (waybar's `tray` module) and
# xdg-desktop-portal-wlr. It launches the app, captures a screenshot, and prints
# a checklist for the human validation that automation cannot replace.
set -uo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="${1:-/tmp/opencode/sway-linux-defender.png}"
missing=0

require() {
    if command -v "$1" >/dev/null 2>&1; then
        printf '  %-24s OK\n' "$1"
    else
        printf '  %-24s MISSING\n' "$1"
        missing=1
    fi
}

echo "Sway session prerequisites:"
require sway
require waybar
require grim
require dbus-send

if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -z "${XDG_SESSION_TYPE:-}" ]; then
    echo "ERROR: no Wayland session detected (WAYLAND_DISPLAY unset)." >&2
    exit 1
fi
if ! pgrep -x sway >/dev/null 2>&1; then
    echo "ERROR: sway is not running. Start Sway, then rerun this script." >&2
    exit 1
fi
if [ "$missing" -ne 0 ]; then
    echo "ERROR: install the missing prerequisites, then rerun." >&2
    exit 1
fi

app="$(command -v linux-defender || true)"
if [ -z "$app" ] && [ -x "$ROOT/target/debug/linux-defender" ]; then
    app="$ROOT/target/debug/linux-defender"
fi
if [ -z "$app" ]; then
    echo "ERROR: linux-defender binary not found; use a package build or target/debug." >&2
    exit 1
fi

echo "Launching $app in the Sway session..."
RUST_LOG=linux_defender_core=debug,linux_defender=debug "$app" >/tmp/opencode/sway-linux-defender.log 2>&1 &
pid=$!
mkdir -p "$(dirname -- "$OUT")"
sleep 4
grim "$OUT" >/dev/null 2>&1 || {
    echo "ERROR: grim could not capture the screen." >&2
    kill "$pid" 2>/dev/null || true
    exit 1
}

echo "CAPTURED: $OUT"
echo "APP PID:  $pid (log: /tmp/opencode/sway-linux-defender.log)"
echo
echo "Human checklist (automation cannot confirm these):"
echo "  1. Linux Defender icon appears in the waybar tray module."
echo "  2. Right-click shows show/hide, Quick Scan, profile, update, and quit."
echo "  3. Minimize-to-tray hides the window; scans continue; restore works."
echo "  4. A native dialog opens through xdg-desktop-portal-wlr."
echo "  5. An EICAR scan reports the detection; the debug log has no new errors."
