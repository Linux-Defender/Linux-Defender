---
title: Linux Defender documentation
description: Task-focused help for Linux Defender and its host ClamAV installation.
---

Linux Defender is a Linux desktop interface for [ClamAV](https://www.clamav.net/). It does not ship ClamAV or its virus database: install host `clamscan` and `freshclam`. Daemon scans additionally need host `clamd` and `clamdscan`. Version 0.6.0 is a development snapshot; Linux Defender release packages are not published yet.

## Start here

1. [Install Linux Defender](/Linux-Defender/docs/installation/), then update the ClamAV database.
2. Follow [your first scan](/Linux-Defender/docs/getting-started/).
3. For recurring work, create [profiles](/Linux-Defender/docs/guides/profiles/) or [scheduled scans](/Linux-Defender/docs/guides/scheduling/).

## Common tasks

- [Scan a file, folder, or removable drive](/Linux-Defender/docs/guides/scanning/)
- [Review or remove quarantined files](/Linux-Defender/docs/guides/quarantine/)
- [Choose a scan backend](/Linux-Defender/docs/reference/scan-backends/)
- [Fix an installation, daemon, tray, or scan problem](/Linux-Defender/docs/troubleshooting/)
- [Configure settings and ClamAV integration](/Linux-Defender/docs/reference/configuration/)

## Contributors

- [Set up development and packaging](/Linux-Defender/docs/contributing/development/)
- [Translate Linux Defender](/Linux-Defender/docs/contributing/translating/)
- [Verify or sign release packages](/Linux-Defender/docs/contributing/signing/)
- [Understand the tray architecture](/Linux-Defender/docs/contributing/architecture/)

Report bugs and feature requests on [GitHub](https://github.com/Linux-Defender/Linux-Defender/issues). Report vulnerabilities privately through the [security policy](/Linux-Defender/docs/contributing/security/).
