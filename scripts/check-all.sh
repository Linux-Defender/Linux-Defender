#!/usr/bin/env bash
# Fast, comprehensive static check for repository / app / website consistency.
# This is the SINGLE SOURCE OF TRUTH for static checks. It is called by:
#   - scripts/hooks/pre-commit  (blocks any commit that leaves drift behind)
#   - scripts/audit-consistency.sh (full local + CI audit)
#   - .github/workflows/consistency.yml (CI)
# Keep heavy builds/tests in audit-consistency.sh; keep all static checks here.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

fail() { printf 'CHECK FAIL: %s\n' "$*" >&2; exit 1; }
step() { printf '\n== %s ==\n' "$*"; }

step "Broken doc links (dead links)"
python3 scripts/check-doc-links.py || fail "doc links"

step "Orphaned docs/modules/skills (dead files)"
python3 scripts/check-dead-files.py || fail "dead files"

step "Cross-layer contracts (IPC / CLI / locales / feature matrix)"
python3 scripts/check-cross-layer.py || fail "cross-layer parity"

step "Repo-wide consistency (versions, app id, workflow/script inventory)"
python3 scripts/check-repo-consistency.py || fail "repo-wide consistency"

step "Upstream repository inventory (external URLs resolve)"
python3 scripts/tests/test_external_links.py >/dev/null 2>&1 || fail "external link checker tests"
python3 scripts/check-upstream-urls.py || fail "dead upstream URL"

step "All package formats (DEB/RPM/AppImage/Flatpak/Snap/AUR) and Sway wiring"
python3 scripts/check-packaging-consistency.py || fail "packaging consistency"
python3 scripts/check-aur-consistency.py || fail "AUR consistency"
python3 scripts/check-sway-integration.py || fail "Sway integration wiring"
python3 scripts/check-integration-parity.py || fail "integration asset parity"
python3 scripts/check-host-tool-guidance.py || fail "host-tool guidance mismatch"

step "Dev/build wiring (tauri dev -> Vite -> dist, vendored glib patch)"
python3 scripts/check-build-wiring.py || fail "build wiring"

step "Unused Rust dependencies (cargo machete)"
if command -v cargo-machete >/dev/null 2>&1; then
    machete_ok=0
    for attempt in 1 2 3; do
        if cargo machete 2>&1 | grep -q "didn't find any unused dependencies"; then
            machete_ok=1
            break
        fi
        sleep 1
    done
    [ "$machete_ok" -eq 1 ] || fail "unused Rust dependency (run cargo machete)"
else
    echo "cargo-machete not installed; skipping dependency dead-code check"
fi

step "Host ClamAV signature database (presence, age, EICAR)"
python3 scripts/tests/test_signature_check.py >/dev/null 2>&1 || fail "signature checker tests"
python3 scripts/check-signatures.py || fail "signature database"

step "Gettext current + well-formed"
python3 scripts/generate-translation-review.py --check >/dev/null || fail "translation review report stale"
./scripts/update-pot.sh --check >/dev/null || fail "POT stale"
./scripts/check-potfiles.sh >/dev/null || fail "potfiles coverage"
./scripts/check-translations.sh >/dev/null || fail "translation catalogs"
for po in po/*.po; do
    msgfmt -c --check-format -o /dev/null "$po" 2>/dev/null || fail "msgfmt $po"
    msgcmp "$po" po/linux-defender.pot >/dev/null 2>&1 || fail "msgcmp $po"
done

step "AI enforcement wiring (single source of truth, no duplicated rules)"
python3 scripts/check-ai-enforcement-wiring.py || fail "AI enforcement adapter drift"

step "Skill provenance + skill documentation wiring"
python3 - <<'PY' || fail "skill check"
import hashlib, json
from pathlib import Path
lock = json.load(open("skills-lock.json"))["skills"]
for name, meta in lock.items():
    p = Path(f".agents/skills/{name}/SKILL.md")
    if not p.exists():
        raise SystemExit(f"missing imported skill: {name}")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != meta.get("computedHash"):
        raise SystemExit(f"skill hash mismatch: {name} (lock {meta.get('computedHash')[:12]}, local {h[:12]})")
# Every local skill must be discoverable from the AI entry-point documents,
# otherwise it is effectively forgotten by future agents/models.
guides = "\n".join(
    Path(p).read_text() for p in ("AGENTS.md", "CLAUDE.md",
    "website/src/content/docs/docs/contributing/development.md") if Path(p).exists()
)
for skill in sorted(Path(".agents/skills").glob("*/SKILL.md")):
    name = skill.parent.name
    if name not in guides:
        raise SystemExit(f"skill not wired into AGENTS.md/CLAUDE.md/dev guide: {name}")
PY

step "Doc indexes, complete map, and known-stale claims"
python3 scripts/check-doc-indexes.py || fail "doc index coverage"
python3 scripts/generate-doc-map.py --check || fail "documentation map stale (run generate-doc-map.py)"
python3 scripts/check-stale-phrases.py || fail "stale documentation claim"

step "Stale brand references"
STALE=$(grep -rniE 'clamui\.com|linx\.systems|clamui@|rooki\.xyz|io\.github\.linx' \
    --include='*.rs' --include='*.ts' --include='*.tsx' --include='*.toml' \
    --include='*.json' --include='*.yml' --include='*.yaml' --include='*.sh' \
    --include='*.md' --include='*.txt' . 2>/dev/null \
    | grep -vE '^\./(target|node_modules|\.git|po|\.agents)/' \
    | grep -vE '^\./scripts/(audit-consistency|check-all)\.sh:' \
    | grep -viE 'docs/revival|docs/clamui-fork|CHANGELOG|LICENSE|compatibility|historical|migration|pre-rename|upstream|\.var/app/io\.github|uninstall\.sh.*remove_file' || true)
[ -z "$STALE" ] || { printf '%s\n' "$STALE" >&2; fail "stale brand references in live files"; }

step "Dead frontend modules"
DEAD=""
for dir in desktop/src desktop/src/pages; do
    for f in "$dir"/*.ts "$dir"/*.tsx; do
        [ -f "$f" ] || continue
        base=$(basename "$f")
        mod=${base%.*}
        case "$mod" in index|main|vite-env|*.test) continue ;; esac
        if ! grep -rq --include='*.ts' --include='*.tsx' --exclude="$base" "\\b$mod\\b" desktop/src 2>/dev/null; then
            DEAD="$DEAD $f"
        fi
    done
done
[ -z "$DEAD" ] || { printf 'Dead modules:%s\n' "$DEAD" >&2; fail "unused frontend modules (wire or remove)"; }

step "Website sidebar + component wiring"
python3 - <<'PY' || fail "sidebar target missing"
import re
from pathlib import Path
cfg = Path("website/astro.config.mjs").read_text()
for doc_id in re.findall(r'"(docs(?:/[^"]*)?)"', cfg):
    base = Path(f"website/src/content/docs/{doc_id}")
    if not any(p.exists() for p in (base.with_suffix(".md"), base.with_suffix(".mdx"), base / "index.md")):
        raise SystemExit(f"sidebar target missing: {doc_id}")
PY
python3 - <<'PY' || fail "unused website component"
from pathlib import Path
src = "\n".join(p.read_text() for p in Path("website/src").rglob("*.astro"))
for comp in sorted(Path("website/src/components").glob("*.astro")):
    name = comp.stem
    if not any(name in line and "import" in line for line in src.splitlines()):
        raise SystemExit(f"unused website component: {name}")
PY

printf '\nCHECK OK: all static consistency checks passed.\n'
