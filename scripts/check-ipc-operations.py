#!/usr/bin/env python3
"""Fail when the frontend invokes an IPC operation the Rust core cannot serve.

The typed frontend talks to the core through one dispatcher: a literal such as
``request("scanner.scan")`` is split into a domain and an action, and the core
routes the domain to a module's ``dispatch`` function. Nothing in the type
system connects those two halves, so a renamed operation compiles cleanly and
fails only at runtime, in front of the user.

This checker joins both sides statically:

  * frontend: every literal ``request("domain.action")`` and direct
    ``invoke("command")`` under ``desktop/src``;
  * core: the ``domain -> module::dispatch`` table in ``lib.rs`` and the action
    literals each module's dispatcher handles (``match`` arms and
    ``action == "..."`` comparisons);
  * runtime: the commands in ``generate_handler!`` must match the direct
    ``invoke`` calls exactly, so a missing or dead command fails here.

Literal operations must resolve to a handled action. A template operation such
as ``quarantine.${action}`` cannot be resolved here, so only its literal domain
is verified. Extra core actions are fine: the CLI, tray, and events use the
same dispatcher.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "crates/linux-defender-core/src"
FRONTEND = ROOT / "desktop/src"
SKIP_PARTS = {"node_modules", "dist", "target"}

# Commands called from native code rather than the webview. Keep this empty:
# a Tauri command is part of the untrusted IPC surface and must have a real
# caller; add a name here only with a reviewed native call site.
NATIVE_ONLY_COMMANDS: set[str] = set()

REQUEST = re.compile(r"""request[^\n(]*\(\s*(["`])([a-z][a-z0-9_]*\.[a-z0-9_${}]*)\1""")
INVOKE = re.compile(r'invoke[^\n(]*\(\s*"([a-z_]+)"')
GENERATED_HANDLERS = re.compile(r"generate_handler!\[([^\]]*)\]")
DOMAIN_ARM = re.compile(r'"([a-z][a-z0-9_]*)"\s*=>')
MODULE_DISPATCH = re.compile(r"(\w+)::dispatch")
LITERAL_ARM = re.compile(r'"([a-z0-9_]+)"\s*=>')
ACTION_COMPARE = re.compile(r'action\s*(?:==|!=)\s*"([a-z0-9_]+)"')
MATCHES_ACTION = re.compile(r"matches!\(\s*action\s*,([^)]*)\)")


def frontend_operations() -> dict[str, set[str]]:
    """Map every literal operation to the files that request it."""
    found: dict[str, set[str]] = {}
    for path in sorted(FRONTEND.rglob("*")):
        if not path.is_file() or path.suffix not in {".ts", ".tsx"}:
            continue
        if SKIP_PARTS & set(path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in REQUEST.finditer(text):
            operation = match.group(2)
            found.setdefault(operation, set()).add(str(path.relative_to(ROOT)))
    return found


def direct_invocations() -> dict[str, set[str]]:
    """Map every direct Tauri ``invoke("command")`` to the files that call it."""
    found: dict[str, set[str]] = {}
    for path in sorted(FRONTEND.rglob("*")):
        if not path.is_file() or path.suffix not in {".ts", ".tsx"}:
            continue
        if SKIP_PARTS & set(path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in INVOKE.finditer(text):
            found.setdefault(match.group(1), set()).add(str(path.relative_to(ROOT)))
    return found


def domain_table() -> dict[str, str]:
    """Read the ``"domain" => module::dispatch`` routing table from lib.rs."""
    text = (CORE / "lib.rs").read_text(encoding="utf-8")
    table: dict[str, str] = {}
    for match in DOMAIN_ARM.finditer(text):
        window = text[match.end() : match.end() + 240]
        dispatch = MODULE_DISPATCH.search(window)
        if dispatch:
            table[match.group(1)] = dispatch.group(1)
    return table


def module_file(module: str) -> Path | None:
    for candidate in (CORE / f"{module}.rs", CORE / module / "mod.rs"):
        if candidate.is_file():
            return candidate
    return None


def handled_actions(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    actions = {match.group(1) for match in LITERAL_ARM.finditer(text)}
    actions |= {match.group(1) for match in ACTION_COMPARE.finditer(text)}
    for match in MATCHES_ACTION.finditer(text):
        actions |= set(re.findall(r'"([a-z0-9_]+)"', match.group(1)))
    return actions


def main() -> int:
    operations = frontend_operations()
    if not operations:
        print("No frontend IPC operations found; the request() pattern moved?", file=sys.stderr)
        return 1

    table = domain_table()
    if not table:
        print("Could not read the domain routing table from crates/linux-defender-core/src/lib.rs",
              file=sys.stderr)
        return 1

    cache: dict[str, set[str]] = {}
    failures: list[str] = []
    checked = 0
    dynamic = 0

    for operation in sorted(operations):
        domain, action = operation.split(".", 1)
        sources = ", ".join(sorted(operations[operation]))
        if domain not in table:
            failures.append(f"{operation}: no core domain route for '{domain}' (used in {sources})")
            continue
        if "$" in action or "{" in action:
            dynamic += 1
            continue
        module = table[domain]
        if module not in cache:
            path = module_file(module)
            if path is None:
                failures.append(
                    f"domain '{domain}' routes to module '{module}', but no "
                    f"crates/linux-defender-core/src/{module}.rs exists"
                )
                cache[module] = set()
                continue
            cache[module] = handled_actions(path)
        if action not in cache[module]:
            handled = ", ".join(sorted(cache[module])) or "none"
            failures.append(
                f"{operation}: core {module}::dispatch does not handle '{action}' "
                f"(used in {sources}; handled: {handled})"
            )
        checked += 1

    runtime = ROOT / "desktop/src-tauri/src/runtime.rs"
    handler = GENERATED_HANDLERS.search(runtime.read_text(encoding="utf-8"))
    if not handler:
        failures.append("desktop/src-tauri/src/runtime.rs has no generate_handler! block")
    else:
        registered = set(re.findall(r"[a-z][a-z0-9_]*", handler.group(1)))
        invoked = direct_invocations()
        for name in sorted(set(invoked) - registered):
            failures.append(
                f"invoke(\"{name}\") has no Tauri command registration "
                f"(used in {', '.join(sorted(invoked[name]))})"
            )
        for name in sorted(registered - set(invoked) - NATIVE_ONLY_COMMANDS):
            failures.append(
                f"Tauri command '{name}' is registered but never invoked by the frontend"
            )
        checked += len(registered)

    if failures:
        print("IPC operation failures:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        print(
            "Add the action to the core dispatcher or fix the frontend call; "
            "never ship an operation the core cannot serve.",
            file=sys.stderr,
        )
        return 1

    print(
        f"IPC operations OK: {checked} literal operation(s) resolve to core handlers "
        f"({dynamic} template operation(s) checked by domain only)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
