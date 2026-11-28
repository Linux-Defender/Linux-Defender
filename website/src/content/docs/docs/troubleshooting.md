---
title: Troubleshooting
description: Resolve host ClamAV, Wayland, daemon, helper, online-check, and scan issues.
---

## ClamAV is missing or definitions are old

Linux Defender uses the host ClamAV tools and the database directory selected by host configuration. Check the engine and database versions in **Database**, or run:

```bash
clamscan --version
freshclam --version
```

Use the distro's FreshClam service or timer to update signatures. On systemd hosts, check `systemctl status clamav-freshclam.timer` (or the distribution's equivalent one-shot timer) and its service journal. Do not run a second `freshclam` process while the service is updating the same database. A warning that FreshClam could not notify `clamd` means there is no reachable daemon socket; it does not undo a database update that passed its database test.

If a manual or forced update stops for inactivity, check host `freshclam` output and connectivity. **Preferences → Behavior → Database Updates** controls the allowed time without stdout or stderr output (10 minutes by default). Active updates have no total time limit; signaling an existing update service is not subject to this setting. When the `clamav-freshclam` service is running, both normal and forced updates ask that service to update via `SIGUSR1` — a forced update never tries to start a second `freshclam` beside it.

## A custom signature source fails and later sources are skipped

FreshClam processes `DatabaseCustomURL` entries in the order written. Some freshclam versions stop the custom-URL phase after one source fails, for example when a provider returns HTTP 410 Gone, so later custom sources are not attempted. Remove or replace the failing URL under **Preferences → Database → Custom Signature Databases**, then run the update again. The failure of a third-party source does not invalidate the official ClamAV database update, but do not assume later custom sources were refreshed until a successful update run lists them.

## Legacy data directories were merged

On first launch, Linux Defender moves a legacy `clamui` directory to its current name. If both old and new directories contain files, the legacy files are merged into the current tree and the old directory is renamed `<name>.migrated`; nothing is deleted. If you want to choose which copy wins, back up both directories before starting the upgraded app:

```bash
cp -a ~/.config/clamui ~/.config/linux-defender ~/ld-config-backup/
cp -a ~/.local/share/clamui ~/.local/share/linux-defender ~/ld-config-backup/
```

After startup, compare `settings.json` and `profiles.json` with the backups if the result is not what you expected. Profiles differ only in IDs and timestamps, so either copy is equivalent. Log JSON files present in only one `logs/` directory can be copied into the other; the log index detects external files and rebuilds itself. Keep the backups until the app opens and your history and settings look right.

## The data directory is unexpectedly large

A killed or crashed daemon scan can leave a private `.linux-defender-clamdscan-<pid>-<sequence>.list` file in the data directory (`~/.local/share/linux-defender`). Normal scans remove it; after a crash, delete it once no scan is running. It only contains target paths that scan was about to read.

## The desktop does not start on Wayland

The native app uses Tauri with WebKitGTK 4.1 and GTK 3. On some Wayland and NVIDIA combinations, WebKitGTK's DMA-BUF renderer can fail during startup with `Error 71` or leave a blank window. When the NVIDIA proprietary driver is present, the native runtime now sets `WEBKIT_DISABLE_DMABUF_RENDERER=1` before creating the webview. To force the workaround on another driver, or to opt out, set the variable yourself:

```bash
WEBKIT_DISABLE_DMABUF_RENDERER=1 bun run --cwd desktop tauri dev
```

On Debian-family hosts, confirm the native runtime libraries with `dpkg -l libwebkit2gtk-4.1-0 libgtk-3-0`. A build on a newer distribution does not establish the Ubuntu 22.04 compatibility baseline.

An explicit `WEBKIT_DISABLE_DMABUF_RENDERER` value in the environment is never overridden. The workaround may reduce hardware acceleration. If it fixes startup, report the desktop session, GPU driver, and exact error.

If the window still opens blank, the native runtime writes one warning to the debug log after ten seconds if React has not reported that it mounted (`frontend did not mount within 10s`). The frontend sends the existing `app.startup_ready` operation once it mounts, so the warning narrows the failure to the WebView bundle, the React error boundary, catalog loading, or an IPC reply. A caught render error is shown in the window with a **Retry** button instead of leaving it blank. Include that log line and the desktop session in a report. The startup-stage warning is written to the debug log under the app's data directory (native installs: `~/.local/share/linux-defender/debug/linux-defender.log`; Flatpak installs: the sandbox-owned data directory). The boot diagnostic shown in a stalled window reports the exact path from the running app.

## Daemon backend is unavailable

The daemon backend needs host `clamd` and `clamdscan`, a running daemon, and a socket accessible to the current user. Select **Auto** or **Clamscan** if you do not need the daemon. Check the service name and socket from your distribution; Fedora commonly uses `clamd@scan` and `/etc/clamd.d/scan.conf`. See the [backend guide](/Linux-Defender/docs/reference/scan-backends/).

Check the daemon on Debian-family hosts with `sudo systemctl status clamav-daemon`, start it with `sudo systemctl enable --now clamav-daemon`, and confirm the client with `clamdscan --version`.

Daemon scans use a protected transport for long paths. A name containing a newline or carriage return is sent through `clamdscan` stdin instead of the newline-delimited file list, so one unusual name does not abort the rest of the scan. Unix file names cannot contain NUL bytes.

## A scan says no virus database was found

Check the host `DatabaseDirectory` in `clamd.conf` or `freshclam.conf`, file permissions, and the path shown in Linux Defender's Database page. Flatpak builds call host ClamAV; they do not need duplicate database files copied into the sandbox. The recognized-file inventory is not proof that a running daemon has loaded every detected file.

## Local YARA rules do not load

Open **Preferences → YARA Rules** and choose a readable directory containing regular `.yar` or `.yara` files. ClamAV supports a subset of YARA syntax. Linux Defender combines those files with the configured system ClamAV database for standalone scans and refuses a YARA-only scan. See [ClamAV's YARA notes](https://docs.clamav.net/manual/Signatures/YaraRules.html).

## VirusTotal or urlscan does not return a result

Check network connectivity, the VirusTotal key in **Preferences → VirusTotal**, rate limits, provider status, and the analysis status shown in Scan. A file/URL result may take time after upload. The app does not submit files or URLs automatically. Review each confirmation carefully: VirusTotal and urlscan have different retention and sharing options. Never upload private files or URLs without authorization.

## A privileged settings change is blocked

Protected host settings require a trusted helper and graphical Polkit authorization. Linux Defender 0.6.0 is a development snapshot; it has no Linux Defender-signed helper package. Legacy helper protocol and package identifiers remain for upgrade compatibility. Use only an already-installed helper whose owner, permissions, protocol, version, and architecture have been independently verified. Linux Defender has no signed helper package yet; do not install a helper from a different product release or bypass trust checks.

If authorization is cancelled or a helper check fails, the protected write remains blocked. Review the exact failure and retry only after a verified helper is available. If an apply fails after some host files were written, use **See Configuration** to inspect each target before manually changing it; the view is read-only.

When running a source build, the helper binary is built next to the desktop executable. In that case Linux Defender detects it and offers **Install Helper** in the blocked-settings dialog even on distributions without a packaged helper (for example Arch/CachyOS). That action uses pkexec to install the same trusted binary that was built with the application; it does not download or substitute an engine or a helper from another release. On a packaged install, install only the version- and architecture-matched helper package.

## File-manager action or tray icon is absent

Linux Defender's integration actions depend on the desktop and file-manager version. The in-app **Preferences → Behavior → Configure Integration** manager exists only in the Flatpak build; native packages install the actions through their package scripts. Recheck the manager if you use Flatpak, then restart the affected file manager or desktop session. The tray requires an SNI watcher; GNOME users may need [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/). Nautilus helper logs under `~/.cache/linux-defender/` record counts and exit status only, never the selected paths. Report the desktop environment and exact file-manager version if an action is missing.

## Scans are slow or report a false positive

- Use **Auto** or a running daemon for repeated scans; standalone `clamscan` reloads definitions each run.
- Check that the account can read the targets and do not unplug removable media during a scan.
- Keep archive and file-size limits finite; untrusted archives can consume CPU, memory, and disk.
- Quarantine first, then research the exact ClamAV signature and file provenance. Heuristic detections can be false positives.
- Compare online reputation only when sharing the file or URL is acceptable; an online reputation result is not a local antivirus verdict.

## Quarantine, schedules, and logs

A restore refusal can mean the destination exists or the saved file's integrity check failed; do not bypass that check. Export important logs before **Clear All** because clearing is permanent. Scheduled scans need an enabled user systemd timer or cron job and a powered-on machine at run time. Check a schedule without changing data:

```bash
linux-defender-scheduled-scan --dry-run
systemctl --user list-timers
crontab -l
```

The canonical CLI command is `linux-defender-scheduled-scan`; the pre-rename `clamui-scheduled-scan` name remains accepted for existing schedules.

## Still stuck?

Collect the Linux Defender commit, ClamAV version, distribution, desktop environment, scan backend, and exact error. Open a [GitHub issue](https://github.com/Linux-Defender/Linux-Defender/issues). Report security vulnerabilities through the [private security policy](/Linux-Defender/docs/contributing/security/), not a public issue.
