#!/usr/bin/env bash
# Full local audit: heavy builds/tests + all static checks + git/CI sync.
# Static checks live in scripts/check-all.sh (single source of truth) and are
# also enforced by the pre-commit hook. Exits non-zero on first failure.
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

step "Website check / build / built-site links"
bun run --cwd website check >/dev/null || fail "website check"
bun run --cwd website build >/dev/null || fail "website build"
python3 scripts/check-built-links.py website/dist >/dev/null || fail "built-site links"

step "All static consistency checks (scripts/check-all.sh)"
bash scripts/check-all.sh || fail "static consistency checks"

step "Git sync"
LOCAL=$(git rev-parse HEAD)
if [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${SKIP_GIT_SYNC:-}" ]; then
    echo "skipping local-vs-origin sync check (CI or pre-push)"
else
    REMOTE=$(git rev-parse origin/main)
    [ "$LOCAL" = "$REMOTE" ] || fail "local HEAD $LOCAL differs from origin/main $REMOTE"
    [ -z "$(git status --short)" ] || fail "working tree is dirty"
fi

step "GitHub Actions on HEAD"
if [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${SKIP_GIT_SYNC:-}" ]; then
    echo "skipping self-CI check (CI or pre-push; workflows cannot have run yet)"
elif command -v gh >/dev/null 2>&1; then
    FAILED=$(gh run list --commit "$LOCAL" --limit 20 --json conclusion \
        --jq '[.[] | select(.conclusion=="failure" or .conclusion=="cancelled")] | length' 2>/dev/null || echo 0)
    [ "$FAILED" = "0" ] || fail "$FAILED workflow(s) failed/cancelled on HEAD"
else
    echo "gh not available; skipping CI check"
fi

printf '\nAUDIT OK: all consistency checks passed.\n'
