---
title: Getting started
description: Update ClamAV, run a first scan, and handle its result.
---

## 1. Launch the development build

Linux Defender 0.6.0 is currently a source-build snapshot. There is no published Linux Defender Flatpak, AppImage, DEB, or RPM yet. Follow [the CachyOS build steps](/Linux-Defender/docs/installation/) or [the development guide](/Linux-Defender/docs/contributing/development/); its legacy commands and identifiers are compatibility details, not an installer.

## 2. Update definitions

Open the **Database** view and check the configured host ClamAV database. FreshClam is the ClamAV updater; on CachyOS, use the system FreshClam service or timer you configured. A manual update is:

```bash
sudo freshclam
```

## 3. Run the first scan

1. In **Scan**, choose **Quick Scan** (your `~/Downloads`) or add a file/folder. Dropping local files and folders into the window works too.
2. Click **Start Scan**.
3. Review the result. Exit code/result `0` is clean, `1` means a detection, and `2` is an error.

Use the built-in **EICAR Test** once after installation to confirm detection. EICAR is a harmless industry-standard test pattern, not malware.

## 4. If a threat is found

Quarantine an unfamiliar or high-severity file first. Linux Defender verifies its SHA-256 hash before restoration. Do **not** restore a file unless you have established that it is safe. See [quarantine](/Linux-Defender/docs/guides/quarantine/) and the [FAQ](/Linux-Defender/docs/guides/faq/) for false-positive handling.

## Main views and shortcuts

The sidebar contains Scan, Database, Logs, Components, Quarantine, Statistics, Audit, and Preferences. `Ctrl+1` opens Scan, `Ctrl+2` Database, `Ctrl+3` Logs, `Ctrl+4` Components, `Ctrl+5` Quarantine, `Ctrl+6` Statistics, `Ctrl+7` Audit, and `Ctrl+,` Preferences. Choose scan profiles in the Scan view.

Next: [scan targets and results](/Linux-Defender/docs/guides/scanning/), [scan profiles](/Linux-Defender/docs/guides/profiles/), or [scheduled scans](/Linux-Defender/docs/guides/scheduling/).
