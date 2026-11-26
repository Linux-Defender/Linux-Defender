#!/bin/bash
# Linux Defender Scanner - Nautilus Script (Flatpak version)
# This script is installed to ~/.local/share/nautilus/scripts/
# and provides a "Scan with Linux Defender" context menu option.
#
# Usage: Called by Nautilus file manager when selecting "Scripts > Scan with Linux Defender"
# The selected files are passed via NAUTILUS_SCRIPT_SELECTED_FILE_PATHS environment variable.

# Enable logging for debugging
LOG_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/linux-defender/scan-nautilus.log"
mkdir -p -m 700 "$(dirname "$LOG_FILE")"
chmod 600 "$LOG_FILE" 2>/dev/null || :

log() {
	echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >>"$LOG_FILE"
}

log "Script started (Flatpak version)"
# Never log selected paths or arguments: they can contain private file names.
# Only counts and status are recorded.

# Check if Linux Defender Flatpak is available
if ! flatpak info io.github.linuxdefender.linuxdefender &>/dev/null; then
	log "ERROR: Linux Defender Flatpak not installed"
	# Try to notify user
	if command -v notify-send &>/dev/null; then
		notify-send "Linux Defender Not Found" "Please install Linux Defender Flatpak to use ClamAV scanning."
	fi
	exit 1
fi

log "Linux Defender Flatpak found"

# Get selected files from Nautilus
# NAUTILUS_SCRIPT_SELECTED_FILE_PATHS contains newline-separated paths
if [[ -n "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS" ]]; then
	# Convert newline-separated paths to array
	IFS=$'\n' read -d '' -r -a files <<<"$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"

	log "Found ${#files[@]} files from NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"

	# Launch Linux Defender with all selected files
	if [[ ${#files[@]} -gt 0 ]]; then
		log "Launching Linux Defender for ${#files[@]} selected path(s)"
		flatpak run io.github.linuxdefender.linuxdefender "${files[@]}" >/dev/null 2>&1
		log "Linux Defender exited with code: $?"
	else
		log "ERROR: No files in array"
	fi
else
	# Fallback: try to use positional arguments
	if [[ $# -gt 0 ]]; then
		log "Using $# positional argument(s)"
		log "Launching Linux Defender for $# positional argument(s)"
		flatpak run io.github.linuxdefender.linuxdefender "$@" >/dev/null 2>&1
		log "Linux Defender exited with code: $?"
	else
		log "ERROR: No files provided (neither env var nor arguments)"
		if command -v notify-send &>/dev/null; then
			notify-send "Linux Defender" "No file selected for scanning."
		fi
	fi
fi

log "Script finished"
