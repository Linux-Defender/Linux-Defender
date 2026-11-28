#!/usr/bin/env python3
"""Guard the pre-React boot-diagnostics and blank-window contract.

The upstream blank-window report (#361) produced a CSP-safe classic script, a
hidden placeholder in index.html, and a read-only local inspector probe. This
checker fails when any part of that chain is removed, weakened, rebranded, or
silently left undocumented. It also guards the host-aware debug log path that
lets the stall message name the right file inside a Flatpak sandbox.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(root: Path = ROOT) -> list[str]:
    failures: list[str] = []

    html = root / "desktop/index.html"
    script = root / "desktop/public/boot-diagnostics.js"
    test = root / "desktop/tests/bootDiagnostics.test.ts"
    probe = root / "scripts/inspect-blank-window.py"
    scripts_index = root / "docs/documentation/SCRIPTS.md"
    troubleshooting = root / "website/src/content/docs/docs/troubleshooting.md"

    if not html.exists():
        failures.append("desktop/index.html is missing")
    else:
        text = html.read_text(encoding="utf-8")
        for marker in (
            'data-boot-placeholder',
            'data-boot-status',
            'data-boot-detail',
            'src="/boot-diagnostics.js"',
        ):
            if marker not in text:
                failures.append(f"desktop/index.html lost {marker}")
        if "Linux Defender is starting" in text:
            failures.append("desktop/index.html still uses the old static boot fallback")

    if not script.exists():
        failures.append("desktop/public/boot-diagnostics.js is missing")
    else:
        text = script.read_text(encoding="utf-8")
        for marker in (
            "sawPlaceholder",          # a pre-body error is not a successful mount
            "pendingFailure",          # early errors are queued, not dropped
            "flush()",                 # and rendered once the placeholder exists
            "debugLogPath()",          # host-aware log path (native + Flatpak)
            "DOMContentLoaded",
            '"error"',
            "unhandledrejection",
            "securitypolicyviolation",
            "STALL_MS = 8000",
            "textContent",
        ):
            if marker not in text:
                failures.append(f"boot-diagnostics.js lost {marker}")
        for forbidden in (
            "innerHTML",
            "fetch(",
            "XMLHttpRequest",
            "sendBeacon",
            "frontend_report",
            "clamui",
            "ClamUI",
        ):
            if forbidden in text:
                failures.append(f"boot-diagnostics.js must not contain {forbidden}")

    if not test.exists():
        failures.append("desktop/tests/bootDiagnostics.test.ts is missing")
    else:
        text = test.read_text(encoding="utf-8")
        if "sawPlaceholder" not in text or "pendingFailure" not in text:
            failures.append("boot diagnostics test no longer guards early-error handling")

    # Host-aware debug log path must exist on both sides of the IPC boundary.
    rust_model = root / "desktop/src-tauri/src/model.rs"
    ts_api = root / "desktop/src/api.ts"
    runtime = root / "desktop/src-tauri/src/runtime.rs"
    if not rust_model.exists() or "pub debug_log: String" not in rust_model.read_text(encoding="utf-8"):
        failures.append("Rust StartupState lost debug_log")
    if not ts_api.exists() or "debug_log?: string" not in ts_api.read_text(encoding="utf-8"):
        failures.append("TypeScript StartupState lost debug_log")
    if not runtime.exists() or "logs::debug_log_path" not in runtime.read_text(encoding="utf-8"):
        failures.append("runtime no longer derives the debug log path from core state")

    if not probe.exists():
        failures.append("scripts/inspect-blank-window.py is missing")
    else:
        text = probe.read_text(encoding="utf-8")
        for marker in (
            "io.github.linuxdefender.linuxdefender",
            "WEBKIT_INSPECTOR_HTTP_SERVER",
            "LINUX_DEFENDER_STARTUP_TRACE",
        ):
            if marker not in text:
                failures.append(f"inspect-blank-window.py lost {marker}")
        if "ClamUI" in text or "clamui" in text:
            failures.append("inspect-blank-window.py has stale upstream branding")

    if not scripts_index.exists() or "scripts/inspect-blank-window.py" not in scripts_index.read_text(encoding="utf-8"):
        failures.append("inspect-blank-window.py is not documented in SCRIPTS.md")
    if not troubleshooting.exists() or "debug/linux-defender.log" not in troubleshooting.read_text(encoding="utf-8"):
        failures.append("troubleshooting.md no longer documents the host-aware debug log")

    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Boot diagnostics contract failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("Boot diagnostics OK: placeholder, script, host-aware path, and probe wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
