---
title: Read statistics
description: Use protection status, trends, and quick actions without over-reading them.
---

Open **Overview** for protection status, all-time totals, quick actions, and the definition/engine checks. Open **Statistics** to see scan activity, detections, totals, duration, and a chart for Day, Week, Month, or All Time. Use **Refresh** after scans, updates, or quarantine actions; the views do not continuously refresh themselves.

## Protection status

Protection status is based on scan recency, not real-time antivirus coverage:

- **Protected:** a recent scan (within seven days).
- **At risk:** the last scan is more than seven days ago but no more than 30 days ago.
- **Unprotected:** no recorded scan, or the last scan is more than 30 days ago.
- **Unknown:** Linux Defender cannot determine status or ClamAV is unavailable.

Keeping definitions current matters, but a definition update alone does not change this scan-recency status. ClamAV is not a complete real-time endpoint-protection guarantee.

## Interpret trends

A rise in files scanned normally reflects larger targets. A rise in detections deserves investigation, but a count does not distinguish severity; open Logs for the affected paths and detection names. Gaps in green scan bars may indicate skipped scheduled scans. Individual scan details live in [Logs](/Linux-Defender/docs/guides/history/).

Quick actions on Overview and Statistics navigate to the relevant view (quick scan, logs, database update, quarantine); they do not make a hidden change.