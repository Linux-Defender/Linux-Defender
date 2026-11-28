#!/usr/bin/env bash
# Read-only host ClamAV report: installed engine versions, the version your
# distro repos offer, daemon state and signature-database health. No sudo, no
# downloads, no package changes. Run with: ./scripts/check-clamav-host.sh
set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

echo "== Installed host tools =="
for tool in clamscan clamd freshclam; do
    if command -v "$tool" >/dev/null 2>&1; then
        printf '%-10s %s\n' "$tool" "$("$tool" --version 2>&1 | head -n 1)"
    else
        printf '%-10s not installed\n' "$tool"
    fi
done

echo "== Repository version =="
installed=""
available=""
if command -v pacman >/dev/null 2>&1; then
    installed="$(pacman -Q clamav 2>/dev/null | awk '{print $2}')"
    available="$(pacman -Si clamav 2>/dev/null | awk -F': ' '/^Version/{print $2; exit}')"
elif command -v apt-cache >/dev/null 2>&1; then
    installed="$(dpkg-query -W -f='${Version}' clamav 2>/dev/null || true)"
    available="$(apt-cache policy clamav 2>/dev/null | awk '/Candidate:/{print $2; exit}')"
else
    echo "unknown (no supported package manager detected)"
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
if command -v systemctl >/dev/null 2>&1; then
    systemctl is-active clamav-daemon 2>/dev/null || echo "clamav-daemon not active (service name may differ)"
else
    echo "systemctl unavailable"
fi

echo "== Signatures =="
if [ -x scripts/check-signatures.py ]; then
    python3 scripts/check-signatures.py 2>&1 | tail -n 1
fi

echo "Official downloads: https://www.clamav.net/downloads"
echo "Linux Defender never installs or bundles the engine or signatures; a human applies distro upgrades."
