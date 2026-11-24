#!/usr/bin/env bash
# Capture the REAL Linux Defender Tauri/WebKitGTK window for visual inspection.
#
# The browser visual harness (desktop/visual-harness.html) renders the same React
# components in Chromium, but native form controls and WebKitGTK rendering can
# differ. This script captures the actual desktop window so an agent or human
# can read the PNG and see what users really see.
#
# Usage:
#   bun run --cwd desktop tauri dev          # in another terminal
#   bash scripts/capture-app-window.sh [out.png]
#   # Then: read <out.png> with your image-capable tool.
#
# Works with any Linux Defender build (native, AppImage, Flatpak, Snap, RPM):
# it captures a window, not a package. Supports KDE/Wayland (Spectacle),
# GNOME (gnome-screenshot), wlroots/Sway/Hyprland (grim), and X11
# (ImageMagick import / scrot / ffmpeg), with graceful failure if none exists.
#
# Focus the Linux Defender window before running (the Wayland path captures the
# active window, since Wayland clients cannot be focused with xdotool).
set -uo pipefail

OUT="${1:-/tmp/opencode/linux-defender-window.png}"
mkdir -p "$(dirname -- "$OUT")"
captured=0

if [ "${XDG_SESSION_TYPE:-}" = "wayland" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    if command -v spectacle >/dev/null 2>&1; then
        echo "Capturing active window with Spectacle (Wayland)..."
        if spectacle -b -n -a -d 1200 -o "$OUT" >/dev/null 2>&1; then captured=1; fi
    elif command -v gnome-screenshot >/dev/null 2>&1; then
        echo "Capturing active window with gnome-screenshot (Wayland)..."
        if gnome-screenshot -w -f "$OUT" >/dev/null 2>&1; then captured=1; fi
    elif command -v grim >/dev/null 2>&1; then
        echo "Capturing screen with grim (Wayland/wlroots)..."
        if grim "$OUT" >/dev/null 2>&1; then captured=1; fi
    fi
fi

if [ "$captured" -eq 0 ] && [ -n "${DISPLAY:-}" ]; then
    wid=""
    if command -v xdotool >/dev/null 2>&1; then
        wid=$(xdotool search --name "Linux Defender" 2>/dev/null | head -n 1 || true)
        if [ -n "$wid" ]; then xdotool windowactivate "$wid" >/dev/null 2>&1 || true; fi
    fi
    if command -v import >/dev/null 2>&1; then
        echo "Capturing window with ImageMagick import (X11)..."
        if [ -n "$wid" ]; then
            if import -window "$wid" "$OUT" >/dev/null 2>&1; then captured=1; fi
        elif import -window root "$OUT" >/dev/null 2>&1; then captured=1; fi
    elif command -v scrot >/dev/null 2>&1; then
        echo "Capturing focused window with scrot (X11)..."
        if scrot -u "$OUT" >/dev/null 2>&1; then captured=1; fi
    fi
fi

if [ "$captured" -eq 0 ] && command -v ffmpeg >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
    echo "Capturing root window with ffmpeg (x11grab)..."
    if ffmpeg -y -loglevel quiet -f x11grab -video_size "$(xrandr 2>/dev/null | grep -m1 '\*' | awk '{print $1}' || echo '1920x1080')" -i "$DISPLAY" -frames:v 1 "$OUT" >/dev/null 2>&1; then captured=1; fi
fi

if [ "$captured" -eq 0 ]; then
    echo "ERROR: no supported screenshot tool found for this session (XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset})." >&2
    echo "Install spectacle (KDE), gnome-screenshot (GNOME), or imagemagick + scrot (X11)." >&2
    exit 1
fi

if [ ! -s "$OUT" ]; then
    echo "ERROR: capture tool ran but produced no file at $OUT" >&2
    exit 1
fi
if command -v file >/dev/null 2>&1 && ! file "$OUT" | grep -q "PNG image data"; then
    echo "ERROR: capture at $OUT is not a PNG image" >&2
    exit 1
fi

echo "CAPTURED: $OUT"
file "$OUT"
