---
title: Set preferences
description: Choose app behavior, host ClamAV options, device scans, and diagnostics.
---

Open **Preferences** with `Ctrl+,`. Most app preferences and exclusions save immediately. **Scheduled Scans** need **Save & Apply** to persist their settings and provision the scheduler; changes to host `freshclam.conf` or `clamd.conf` also need **Save & Apply** and elevated host access.

## Choose the right page

| Task | Page |
| --- | --- |
| Language, close behavior, tray startup, live progress, manual update timeout | Behavior |
| Select ClamAV mode and socket | Scanner |
| Schedule recurring scans | Scheduled Scans |
| Definition update settings | Database |
| Local YARA rules folder | YARA Rules |
| Global exclusion records | Exclusions |
| Mounted-device scanning | Device Scan |
| On-access ClamAV monitoring | On-Access |
| VirusTotal API key | VirusTotal |
| Debug logging | Debugging |

For every raw key, default, location, and host boundary see [Configuration](/Linux-Defender/docs/reference/configuration/).

## Language

Open **Preferences → Behavior → Language** to use **Automatic (System)** or choose `de`, `en`, `es`, `fr`, `hu`, `it`, `nb`, `pt_BR`, `vi`, or `zh_CN`. Restart Linux Defender after changing the selection so the core, CLI, tray, and desktop load the same catalog. See [translation](/Linux-Defender/docs/contributing/translating/) for regional locale normalization and plural-form conventions.

## Database update timeout

In **Preferences → Behavior → Database Updates**, set **Update inactivity timeout (minutes)** to a whole number from 1 to 1440. It saves automatically and applies to manual and forced updates started afterwards. The default is 10 minutes; zero does not disable the timeout.

The timeout measures time without any `freshclam` standard-output or standard-error bytes, not total update duration. An update that continues producing output can run longer than the configured limit. Updates requested by signaling the existing service do not use this limit.

## Global scan exclusions

Open **Preferences → Exclusions**. Use **Add Files** or **Add Folders** to choose one or more files or folders with the native dialog. Alternatively, enter an absolute file path or a pattern such as `*.tmp`, then choose **Add**. Manual absolute paths are file exclusions; use **Add Folders** for directory exclusions.

Use an entry's checkbox to enable or disable it without removing it. Changes save immediately.

## Host configuration warning

Database, Scanner, and On-Access settings change host `/etc/clamav`, not Flatpak files. They need the trusted canonical native `/usr/bin/clamui-apply-preferences` helper and polkit approval. Native helper readiness does not depend on unavailable automatic-install support or installed-package metadata; a successfully reported version or architecture mismatch is reported as outdated and prompts repair, while every untrusted helper remains blocked. Flatpak continues to validate its host package state. Where offered, automatic setup requires explicit action and validates matching newly published, signed Rust release assets. Its protected-host protocol rejects unauthorized or invalid writes; if the helper is unavailable, saving fails without modifying host configuration. Exclusions and normal application settings remain local to Linux Defender.

## Local YARA rules

In **Preferences → YARA Rules**, choose a folder containing rules you trust. Only regular `.yar` and `.yara` files are loaded. ClamAV supports a subset of YARA syntax; the standalone `clamscan` backend passes the configured system database together with those rule files. Local YARA rules do not install or update third-party ClamAV feeds.

## Safe defaults

Use **Auto** backend unless you know you need daemon-only behavior; leave notifications on for scheduled scans; prefer narrow exclusions; and preserve finite archive limits. On-access scanning requires `clamd`, careful include paths, and exclusions for the scanner account to prevent loops. Start with a small path such as `~/Downloads`.

VirusTotal keys use the system keyring when available, not `settings.json`; plaintext fallback requires explicit consent. File, folder, VirusTotal URL, and urlscan checks are optional and require confirmation. Do not submit private files or URLs you are not authorized to share.
