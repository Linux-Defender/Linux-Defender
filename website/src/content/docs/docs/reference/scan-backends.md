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

Linux Defender ships **one active, MIT-authored YARA rule by default**: it matches only the standard EICAR test string and is applied to standalone `clamscan` scans alongside the host database. It cannot match legitimate content, and daemon scans keep their original behavior. Clear or replace `<data-dir>/yara/linux-defender-default.yar`, or configure your own rules folder, to change it. No other `.yar`/`.yara` file is bundled in any package format. A ClamAV-validated example (`assets/yara/linux-defender-examples.yar.example`) is included and can be copied from **Preferences → YARA Rules**; it stays inert until you save it into your rules folder as `.yar`.

```yara
rule LinuxDefender_Example_EICAR_Test {
    strings:
        $eicar = "EICAR-STANDARD-ANTIVIRUS-TEST-FILE"
    condition:
        $eicar
}
``` Selected `.yar` and `.yara` files can be added in **Preferences → YARA Rules** (at most 1,000 files, 8 MiB per file, 64 MiB total; symlinks and non-UTF-8 names are skipped). ClamAV implements a subset of YARA syntax, and Linux Defender combines these rules with the host database for standalone `clamscan`; it refuses a YARA-only scan without a readable ClamAV database. See the [ClamAV signature-format guide](https://docs.clamav.net/manual/Signatures.html) and [YARA support notes](https://docs.clamav.net/manual/Signatures/YaraRules.html).

## Install a daemon

The commands below are copy-only: Linux Defender never installs packages or
starts services for you. Run them as an administrator on the host. The app's
Components page offers the same per-family commands: **Ubuntu/Debian**
`sudo apt install clamav`, **Fedora Workstation** `sudo dnf install clamav`,
**Fedora Atomic** `sudo rpm-ostree install clamav`, **Arch Linux**
`sudo pacman -S clamav`, and **openSUSE Tumbleweed/Leap**
`sudo zypper install clamav`. FreshClam equivalents are `sudo apt install clamav-freshclam` (Ubuntu/Debian), `sudo dnf install clamav-freshclam` (Fedora Workstation), `sudo rpm-ostree install clamav-freshclam` (Fedora Atomic), `sudo pacman -S clamav` (Arch Linux), and `sudo zypper install clamav` (openSUSE Tumbleweed/Leap). For daemon diagnosis on Fedora use
`clamdscan --config-file=/etc/clamd.d/scan.conf --ping 3`.

```bash
# Debian/Ubuntu
sudo apt install clamav-daemon
sudo systemctl enable --now clamav-daemon
clamdscan --version

# Fedora
sudo dnf install clamd clamav-freshclam
sudo freshclam
sudo systemctl enable --now clamd@scan

# Fedora Atomic
sudo rpm-ostree install clamd clamav-freshclam
sudo systemctl reboot

# Arch Linux
sudo pacman -S clamav
sudo systemctl enable --now clamav-daemon

# openSUSE Tumbleweed/Leap
sudo zypper install clamav
sudo systemctl enable --now clamd
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
