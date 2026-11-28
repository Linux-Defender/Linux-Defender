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
mkdir -p "$OUT"

echo "== Real Tauri/WebKitGTK window =="
if pgrep -f 'target/debug/linux-defender' >/dev/null 2>&1; then
    bash "$SCRIPT_DIR/capture-app-window.sh" "$OUT/real-app.png"
else
    echo "SKIP: start 'bun run --cwd desktop tauri dev' to capture the native window"
fi

echo "== React views + website =="
HARNESS_URL="${HARNESS_URL:-http://127.0.0.1:1420/visual-harness.html}"
SITE_URL="${SITE_URL:-http://127.0.0.1:8899/Linux-Defender/index.html}"
if curl -fsS -o /dev/null "$HARNESS_URL"; then
    if [ -d "$PROJECT_ROOT/website/node_modules/playwright" ]; then
        ( cd "$PROJECT_ROOT" && bun scripts/capture-browser.mjs "$OUT" "$HARNESS_URL" "$SITE_URL" )
    else
        echo "SKIP: install website dependencies for Playwright browser captures"
    fi
else
    echo "SKIP: start 'bun run --cwd desktop dev' to serve the visual harness"
fi

echo "CAPTURE ALL OK: $OUT ($(find "$OUT" -type f -name '*.png' | wc -l) PNGs)"
