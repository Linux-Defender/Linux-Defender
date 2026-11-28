#!/usr/bin/env python3
"""Fail when a static check is not wired into a gate, or a gate points nowhere.

Two drift classes this catches that the other checkers cannot see:

  * a new ``scripts/check-*`` is added but never invoked, so the "guard" never
    runs and the drift it was written to prevent comes back; and
  * a gate or workflow keeps invoking a script that was renamed or deleted,
    which either fails CI later or silently stops checking anything.

``scripts/check-all.sh`` remains the single source of truth for static checks;
this checker only verifies that everything is reachable from a gate.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = ROOT / ".github/workflows"
GATES = (
    ROOT / "scripts/check-all.sh",
    ROOT / "scripts/audit-consistency.sh",
    ROOT / "scripts/check-translations.sh",
    ROOT / "scripts/update-all.sh",
    ROOT / "scripts/hooks/pre-commit",
    ROOT / "scripts/hooks/pre-push",
)
CHECKER = re.compile(r"^scripts/(?:check-[A-Za-z0-9_.-]+|tests/test_[A-Za-z0-9_.-]+)\.(?:py|sh|ts)$")
INVOCATION = re.compile(
    r"(?:python3?|bun|node|sh|bash)?\s*(?:\.?/scripts/|scripts/|\$SCRIPT_DIR/)"
    r"([A-Za-z0-9_.\-/]+\.(?:py|sh|ts))"
)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout.splitlines()


def main() -> int:
    tracked = set(tracked_files())
    checkers = sorted(path for path in tracked if CHECKER.match(path))

    gate_paths = [path for path in GATES if path.exists()]
    gate_paths += sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
    if not gate_paths:
        print("No gate files found (check-all.sh, audit-consistency.sh, workflows)", file=sys.stderr)
        return 1

    referenced: dict[str, set[str]] = {}
    for gate in gate_paths:
        for line in gate.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", '"', "- \"")):
                continue
            command = stripped.lstrip("!")
            command = re.sub(
                r"^(?:if\s+[^;]+;\s+then\s+|then\s+|else\s+|fi\s*;?\s*)", "", command
            )
            for match in INVOCATION.finditer(command):
                name = match.group(1) or match.group(2)
                referenced.setdefault(f"scripts/{name}", set()).add(
                    str(gate.relative_to(ROOT))
                )

    failures: list[str] = []
    for missing in sorted(set(referenced) - tracked):
        failures.append(
            f"{', '.join(sorted(referenced[missing]))} invokes {missing}, which is not tracked"
        )
    for checker in checkers:
        if checker not in referenced:
            failures.append(
                f"{checker} is not invoked by check-all.sh, audit-consistency.sh, or a workflow"
            )

    if failures:
        print("Gate wiring failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            "Wire new checkers into scripts/check-all.sh (the single source of truth) "
            "and keep gate references pointing at existing files.",
            file=sys.stderr,
        )
        return 1

    print(f"Gate wiring OK: {len(checkers)} checkers referenced by {len(gate_paths)} gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
