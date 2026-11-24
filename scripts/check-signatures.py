#!/usr/bin/env python3
"""Verify the host ClamAV signature database is present, current, and working.

Checks `clamscan --version` (engine + daily database version/date) and runs an
EICAR detection through the real scanner. Skips cleanly when ClamAV is not
installed; fails when it is installed but the database is missing, stale beyond
SIGNATURE_MAX_AGE_DAYS (default 14), or EICAR is not detected.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

EICAR = r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" + "\n"
VERSION_RE = re.compile(r"ClamAV\s+([0-9.]+)/(\d+)/(.+)")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def main() -> int:
    try:
        version = run(["clamscan", "--version"])
    except FileNotFoundError:
        print("SKIP: host ClamAV (clamscan) is not installed")
        return 0
    except subprocess.TimeoutExpired:
        print("FAIL: clamscan --version timed out", file=sys.stderr)
        return 1
    if version.returncode == 127 or "not found" in version.stderr.lower():
        print("SKIP: host ClamAV (clamscan) is not installed")
        return 0
    if version.returncode != 0:
        print(f"FAIL: clamscan --version failed: {version.stderr.strip()}", file=sys.stderr)
        return 1

    output = version.stdout.strip()
    print(f"ClamAV: {output}")
    match = VERSION_RE.search(output)
    if not match:
        print(f"FAIL: cannot parse ClamAV version/database date: {output!r}", file=sys.stderr)
        return 1
    engine, daily, raw_date = match.groups()
    try:
        db_date = parsedate_to_datetime(raw_date.strip())
        if db_date.tzinfo is None:
            db_date = db_date.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - db_date).days
    except (TypeError, ValueError) as exc:
        print(f"FAIL: cannot parse database date {raw_date!r}: {exc}", file=sys.stderr)
        return 1

    max_age = int(os.environ.get("SIGNATURE_MAX_AGE_DAYS", "14"))
    print(f"Database: daily {daily}, dated {raw_date.strip()} ({age_days} day(s) old)")
    if daily in {"0", ""} or age_days < 0 or age_days > max_age:
        print(f"FAIL: signature database is missing or older than {max_age} days", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="ld-eicar-") as tmp:
        sample = Path(tmp) / "eicar.txt"
        sample.write_text(EICAR, encoding="ascii")
        try:
            scan = run(["clamscan", "--no-summary", "--infected", str(sample)])
        except subprocess.TimeoutExpired:
            print("FAIL: EICAR scan timed out", file=sys.stderr)
            return 1
        text = f"{scan.stdout}\n{scan.stderr}".lower()
        if "eicar" not in text:
            print(f"FAIL: EICAR was not detected (exit {scan.returncode}): {text.strip()}", file=sys.stderr)
            return 1
        print("EICAR: detected by host ClamAV")

    print("SIGNATURES OK: host database is present, current, and detecting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
