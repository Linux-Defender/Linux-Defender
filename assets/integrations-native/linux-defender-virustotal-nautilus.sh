#!/bin/bash
# Linux Defender VirusTotal Scanner - Nautilus Script
# This script is installed to ~/.local/share/nautilus/scripts/
# and provides a "Scan with VirusTotal" context menu option.
#
# Usage: Called by Nautilus file manager when selecting "Scripts > Scan with VirusTotal"
# The selected files are passed via NAUTILUS_SCRIPT_SELECTED_FILE_PATHS environment variable.

# Enable logging for debugging
LOG_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/linux-defender/virustotal-nautilus.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Never log selected paths or arguments: they can contain private file names.
# Only counts and status are recorded.
log "Script started"

# Prefer the canonical command. The pre-rename name is still accepted so this
# script keeps working on an install that has not been upgraded yet.
if command -v linux-defender &> /dev/null; then
    LAUNCHER=linux-defender
elif command -v clamui &> /dev/null; then
    LAUNCHER=clamui
else
    log "ERROR: Linux Defender is not installed (no linux-defender command was found)"
    # Try to notify user
    if command -v notify-send &> /dev/null; then
        notify-send "Linux Defender Not Found" "Please install Linux Defender to use VirusTotal scanning."
    fi
    exit 1
fi

log "Linux Defender launcher found"

# Get selected files from Nautilus
# NAUTILUS_SCRIPT_SELECTED_FILE_PATHS contains newline-separated paths
if [[ -n "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS" ]]; then
    # Convert newline-separated paths to array
    IFS=$'\n' read -d '' -r -a files <<< "$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"

    log "Found ${#files[@]} files from NAUTILUS_SCRIPT_SELECTED_FILE_PATHS"

    # Launch Linux Defender with --virustotal for the first file.
    # (VirusTotal only supports single file scanning)
    if [[ ${#files[@]} -gt 0 ]]; then
        log "Launching VirusTotal check for the first of ${#files[@]} selected path(s)"
        "$LAUNCHER" --virustotal "${files[0]}" 2>&1 | tee -a "$LOG_FILE"
        log "Linux Defender exited with code: ${PIPESTATUS[0]}"
    else
        log "ERROR: No files in array"
    fi
else
    # Fallback: try to use positional arguments
    if [[ $# -gt 0 ]]; then
        log "Using $# positional argument(s)"
        log "Launching Linux Defender's VirusTotal check for the selected file"
        "$LAUNCHER" --virustotal "$1" 2>&1 | tee -a "$LOG_FILE"
        log "Linux Defender exited with code: ${PIPESTATUS[0]}"
    else
        log "ERROR: No files provided (neither env var nor arguments)"
        if command -v notify-send &> /dev/null; then
            notify-send "Linux Defender VirusTotal" "No file selected for scanning."
        fi
    fi
fi

log "Script finished"
