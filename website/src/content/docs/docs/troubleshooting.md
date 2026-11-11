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

Use the distro's FreshClam service or timer to update signatures. On Kira's CachyOS setup, check `clamav-freshclam-once.timer` and its service journal. Do not run a second `freshclam` process while the service is updating the same database. A warning that FreshClam could not notify `clamd` means there is no reachable daemon socket; it does not undo a database update that passed its database test.

If a manual or forced update stops for inactivity, check host `freshclam` output and connectivity. **Preferences → Behavior → Database Updates** controls the allowed time without stdout or stderr output (10 minutes by default). Active updates have no total time limit; signaling an existing update service is not subject to this setting.

## The desktop does not start on Wayland

The native app uses Tauri with WebKitGTK 4.1 and GTK 3. On some Wayland and NVIDIA combinations, WebKitGTK's DMA-BUF renderer can fail during startup with `Error 71`. For a source-development launch, try:

```bash
WEBKIT_DISABLE_DMABUF_RENDERER=1 bun run --cwd desktop tauri dev
```

If the workaround fixes startup, report the desktop session, GPU driver, and exact error. It may reduce hardware acceleration. This workaround has only been verified in an upstream Flatpak; Linux Defender has no released Flatpak yet.

## Daemon backend is unavailable

The daemon backend needs host `clamd` and `clamdscan`, a running daemon, and a socket accessible to the current user. Select **Auto** or **Clamscan** if you do not need the daemon. Check the service name and socket from your distribution; Fedora commonly uses `clamd@scan` and `/etc/clamd.d/scan.conf`. See the [backend guide](/Linux-Defender/docs/reference/scan-backends/).

Daemon scans use a protected transport for long paths. ClamAV's file-list protocol cannot represent names containing newline, carriage return, or NUL characters; Linux Defender refuses those daemon targets rather than scanning a different name. Use standalone `clamscan` for that target.

## A scan says no virus database was found

Check the host `DatabaseDirectory` in `clamd.conf` or `freshclam.conf`, file permissions, and the path shown in Linux Defender's Database page. Flatpak builds call host ClamAV; they do not need duplicate database files copied into the sandbox. The recognized-file inventory is not proof that a running daemon has loaded every detected file.

## Local YARA rules do not load

Open **Preferences → YARA Rules** and choose a readable directory containing regular `.yar` or `.yara` files. ClamAV supports a subset of YARA syntax. Linux Defender combines those files with the configured system ClamAV database for standalone scans and refuses a YARA-only scan. See [ClamAV's YARA notes](https://docs.clamav.net/manual/Signatures/YaraRules.html).

## VirusTotal or urlscan does not return a result

Check network connectivity, the VirusTotal key in **Preferences → VirusTotal**, rate limits, provider status, and the analysis status shown in Scan. A file/URL result may take time after upload. The app does not submit files or URLs automatically. Review each confirmation carefully: VirusTotal and urlscan have different retention and sharing options. Never upload private files or URLs without authorization.

## A privileged settings change is blocked

Protected host settings require a trusted helper and graphical Polkit authorization. Linux Defender 0.6.0 is a development snapshot; it has no Linux Defender-signed helper package. Legacy helper protocol and package identifiers remain for upgrade compatibility. Use only an already-installed helper whose owner, permissions, protocol, version, and architecture have been independently verified. Linux Defender has no signed helper package yet; do not install a helper from a different product release or bypass trust checks.

If authorization is cancelled or a helper check fails, the protected write remains blocked. Review the exact failure and retry only after a verified helper is available. If an apply fails after some host files were written, use **See Configuration** to inspect each target before manually changing it; the view is read-only.

## File-manager action or tray icon is absent

Linux Defender's integration actions are managed by the development build and depend on the desktop and file-manager version. Recheck **Preferences → Behavior → Configure Integration**, then restart the affected file manager or desktop session. The tray requires an SNI watcher; GNOME users may need [AppIndicator Support](https://extensions.gnome.org/extension/615/appindicator-support/). Report the desktop environment and exact file-manager version if an action is missing.

## Scans are slow or report a false positive

- Use **Auto** or a running daemon for repeated scans; standalone `clamscan` reloads definitions each run.
- Check that the account can read the targets and do not unplug removable media during a scan.
- Keep archive and file-size limits finite; untrusted archives can consume CPU, memory, and disk.
- Quarantine first, then research the exact ClamAV signature and file provenance. Heuristic detections can be false positives.
- Compare online reputation only when sharing the file or URL is acceptable; an online reputation result is not a local antivirus verdict.

## Quarantine, schedules, and logs

A restore refusal can mean the destination exists or the saved file's integrity check failed; do not bypass that check. Export important logs before **Clear All** because clearing is permanent. Scheduled scans need an enabled user systemd timer or cron job and a powered-on machine at run time. Check a schedule without changing data:

```bash
clamui-scheduled-scan --dry-run
systemctl --user list-timers
crontab -l
```

The CLI command name is still `clamui-scheduled-scan` during the application-identity migration.

## Still stuck?

Collect the Linux Defender commit, ClamAV version, distribution, desktop environment, scan backend, and exact error. Open a [GitHub issue](https://github.com/Linux-Defender/Linux-Defender/issues). Report security vulnerabilities through the [private security policy](/Linux-Defender/docs/contributing/security/), not a public issue.
