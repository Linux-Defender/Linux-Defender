---
title: Read statistics
description: Use protection status, trends, and quick actions without over-reading them.
---

Open the [overview](/Linux-Defender/docs/guides/overview/) for protection status, all-time totals, quick actions, and the definition/engine checks. Open **Statistics** to see scan activity, detections, totals, duration, and a chart for Day, Week, Month, or All Time. Use **Refresh** after scans, updates, or quarantine actions; the views do not continuously refresh themselves.

## Protection status

Protection status combines scan recency with the age of the virus definitions Linux Defender knows about:

- **Protected:** the last scan is within seven days and the known definitions are at most one day old.
- **At risk:** the last scan is more than seven days ago, or the known definitions are more than one day old. A definition age above seven days keeps the same badge with a more urgent message.
- **Unprotected:** no recorded scan, or the last scan is more than 30 days ago.
- **At risk / Protected:** the last scan found threats or was clean. A load failure is reported as an error, not an Unknown status.

When no definition timestamp is available, status falls back to scan recency alone. Neither case is a real-time endpoint-protection guarantee; ClamAV is not watching every file operation.

## Interpret trends

A rise in files scanned normally reflects larger targets. A rise in detections deserves investigation, but a count does not distinguish severity; open Logs for the affected paths and detection names. Gaps in green scan bars may indicate skipped scheduled scans. Individual scan details live in [Logs](/Linux-Defender/docs/guides/history/).

Quick actions on Overview and Statistics navigate to the relevant view (quick scan, logs, database update, quarantine); they do not make a hidden change.