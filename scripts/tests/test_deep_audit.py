"""Guard the canonical deep-audit entry point and its wiring."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class DeepAuditTests(unittest.TestCase):
    def test_entry_point_modes(self) -> None:
        text = read("scripts/deep-audit.sh")
        for marker in ("--quick", "--fleet", "update-all.sh --check", "check-all.sh", "audit-consistency.sh", "Agent fleet brief"):
            self.assertIn(marker, text)

    def test_update_all_has_check_mode(self) -> None:
        self.assertIn('"--check"', read("scripts/update-all.sh"))

    def test_wired_into_mcp_plugin_and_docs(self) -> None:
        self.assertIn("ld_deep_audit", read("mcp/linux-defender-assist/src/index.ts"))
        self.assertIn("ld_deep_audit", read("mcp/README.md"))
        command = ROOT / ".claude/plugins/linux-defender-enforcement/commands/deep-audit.md"
        self.assertTrue(command.exists())
        self.assertIn("deep-audit.sh", command.read_text())
        for rel in ("AGENTS.md", "CLAUDE.md", "README.md", "docs/documentation/SCRIPTS.md",
                    "website/src/content/docs/docs/contributing/development.md"):
            self.assertIn("deep-audit", read(rel))

    def test_activation_phrase_and_all_adapters(self) -> None:
        context = read("docs/ai-tooling/CONTEXT.md")
        self.assertIn("yk the drill", context)
        self.assertIn("ld_deep_audit", context)
        config = json.loads(read("opencode.json")) if "json" in globals() else None
        if config is None:
            import json as _json
            config = _json.loads(read("opencode.json"))
        self.assertIn("deep-audit", config["commands"])
        self.assertIn("yk the drill", config["commands"]["deep-audit"]["template"])
        self.assertIn("yk the drill", read(".claude/commands/deep-audit.md").replace("${CLAUDE_PROJECT_DIR}", ""))
        for rel in ("AGENTS.md", "CLAUDE.md", "docs/ai-tooling/README.md"):
            self.assertIn("yk the drill", read(rel))

    def test_wired_into_gate_and_index(self) -> None:
        self.assertIn("test_deep_audit.py", read("scripts/check-all.sh"))
        self.assertIn("scripts/deep-audit.sh", read("docs/documentation/SCRIPTS.md"))


if __name__ == "__main__":
    unittest.main()
