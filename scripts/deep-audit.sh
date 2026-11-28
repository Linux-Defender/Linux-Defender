#!/usr/bin/env bash
# Canonical deep audit for Linux Defender: one command that regenerates-checks
# every derived artifact, runs every static and full gate, verifies parity,
# signatures, images, packaging and CI, then prints a fleet brief so any AI
# assistant or human can repeat the exhaustive review.
#
#   ./scripts/deep-audit.sh            # full: static + builds + tests + CI status
#   ./scripts/deep-audit.sh --quick    # static checks only (MCP/plugin safe)
#   ./scripts/deep-audit.sh --fleet    # print the agent-fleet brief only
#
# The report is written outside the repository (no generated files in git).
set -uo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"
REPORT="${TMPDIR:-/tmp/opencode}/linux-defender-deep-audit.md"
mkdir -p "$(dirname "$REPORT")"
: > "$REPORT"

failures=0
step() { printf '\n== %s ==\n' "$*" | tee -a "$REPORT"; }
run() {
    local label="$1"; shift
    printf '\n--- %s ---\n' "$label" | tee -a "$REPORT"
    if "$@" >>"$REPORT" 2>&1; then
        printf 'OK: %s\n' "$label" | tee -a "$REPORT"
    else
        printf 'FAIL: %s\n' "$label" | tee -a "$REPORT"
        failures=$((failures + 1))
    fi
}

fleet_brief() {
    cat <<'EOF'
Agent fleet brief — spawn read-only agents for these domains when a deeper
manual review is requested. Each agent must report file:line, severity, and a
concrete fix; no agent edits, commits, or pushes.

1 Rust core security 2 Tauri runtime/IPC 3 React frontend/a11y 4 Website/CSS
5 Gettext/locales 6 Native packaging (DEB/RPM/AppImage) 7 Sandbox packaging
(Flatpak/Snap/AUR) 8 Workflows/guards 9 Docs/stale refs 10 ClamUI upstream
11 ClamTk/Lenspect upstream 12 Dependency advisories 13 Images/captures
14 CLI/data compatibility 15 Scheduler/privacy 16 Test coverage
17 MCP server 18 Install guidance 19 License/provenance 20 Release readiness
21 Cross-layer contracts 22 Universal entry/format parity 23 Final reconciliation.

Reports: docs/revival/CHAT-AND-PROJECT-AUDIT.md (ledger),
docs/revival/RELATED-PROJECT-REVIEW.md (parity + deferrals),
docs/DOC-MAP.md (all docs), docs/documentation/SCRIPTS.md (all tooling).
EOF
}

if [ "${1:-}" = "--fleet" ]; then
    fleet_brief
    exit 0
fi

step "Repository state"
printf 'HEAD %s origin %s\n' "$(git rev-parse --short HEAD)" "$(git rev-parse --short origin/main)" | tee -a "$REPORT"
printf 'dirty files %s\n' "$(git status --short | wc -l)" | tee -a "$REPORT"

step "Generated artifacts and static gates"
run "update-all.sh --check" bash scripts/update-all.sh --check
run "check-all.sh" bash scripts/check-all.sh

step "Parity and maintenance guards"
for checker in check-format-coverage check-screenshot-branding check-boot-diagnostics \
               check-website-a11y check-release-profile check-ipc-operations \
               check-support-parity check-upstream-freshness check-signatures \
               check-signature-feeds check-external-links check-gate-wiring \
               check-scripts-index check-file-modes; do
    run "$checker" python3 "scripts/$checker.py"
done

if [ "${1:-}" != "--quick" ]; then
    step "Full audit: builds, tests, clippy, git/CI sync"
    run "audit-consistency.sh" env GITHUB_ACTIONS=true bash scripts/audit-consistency.sh

    step "GitHub Actions status on HEAD"
    if command -v gh >/dev/null 2>&1 && [ -z "${GITHUB_ACTIONS:-}" ]; then
        SHA="$(git rev-parse HEAD)"
        CI_OUT=$(gh api "repos/Linux-Defender/Linux-Defender/actions/runs?head_sha=$SHA&per_page=100" \
            --jq '[.workflow_runs[] | select(.status!="completed" or .conclusion!="success") | .name] | if length==0 then "CI OK: all workflows green" else "CI PENDING/FAIL: " + join(", ") end' 2>&1)
        printf '%s\n' "$CI_OUT" >>"$REPORT"
        case "$CI_OUT" in
            "CI OK: all workflows green") ;;
            *) failures=$((failures + 1)) ;;
        esac
    else
        printf 'CI status skipped (CI context)\n' >>"$REPORT"
    fi
fi

step "Agent fleet brief"
fleet_brief | tee -a "$REPORT"

printf '\nDEEP AUDIT %s: %s failure(s). Report: %s\n' \
    "$([ "$failures" -eq 0 ] && echo OK || echo FAIL)" "$failures" "$REPORT"
[ "$failures" -eq 0 ]
