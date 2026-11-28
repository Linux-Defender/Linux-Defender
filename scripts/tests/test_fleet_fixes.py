"""Fail-closed tests for the fine-comb fleet fixes."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class FleetFixTests(unittest.TestCase):
    def test_mcp_stays_local(self) -> None:
        mcp = read("mcp/linux-defender-assist/src/index.ts")
        self.assertNotIn("endpoint: z.string().url()", mcp)
        self.assertIn("http://127.0.0.1:1234/v1/chat/completions", mcp)
        self.assertIn("/tmp/opencode", mcp)
        self.assertIn("parseInt(fields[1], 8)", mcp)

    def test_gettext_plural_paths(self) -> None:
        merge = read("scripts/merge-catalogs.py")
        review = read("scripts/generate-translation-review.py")
        self.assertIn('msgstr[', merge)
        self.assertIn('msgstr[0] ', review)
        self.assertIn("--no-fuzzy-matching", read("docs/translations/README.md"))

    def test_cli_handles_non_unicode_argv(self) -> None:
        cli = read("crates/linux-defender-core/src/bin/linux-defender-cli.rs")
        self.assertIn("args_os()", cli)
        self.assertIn("std::process::exit(2)", cli)

    def test_scheduler_and_quarantine_invariants(self) -> None:
        scheduler = read("crates/linux-defender-core/src/scheduler.rs")
        self.assertIn("validate_launcher_command", scheduler)
        self.assertIn("saturating_mul(86_400)", read("crates/linux-defender-core/src/quarantine.rs"))
        self.assertIn("is_ascii_digit()", read("crates/linux-defender-core/src/logs.rs"))

    def test_gates_fail_closed(self) -> None:
        self.assertIn("raise SystemExit(1)", read("scripts/check-workflows.py"))
        self.assertIn("CI_RC", read("scripts/audit-consistency.sh"))
        self.assertIn("scripts/hooks/pre-commit", read("scripts/check-gate-wiring.py"))
        self.assertIn("consistency.yml", read(".github/workflows/dependabot-refresh.yml"))
        self.assertIn("len(skipped) == len(locations)", read("scripts/check-external-links.py"))

    def test_capture_and_packaging_wiring(self) -> None:
        self.assertIn("4321/Linux-Defender/", read("scripts/capture-all.sh"))
        self.assertIn('desktop/src-tauri/tauri.conf.json', read("scripts/check-packaging-consistency.py"))
        self.assertIn("rm -rf \"$BUILD_DIR\"", read("appimage/build-appimage.sh"))
        self.assertIn("Invalid locale name", read("debian/build-deb.sh"))

    def test_contracts_and_advisories(self) -> None:
        import json
        contracts = json.loads(read("scripts/cross-layer-contracts.json"))
        ids = {feature["id"] for feature in contracts["features"]}
        self.assertIn("portmaster", ids)
        self.assertIn("tray-close-behavior", ids)
        security = read("website/src/content/docs/docs/contributing/security.md")
        for advisory in ("RUSTSEC-2026-0543", "RUSTSEC-2024-0370", "RUSTSEC-2026-0372"):
            self.assertIn(advisory, security)


if __name__ == "__main__":
    unittest.main()
