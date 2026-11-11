#!/bin/sh
# Install Nemo context menu actions for ClamUI (Flatpak version)
#
# This script copies the Nemo action files from the Flatpak to the user's
# local Nemo actions directory, enabling right-click context menu integration.
#
# Usage:
#   flatpak run --command=clamui-install-nemo-actions io.github.linx_systems.ClamUI
#
# Or from within the Flatpak environment:
#   clamui-install-nemo-actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    printf "${GREEN}[INFO]${NC} %s\n" "$1"
}

log_warn() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$1"
}

log_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1" >&2
}

# Source directory (inside Flatpak)
SOURCE_DIR="/app/share/clamui/nemo-actions"

# Destination directory (user's home)
DEST_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nemo/actions"

# Check if running inside Flatpak
if [ ! -d "$SOURCE_DIR" ]; then
    log_error "Nemo action files not found at $SOURCE_DIR"
    log_error "This script should be run from within the ClamUI Flatpak:"
    log_error "  flatpak run --command=clamui-install-nemo-actions io.github.linx_systems.ClamUI"
    exit 1
fi

# Create destination directory if it doesn't exist
log_info "Creating Nemo actions directory: $DEST_DIR"
mkdir -p "$DEST_DIR"

# Copy action files
log_info "Installing Nemo context menu actions..."

for action_file in "$SOURCE_DIR"/*.nemo_action; do
    if [ -f "$action_file" ]; then
        filename=$(basename "$action_file")
        cp "$action_file" "$DEST_DIR/$filename"
        log_info "Installed: $filename"
    fi
done

log_info ""
log_info "Nemo context menu actions installed successfully!"
log_info ""
log_info "You may need to restart Nemo for changes to take effect:"
log_info "  nemo -q"
log_info ""
log_info "After restart, right-click any file or folder to see:"
log_info "  - 'Scan with ClamUI' - Scan with local ClamAV"
log_info "  - 'Scan with VirusTotal' - Scan online (single file only)"
