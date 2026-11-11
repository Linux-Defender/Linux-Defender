---
title: Scan backends
description: Choose auto, daemon, or standalone ClamAV scanning.
---

Set the backend in **Preferences → Scanner Settings** or `scan_backend` in `settings.json`.

| Backend | Startup | Idle memory | Use it when |
| --- | --- | --- | --- |
| Auto (default) | daemon if reachable; otherwise `clamscan` | about 50 MB without daemon | Most desktops |
| Daemon | immediate | 500 MB–1 GB for `clamd` | Frequent, scheduled, or performance-sensitive scans |
| Clamscan | loads definitions each scan (about 3–10 seconds) | about 50 MB | Occasional scans, minimal setup, or daemon diagnosis |

Auto checks `clamdscan --ping` and caches availability for 60 seconds. Daemon mode uses `--fdpass`; scans fail when the daemon is down. `clamscan` has no background service and forwards relevant `clamd.conf` limits (`MaxFileSize`, `MaxScanSize`, `MaxRecursion`, and `MaxFiles`) as CLI limits so both modes remain consistent.

Daemon scans batch ordinary paths in a private file list. Files whose names contain carriage returns or newlines are scanned individually through open file descriptors, so these valid filenames do not abort their parent-folder scan. Exclusions still apply, and detections retain the original paths.

## Signatures and local YARA rules

Both ClamAV backends use the host's configured database directory, including compatible files such as official CVD/CLD databases and supported custom signature formats. The Database page lists file types it recognizes; that inventory cannot prove which signatures a running `clamd` has loaded. Linux Defender does not automatically install or update third-party feeds. FreshClam updates the shared host database using the system configuration and service or timer.

Selected `.yar` and `.yara` files can be added in **Preferences → YARA Rules**. ClamAV implements a subset of YARA syntax, and Linux Defender combines these rules with the host database for standalone `clamscan`; it refuses a YARA-only scan without a readable ClamAV database. See the [ClamAV signature-format guide](https://docs.clamav.net/manual/Signatures.html) and [YARA support notes](https://docs.clamav.net/manual/Signatures/YaraRules.html).

## Install a daemon

```bash
# Debian/Ubuntu
sudo apt install clamav-daemon
sudo systemctl enable --now clamav-daemon
clamdscan --version

# Fedora
sudo dnf install clamd clamav-freshclam
sudo freshclam
sudo systemctl enable --now clamd@scan

# Arch Linux
sudo pacman -S clamav
sudo systemctl enable --now clamav-daemon
```

Fedora uses `/etc/clamd.d/scan.conf`; Linux Defender invokes `clamdscan --config-file=/etc/clamd.d/scan.conf`. If a running Fedora daemon is unavailable, check its `LocalSocketMode` and `LocalSocketGroup`.

Flatpak users install all ClamAV tools on the **host**. Linux Defender invokes them through `flatpak-spawn --host` and auto-detects the host daemon.

Database availability is checked on the host too, including `DatabaseDirectory` from the configured `clamd.conf` or `freshclam.conf`. Do not copy host definitions into the sandbox; read-only database detection does not require the privileged helper.

## Sockets and exit codes

Linux Defender probes `/var/run/clamav/clamd.ctl`, `/run/clamav/clamd.ctl`, `/run/clamd.scan/clamd.sock`, and `/var/run/clamd.scan/clamd.sock`, after checking configured `LocalSocket`. Override with `daemon_socket_path` when necessary.

```bash
grep "LocalSocket" /etc/clamav/clamd.conf
grep "LocalSocket" /etc/clamd.d/scan.conf
```

Both modes use standard ClamAV codes: `0` clean, `1` detection, and `2` error. See [Configuration](/Linux-Defender/docs/reference/configuration/) for overrides and [Troubleshooting](/Linux-Defender/docs/troubleshooting/) for failures.
