#!/bin/sh
# Install Nemo context-menu actions for Linux Defender from a source checkout.
#
# Linux Defender also installs these actions at runtime through platform.rs;
# this helper is for people who want to install them from the repository
# without starting the app. Run it from any directory:
#
#   ./scripts/install-nemo-actions.sh
#
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/../assets/integrations-native"
DEST_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nemo/actions"

if [ ! -d "$SOURCE_DIR" ]; then
    printf '[ERROR] Nemo action assets not found at %s\n' "$SOURCE_DIR" >&2
    exit 1
fi

printf '[INFO] Creating Nemo actions directory: %s\n' "$DEST_DIR"
mkdir -p "$DEST_DIR"

installed=0
for action_file in "$SOURCE_DIR"/*.nemo_action; do
    [ -f "$action_file" ] || continue
    filename=$(basename "$action_file")
    cp "$action_file" "$DEST_DIR/$filename"
    printf '[INFO] Installed: %s\n' "$filename"
    installed=$((installed + 1))
done

if [ "$installed" -eq 0 ]; then
    printf '[ERROR] No .nemo_action files found in %s\n' "$SOURCE_DIR" >&2
    exit 1
fi

printf '[INFO] Installed %s Nemo action(s).\n' "$installed"
printf '[INFO] Restart Nemo with `nemo -q` if the actions do not appear immediately.\n'
