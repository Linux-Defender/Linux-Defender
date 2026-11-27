---
title: Frequently asked questions
description: Practical answers for scanning, detections, performance, and external drives.
---

## Is Linux Defender the antivirus engine?

No. Linux Defender is the desktop interface; [ClamAV](https://www.clamav.net/) performs detection. All package formats require host `clamscan` and `freshclam`; daemon mode adds `clamd` and `clamdscan`.

## Which signatures does it use?

ClamAV loads compatible signature files from its configured database directory. Linux Defender shows a recognized-file inventory and can pass selected local YARA files alongside that database for standalone scans. It does not yet install or automatically update every third-party feed. FreshClam and the system package/service own the shared ClamAV database.

## Can I check a website URL or a folder with VirusTotal?

Yes. Choose **Website URL** in Scan to use VirusTotal or urlscan. VirusTotal also accepts file and confirmed folder uploads. These are online reputation checks: Linux Defender asks before sending data and keeps their results separate from the local ClamAV verdict. Review the provider's privacy and visibility terms before submitting.

## Is Linux Defender 0.6.0 ready to install?

Not yet. It is a development snapshot with no signed Linux Defender package published. Use the source-build steps in [Installation and testing](/Linux-Defender/docs/installation/). ClamTk data migration and release signing remain open. An initial Sway/CachyOS tray and window pass is recorded in the [tray guide](/Linux-Defender/docs/guides/tray/); right-click actions, minimize/restore during a scan, and portal dialogs still need interactive validation.

## What distributions are supported?

No Linux Defender packages are published yet, so no distribution has a released support claim. Build targets exist for Ubuntu/Debian (DEB), Fedora (helper RPM), Flatpak, AppImage, Snap, and Arch/CachyOS (local AUR source recipes); an initial Sway/CachyOS window and tray pass is recorded but interactive checks remain open. The app needs GTK 3 and WebKitGTK 4.1. See the [installation guide](/Linux-Defender/docs/installation/) for the per-target status.

## How often should I scan?

A practical default is daily Downloads scans and a weekly Home Folder scan. Use a Full Scan after a high-risk event or periodically when the computer is idle. Keep definitions updated more often than you scan.

## What should I do when a scan detects something?

Do not execute it. Quarantine unknown, critical, or high-severity files first; inspect source, hash, and intended use; then delete confirmed malware or restore only a confirmed false positive. Severity is a name-based clue, not a verdict. Do not upload confidential files to VirusTotal or another third party.

## Are false positives possible?

Yes, especially for heuristic, packed, administrative, and potentially unwanted tools. Update definitions, research the exact detection, check provenance and hashes, and compare independent engines only when disclosure is acceptable. Keep a suspicious file quarantined while deciding. Report confirmed false-positive detections to the [ClamAV project](https://github.com/Cisco-Talos/clamav/issues/new/choose), including the exact signature name, file hash, and why the file is legitimate. Linux Defender does not maintain the signature database; it uses the host ClamAV definitions.

## Will scans slow down my system?

They can be CPU- and disk-intensive. A running daemon avoids reloading definitions and is best for recurring scans. Prefer targeted schedules and narrow, justified exclusions; do not reduce protection or set unlimited archive limits merely for speed.

## Is quarantine safe?

It is reversible isolation with owner-only storage and SHA-256 verification on restore. It is not a backup: deletion and clearing old items are permanent, and manual file changes bypass metadata and integrity protections.

## Can I scan USB, external, or network drives?

Yes. Scan a mounted path manually or enable Device Scan for removable, external, and optionally network mounts. Review results before opening files, scan unfamiliar media before use, and do not disconnect it while scanning.
