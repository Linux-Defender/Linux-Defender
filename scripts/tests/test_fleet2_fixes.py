"""Fail-closed tests for the second fine-comb fleet wave."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class Fleet2FixTests(unittest.TestCase):
    def test_cli_headless_contract(self) -> None:
        self.assertIn("args_os()", read("crates/linux-defender-core/src/bin/linux-defender-scheduled-scan.rs"))
        cli = read("crates/linux-defender-core/src/cli.rs")
        self.assertIn("None => args", cli)
        self.assertIn("sanitize_line", cli)

    def test_service_fail_closed(self) -> None:
        vt = read("crates/linux-defender-core/src/virustotal.rs")
        self.assertIn('"Malformed response: missing analysis stats" =>', vt)
        self.assertIn('tr(ctx, "Malformed response: missing analysis stats")', vt)
        scheduler = read("crates/linux-defender-core/src/scheduler.rs")
        self.assertIn("detect_backend() != SchedulerBackend::Cron", scheduler)
        self.assertIn("is_scheduled_scan_command(line)", scheduler)

    def test_core_hardening(self) -> None:
        self.assertIn("sanitize_line(", read("crates/linux-defender-core/src/host.rs"))
        self.assertIn('#[serde(rename = "portmaster")]', read("crates/linux-defender-core/src/audit.rs"))
        self.assertIn("parent.sync_all()?", read("crates/linux-defender-core/src/quarantine.rs"))
        self.assertIn("valid_debug_name", read("crates/linux-defender-core/src/logs.rs"))
        self.assertIn("rate_limited_databases", read("crates/linux-defender-core/src/updater.rs"))
        self.assertIn("include_str!(\"../../../signing-key.asc\")", read("crates/linux-defender-core/src/privileged.rs"))

    def test_wave3_and_wave4_hardening(self) -> None:
        audit = read("crates/linux-defender-core/src/audit.rs")
        self.assertIn('tool == "rkhunter" && !rkhunter_findings(&output.stdout).is_empty()', audit)
        self.assertIn("file.take(512)", audit)
        self.assertIn("localize_known(ctx, &message)", read("crates/linux-defender-core/src/virustotal.rs"))
        scan = read("desktop/src/pages/Scan.tsx")
        self.assertIn("void refreshLiveProgress(id)", scan)
        self.assertIn("scan.id ??", read("desktop/src/pages/Results.tsx"))
        self.assertIn("snapshot?.message", read("desktop/src/pages/Network.tsx"))
        self.assertIn("if-no-files-found: error", read(".github/workflows/build-flatpak.yml"))
        self.assertIn("aliases = {", read("scripts/check-format-coverage.py"))

    def test_frontend_and_packaging_hardening(self) -> None:
        audit = read("desktop/src/pages/Audit.tsx")
        self.assertIn("opensnitch-ui", audit)
        self.assertIn("audit.ufw_status", audit)
        results = read("desktop/src/pages/Results.tsx")
        self.assertIn('Array.isArray(record.threat_details)', results)
        self.assertIn("actionLabel", read("desktop/src/pages/SettingsPreferences.tsx"))
        appimage = read("appimage/build-appimage.sh")
        self.assertIn("normalize_appdir_permissions", appimage)
        self.assertIn("check_appimage_permissions", appimage)
        self.assertIn("squashfs-tools", read(".github/workflows/build-appimage.yml"))
        capture = read("scripts/capture-all.sh")
        self.assertIn("CAPTURE_FAILED=1", capture)
        self.assertIn('exit "$CAPTURE_FAILED"', capture)
        plugin = read(".claude/plugins/linux-defender-enforcement/commands/deep-audit.md")
        self.assertTrue(plugin.startswith("---\n"))


if __name__ == "__main__":
    unittest.main()
