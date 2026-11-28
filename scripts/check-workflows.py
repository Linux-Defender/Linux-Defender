#!/usr/bin/env python3
"""Fail when a GitHub Actions workflow is malformed or unnamable.

A malformed `on:` block makes GitHub display the file path instead of the
workflow name and silently prevents the workflow from running correctly. Parse
every workflow and require a name plus a recognizable trigger.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FAIL: PyYAML is required to validate workflows; install pyyaml==6.0.4", file=sys.stderr)
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
TRIGGERS = {
    "push", "pull_request", "schedule", "workflow_dispatch", "workflow_call",
    "release", "issue_comment", "pull_request_target", "repository_dispatch",
    "issues", "workflow_run", "check_run", "deployment", "page_build",
}
# auto-assign only runs on `opened` (no synchronize events), so stale runs are
# impossible; dependabot-refresh has a dedicated per-PR group with
# cancel-in-progress: false so its guarded generation is never interrupted.
CONCURRENCY_EXEMPT = {"auto-assign.yml", "dependabot-refresh.yml"}
EXTERNAL_USE = re.compile(r"uses:\s*[A-Za-z0-9._-]+/[A-Za-z0-9._/-]+@([^\s#]+)")
PINNED = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    failures: list[str] = []
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    for path in workflows:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            failures.append(f"{path.name}: invalid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            failures.append(f"{path.name}: workflow is not a mapping")
            continue
        if not isinstance(data.get("name"), str) or not data["name"].strip():
            failures.append(f"{path.name}: missing workflow name")
        triggers = data.get(True, data.get("on"))
        if not isinstance(triggers, dict):
            failures.append(f"{path.name}: missing or malformed on: triggers")
            continue
        if not (set(triggers) & TRIGGERS):
            failures.append(f"{path.name}: no recognized trigger")
        if "workflow_dispatch" not in triggers:
            failures.append(f"{path.name}: missing workflow_dispatch (cannot be manually verified)")
        if ("pull_request" in triggers and path.name not in CONCURRENCY_EXEMPT):
            concurrency = data.get("concurrency")
            if not isinstance(concurrency, dict) or "pull_request" not in str(
                concurrency.get("cancel-in-progress", "")
            ):
                failures.append(
                    f"{path.name}: PR trigger without PR-scoped concurrency; "
                    "a newer push must cancel stale runs"
                )
        for job_name, job in (data.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            if "runs-on" in job and "timeout-minutes" not in job:
                failures.append(f"{path.name}: job '{job_name}' has no timeout-minutes")
        for ref in EXTERNAL_USE.findall(path.read_text(encoding="utf-8")):
            if not PINNED.match(ref):
                failures.append(
                    f"{path.name}: external action pinned to mutable ref '{ref}'; "
                    "use a 40-hex commit SHA (CodeQL actions/unpinned-tag)"
                )
    if failures:
        print("Workflow failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} workflow failure(s)", file=sys.stderr)
        return 1
    print(f"Workflows OK: {len(workflows)} parsed, named, and triggerable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
