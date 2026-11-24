#!/bin/bash
# Install git hooks for Linux Defender development.
#
# Usage: ./scripts/hooks/install-hooks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [ -t 1 ]; then
    GREEN='\033[0;32m'
    BLUE='\033[0;34m'
    NC='\033[0m'
else
    GREEN=''
    BLUE=''
    NC=''
fi

printf "${BLUE}Installing git hooks...${NC}\n"
mkdir -p "$GIT_HOOKS_DIR"

if [ -f "$GIT_HOOKS_DIR/pre-commit" ]; then
    printf "  Backing up existing pre-commit hook...\n"
    mv "$GIT_HOOKS_DIR/pre-commit" "$GIT_HOOKS_DIR/pre-commit.backup"
fi

if [ -f "$GIT_HOOKS_DIR/pre-push" ]; then
    printf "  Backing up existing pre-push hook...\n"
    mv "$GIT_HOOKS_DIR/pre-push" "$GIT_HOOKS_DIR/pre-push.backup"
fi

ln -sf "../../scripts/hooks/pre-commit" "$GIT_HOOKS_DIR/pre-commit"
ln -sf "../../scripts/hooks/pre-push" "$GIT_HOOKS_DIR/pre-push"
chmod +x "$SCRIPT_DIR/pre-commit" "$SCRIPT_DIR/pre-push"

printf "${GREEN}Installed:${NC} pre-commit (all static checks + fmt/TS) and pre-push (full audit) hooks\n"
printf "\n${GREEN}Done!${NC} Git hooks installed successfully.\n"
