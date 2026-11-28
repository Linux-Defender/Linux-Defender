#!/usr/bin/env bash
# Capture every Linux Defender surface in one pass: the real Tauri/WebKitGTK
# window (native rendering), every React view through the visual harness, and
# the production site in both color schemes. Outputs PNGs to one directory for
# review with an image-capable tool.
#
#   ./scripts/capture-all.sh [out-dir]
#
# Prerequisites: `bun run --cwd desktop tauri dev` running for the native shot,
# `bun run --cwd desktop dev` for the harness, a local site preview for the site
# shots, and frozen website dependencies installed for Playwright. Missing
# sources are skipped with a message rather than failing the whole review.
set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
OUT="${1:-/tmp/opencode/captures}"
CAPTURE_FAILED=0
mkdir -p "$OUT"

echo "== Real Tauri/WebKitGTK window =="
if pgrep -f 'target/debug/linux-defender' >/dev/null 2>&1; then
    if ! bash "$SCRIPT_DIR/capture-app-window.sh" "$OUT/real-app.png"; then
        CAPTURE_FAILED=1
    fi
else
    echo "SKIP: start 'bun run --cwd desktop tauri dev' to capture the native window"
fi

echo "== React views + website =="
HARNESS_URL="${HARNESS_URL:-http://127.0.0.1:1420/visual-harness.html}"
SITE_URL="${SITE_URL:-http://127.0.0.1:4321/Linux-Defender/}"
if curl -fsS -o /dev/null "$HARNESS_URL"; then
    if [ -d "$PROJECT_ROOT/website/node_modules/playwright" ]; then
        SITE_FOR_CAPTURE=""
        if curl -fsS -o /dev/null "$SITE_URL"; then
            SITE_FOR_CAPTURE="$SITE_URL"
        else
            echo "SKIP: start 'bun run --cwd website preview' for site captures"
        fi
        if ! ( cd "$PROJECT_ROOT" && bun scripts/capture-browser.mjs "$OUT" "$HARNESS_URL" "$SITE_FOR_CAPTURE" ); then
            echo "WARN: some browser captures failed"
            CAPTURE_FAILED=1
        fi
    else
        echo "SKIP: install website dependencies for Playwright browser captures"
    fi
else
    echo "SKIP: start 'bun run --cwd desktop dev' to serve the visual harness"
fi

printf "CAPTURE ALL %s: %s (%s PNGs)\n" "$([ "$CAPTURE_FAILED" -eq 0 ] && echo OK || echo FAIL)" "$OUT" "$(find "$OUT" -type f -name '*.png' | wc -l)"
exit "$CAPTURE_FAILED"
