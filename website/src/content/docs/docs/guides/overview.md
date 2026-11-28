---
title: Start on the overview
description: Read protection posture, totals, and readiness checks without over-trusting them.
---

**Overview** is the view Linux Defender opens on, and `Ctrl+0` returns to it. It answers three questions: is protection current, what has been scanned so far, and is the scanner ready. Nothing on it changes settings or starts work on its own.

## What the page contains

- **Protection status:** the same status that [Statistics](/Linux-Defender/docs/guides/statistics/) shows, with the last scan time and how long ago it ran.
- **Totals:** all-time scans, files checked, threats detected, and clean scans. These are lifetime counters, not a session summary, and they do not reset when you change the Statistics timeframe.
- **Protection checks:** the scanner engine and database availability reported by the native runtime, the last scan, and how many files are held in quarantine.
- **Quick actions:** shortcuts into Quick Scan, the [System Security Check](/Linux-Defender/docs/guides/security-audit/), Database, Logs, and Quarantine. The security check opens the Audit view; it does not start a scan by itself.

Each card and row is read-only except the actions. **Refresh** re-reads the current state, and the page also refreshes when you switch back to it or when a scan finishes.

## How to read it

A green **Protected** status means a scan ran within the last seven days and the definitions Linux Defender knows about were updated within the last day. It does not mean ClamAV is watching new files: Linux Defender runs scans on demand or on your schedule, so a clean result only describes what was scanned at that time. [Read statistics](/Linux-Defender/docs/guides/statistics/) explains the exact thresholds and how to interpret counts.

An **At risk** or **Unprotected** badge usually means the last scan is old or the definitions are stale, not that something was detected. If **Threats Detected** is above zero, open [Logs](/Linux-Defender/docs/guides/history/) to see which files matched and what the detection names were before you decide anything.

If **Virus definitions** shows **Unavailable**, the host database is missing or unreadable. Fix that in **Database** first; an out-of-date engine is the most common reason a clean scan is not meaningful. [Scan backends and definitions](/Linux-Defender/docs/reference/scan-backends/) covers how the host database is located.

## Limits worth knowing

- Online reputation checks are optional and separate; Overview never contacts a network service.
- The quarantine count is a storage total, not a judgement about risk. Review entries in [Quarantine](/Linux-Defender/docs/guides/quarantine/).
- Status uses the definition timestamp when Linux Defender has one; if it cannot determine definition age, the badge falls back to scan recency alone.

Next: [scan targets and results](/Linux-Defender/docs/guides/scanning/), [quarantine](/Linux-Defender/docs/guides/quarantine/), or [read statistics](/Linux-Defender/docs/guides/statistics/).
