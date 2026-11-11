---
title: Scan files and folders
description: Select targets, interpret results, and test detection safely.
---

## Start a scan

In **Scan**, choose **File** or **Folder** in the header to add a target, select a saved profile, or drag local targets into the window. Choose **Quick Scan** there to scan `~/Downloads`; the application menu contains the window's common actions. Folders scan recursively. Invalid, missing, inaccessible, or protected targets are rejected before the scan begins.

For one-off integrations, launch with paths:

```bash
clamui /path/to/file /path/to/folder
```

The source build still uses the compatibility command name `clamui`; a Linux Defender Flatpak is not published yet. Headless use is available through `clamui scan`; run `clamui scan --help` for the current options. Its standard ClamAV exit codes are `0` clean, `1` infected, and `2` error. Most Linux Defender subcommands accept `--json` for scripts.

## Select the right scan

| Need | Best choice |
| --- | --- |
| New download | Scan the file or use **Quick Scan** |
| Personal files | **Home Folder** profile |
| System-wide review | **Full Scan** when the machine is idle |
| Recurring work | [Scheduled scan](/Linux-Defender/docs/guides/scheduling/) |
| New removable media | Scan its mount point, or enable device auto-scan |

**Quick Scan** targets `~/Downloads`. **Full Scan** targets `/` and excludes `/proc`, `/sys`, `/dev`, `/run`, `/tmp`, `/var/cache`, and `/var/tmp`. **Home Folder** targets `~` and excludes `~/.cache` and `~/.local/share/Trash`.

## Results and detections

Linux Defender displays clean, infected, error, or cancelled results with a file path and ClamAV detection name. A cancelled scan keeps the partial result collected before cancellation. Severity badges are guidance derived from detection names, not proof of actual malware behavior. Treat critical/high detections urgently; for uncertain, low, or heuristic detections, quarantine first and investigate.

**Quarantine** copies the file to owner-only storage, hashes it with SHA-256, and verifies that hash when restoring. It is safer than deleting immediately. See [quarantine](/Linux-Defender/docs/guides/quarantine/).

Open **Scan Details** for an expanded result view. Choose **Copy** to place the displayed details on the clipboard.

The **Scan Details** dialog keeps focus inside it: use `Tab` and `Shift+Tab` to move between **Copy** and **Close**. `Escape` closes it and returns focus to its **Fullscreen** opener.

When notifications are enabled and permitted by the desktop, a completed scan sends a native notification. Use its **Show Scan** action to return to the scan results.

## Optional online reputation checks

Choose **Website URL** in Scan to submit a URL to VirusTotal or urlscan. Linux Defender asks you to confirm before sending it. VirusTotal URL submissions are added to its analysis dataset and may be shared with its security partners; urlscan offers **Private**, **Unlisted**, and **Public** visibility choices. Read the provider's terms and choose the visibility deliberately: [VirusTotal data use](https://docs.virustotal.com/docs/how-it-works), [urlscan visibility](https://docs.urlscan.io/pages/visibility).

VirusTotal also supports file lookups and uploads, including a bounded, user-confirmed folder-upload flow with visible progress. Any uploaded file leaves your device. Its result is an online reputation report, not the local ClamAV scan result. The app does not submit files or URLs automatically.

## Test with EICAR

Use the built-in **EICAR Test** button after installation. It creates a harmless, standard detection test; delete or quarantine the resulting EICAR item when finished. Do not test with real malware.

## Removable and network storage

Enable **Preferences → Device Scan** to scan `removable`, `external`, and optionally `network` mounts. Set a maximum size (`0` means unlimited), a post-mount delay, notifications, optional auto-quarantine, and battery skipping. Review targets and results before opening files; never disconnect a device during its scan.

## Speed and safety

A daemon keeps signatures in memory and is better for repeated scans. Exclusions can reduce work, but never exclude the whole target, Downloads, or documents just to make a scan finish faster. Archive limits protect against resource-exhaustion archives; configure them in [Configuration](/Linux-Defender/docs/reference/configuration/).
