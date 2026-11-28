#!/usr/bin/env bash
# Read-only host ClamAV report for every supported distro and package format.
# Shows installed engine versions, what the distro repository offers, daemon
# state and signature-database health. No sudo, downloads or package changes.
# Works on native installs, Flatpak/Snap hosts and AppImage systems: it only
# inspects whatever host tools are visible from the current environment.
set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "== Installed host tools =="
for tool in clamscan clamd freshclam; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf '%-10s %s\n' "$tool" "$("$tool" --version 2>&1 | head -n 1)"
    else
        printf '%-10s not visible here (sandbox or not installed)\n' "$tool"
    fi
done

echo "== Repository version =="
installed=""
available=""
if command -v pacman >/dev/null 2>&1; then
    installed="$(pacman -Q clamav 2>/dev/null | awk '{print $2}')"
    available="$(pacman -Si clamav 2>/dev/null | awk -F': ' '/^Version/{print $2; exit}')"
elif command -v apt-cache >/dev/null 2>&1 && command -v dpkg-query >/dev/null 2>&1; then
    installed="$(dpkg-query -W -f='${Version}' clamav 2>/dev/null || true)"
    available="$(apt-cache policy clamav 2>/dev/null | awk '/Candidate:/{print $2; exit}')"
elif command -v dnf >/dev/null 2>&1; then
    installed="$(rpm -q --qf '%{VERSION}-%{RELEASE}' clamav 2>/dev/null || true)"
    available="$(dnf -q list --available clamav 2>/dev/null | awk 'NR>1 && $1 ~ /^clamav\./ {print $2; exit}')"
elif command -v zypper >/dev/null 2>&1; then
    installed="$(rpm -q --qf '%{VERSION}-%{RELEASE}' clamav 2>/dev/null || true)"
    available="$(zypper -q info clamav 2>/dev/null | awk -F': ' '/^Version/{print $2; exit}')"
else
    echo "unknown package manager (source build, container, or unsupported distro)"
fi
if [ -n "$installed" ] || [ -n "$available" ]; then
    printf 'installed=%s available=%s\n' "${installed:-unknown}" "${available:-unknown}"
    if [ -n "$installed" ] && [ -n "$available" ] && [ "$installed" != "$available" ]; then
        echo "Upgrade available from the distribution repository."
    else
        echo "No repository upgrade detected (or version comparison unavailable)."
    fi
fi

echo "== Daemon =="
daemon_active=""
if command -v systemctl >/dev/null 2>&1; then
    for unit in clamav-daemon clamd@scan clamd; do
        if [ "$(systemctl is-active "$unit" 2>/dev/null)" = "active" ]; then
            daemon_active="$unit"
            break
        fi
    done
fi
if [ -n "$daemon_active" ]; then
    printf 'active daemon unit: %s\n' "$daemon_active"
else
    echo "no active daemon unit found (daemon scans may be unavailable)"
fi

echo "== Signatures =="
if [ -x scripts/check-signatures.py ]; then
    python3 scripts/check-signatures.py 2>&1 | tail -n 1
fi

echo "Official downloads: https://www.clamav.net/downloads"
echo "Linux Defender never installs or bundles the engine or signatures; a human applies distro upgrades."
