#!/usr/bin/env bash
# Full local audit: formatting, lints, tests, frontend, website, gettext,
# stale references, dead frontend modules, git sync, and CI status.
# Exits non-zero on the first failure. Safe to run before any push.
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

fail() { printf 'AUDIT FAIL: %s\n' "$*" >&2; exit 1; }
step() { printf '\n== %s ==\n' "$*"; }

step "Frontend type-check / build / tests (needed before clippy: generate_context! embeds dist)"
bun run --cwd desktop check >/dev/null || fail "desktop check (tsc)"
bun run --cwd desktop build >/dev/null || fail "desktop build"
( cd desktop && bun test >/dev/null ) || fail "desktop tests"

step "Rust format"
cargo fmt --check --all || fail "cargo fmt --check --all"

step "Rust clippy (-D warnings)"
cargo clippy --workspace --all-targets --locked -- -D warnings >/dev/null || fail "cargo clippy"

step "Rust tests"
cargo test --workspace --locked >/dev/null || fail "cargo test --workspace"

step "Website check / build / links / assets"
bun run --cwd website check >/dev/null || fail "website check"
bun run --cwd website build >/dev/null || fail "website build"
python3 scripts/check-built-links.py website/dist >/dev/null || fail "built-site links"
# Every Starlight sidebar entry in astro.config.mjs must resolve to a real doc.
python3 - <<'PY' || fail "sidebar target missing"
import re
from pathlib import Path
cfg = Path("website/astro.config.mjs").read_text()
ids = re.findall(r'"(docs(?:/[^"]*)?)"', cfg)
for doc_id in ids:
    doc = Path(f"website/src/content/docs/{doc_id}.md")
    mdx = Path(f"website/src/content/docs/{doc_id}.mdx")
    index = Path(f"website/src/content/docs/{doc_id}/index.md")
    if not (doc.exists() or mdx.exists() or index.exists()):
        raise SystemExit(f"sidebar target missing: {doc_id}")
PY
# No dead website components: every .astro in src/components must be imported.
python3 - <<'PY' || fail "unused website component"
from pathlib import Path
comps = {p.stem for p in Path("website/src/components").glob("*.astro")}
src = "\n".join(p.read_text() for p in Path("website/src").rglob("*.astro"))
for name in sorted(comps):
    if name not in src.replace(f"components/{name}.astro", ""):
        # crude but effective: the component name must appear in an import line
        if not any(f"{name}" in line and "import" in line for line in src.splitlines()):
            raise SystemExit(f"unused website component: {name}")
PY

step "Gettext current + well-formed"
./scripts/update-pot.sh --check >/dev/null || fail "POT stale"
./scripts/check-potfiles.sh >/dev/null || fail "potfiles coverage"
./scripts/check-translations.sh >/dev/null || fail "translation catalogs"
for po in po/*.po; do
    msgfmt -c --check-format -o /dev/null "$po" 2>/dev/null || fail "msgfmt $po"
    msgcmp "$po" po/linux-defender.pot >/dev/null 2>&1 || fail "msgcmp $po"
done

step "Skill provenance (imported payloads match skills-lock.json)"
python3 - <<'PY' || fail "imported skill hash mismatch"
import json, hashlib
from pathlib import Path
lock = json.load(open("skills-lock.json"))["skills"]
for name, meta in lock.items():
    p = Path(f".agents/skills/{name}/SKILL.md")
    if not p.exists():
        raise SystemExit(f"missing imported skill: {name}")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != meta.get("computedHash"):
        raise SystemExit(f"skill hash mismatch: {name} (lock {meta.get('computedHash')[:12]}, local {h[:12]})")
PY

step "Stale brand references"
# Only intentional historical/compat references may contain these tokens.
# The audit script and parity skill contain the pattern itself; exclude them.
STALE=$(grep -rniE 'clamui\.com|linx\.systems|clamui@|rooki\.xyz|io\.github\.linx' \
    --include='*.rs' --include='*.ts' --include='*.tsx' --include='*.toml' \
    --include='*.json' --include='*.yml' --include='*.yaml' --include='*.sh' \
    --include='*.md' --include='*.txt' . 2>/dev/null \
    | grep -vE '^\./(target|node_modules|\.git|po|\.agents)/' \
    | grep -vE '^\./scripts/audit-consistency\.sh:' \
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
        # A module is live if another source file references its basename.
        if ! grep -rq --include='*.ts' --include='*.tsx' --exclude="$base" "\\b$mod\\b" desktop/src 2>/dev/null; then
            DEAD="$DEAD $f"
        fi
    done
done
[ -z "$DEAD" ] || { printf 'Dead modules:%s\n' "$DEAD" >&2; fail "unused frontend modules (wire or remove)"; }

step "Git sync"
LOCAL=$(git rev-parse HEAD)
if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "running inside GitHub Actions; skipping local-vs-origin sync check"
else
    REMOTE=$(git rev-parse origin/main)
    [ "$LOCAL" = "$REMOTE" ] || fail "local HEAD $LOCAL differs from origin/main $REMOTE"
    [ -z "$(git status --short)" ] || fail "working tree is dirty"
fi

step "GitHub Actions on HEAD"
if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "running inside GitHub Actions; skipping self-CI check"
elif command -v gh >/dev/null 2>&1; then
    FAILED=$(gh run list --commit "$LOCAL" --limit 20 --json conclusion \
        --jq '[.[] | select(.conclusion=="failure" or .conclusion=="cancelled")] | length' 2>/dev/null || echo 0)
    [ "$FAILED" = "0" ] || fail "$FAILED workflow(s) failed/cancelled on HEAD"
else
    echo "gh not available; skipping CI check"
fi

printf '\nAUDIT OK: all consistency checks passed.\n'
