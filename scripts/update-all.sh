#!/usr/bin/env bash
# One entry point for regenerating every checked-in derived artifact, then
# proving the tree is still consistent. Run this after any source, doc, site,
# translation, or packaging change before committing.
#
#   ./scripts/update-all.sh          # regenerate docs/gettext artifacts + verify
#   ./scripts/update-all.sh --full   # also refresh locked packaging sources
#
# The default path is offline and deterministic (no network calls). `--full`
# regenerates Flatpak/Dependabot source pins from the locked manifests and may
# need network access plus the Flatpak SDK.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

export LC_ALL=C

echo "== Gettext template and catalogs =="
./scripts/update-pot.sh
python3 scripts/merge-catalogs.py
python3 scripts/generate-translation-review.py
rm -f po/*.po~ po/*.pot~

echo "== Documentation map =="
python3 scripts/generate-doc-map.py

if [ "${1:-}" = "--check" ]; then
    echo "== Verification only =="
    ./scripts/update-pot.sh --check
    python3 scripts/generate-translation-review.py --check
    python3 scripts/generate-doc-map.py --check
    bash scripts/check-all.sh
    echo "UPDATE CHECK OK: generated artifacts current and every static check passed"
    exit 0
fi

if [ "${1:-}" = "--full" ]; then
    echo "== Locked packaging sources (network/SDK required) =="
    bash scripts/generate-flatpak-sources.sh
    bash scripts/refresh-dependabot-sources.sh
elif [ $# -gt 0 ]; then
    printf 'usage: %s [--full]\n' "$0" >&2
    exit 2
fi

echo "== Verification =="
bash scripts/check-all.sh

echo "UPDATE OK: generated artifacts refreshed and every consistency check passed"
