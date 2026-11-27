#!/usr/bin/env python3
"""Verify cross-layer feature parity and derive IPC/CLI contracts from code.

Derives Tauri commands from generate_handler!, CLI subcommands from cli.rs, and
the active locale list from po/LINGUAS, then asserts each contract is honored in
every layer that consumes it. Also enforces the declarative feature matrix in
scripts/cross-layer-contracts.json so a feature cannot land in only one scanner.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REDACTED = "<redacted-auth-key>"

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = Path(__file__).with_name("cross-layer-contracts.json")


def read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def corpus(paths: list[str], exts: list[str]) -> str:
    chunks: list[str] = []
    for rel in paths:
        base = ROOT / rel
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file() and (not exts or p.suffix in exts):
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks).lower()


def startup_state_fields() -> tuple[set[str], set[str]]:
    """Field names of the Rust and TypeScript StartupState contracts."""
    rust = read("desktop/src-tauri/src/model.rs")
    ts = read("desktop/src/api.ts")
    rust_block = re.search(r"pub struct StartupState\s*\{(.*?)\n\}", rust, re.S)
    ts_block = re.search(r"(?:export\s+)?type StartupState\s*=\s*\{(.*?)\n\};", ts, re.S)

    def names(body: str) -> set[str]:
        result: set[str] = set()
        for line in body.splitlines():
            match = re.match(r"\s*(?:pub\s+)?([A-Za-z_][A-Za-z0-9_]*)\??\s*:", line)
            if match:
                result.add(match.group(1))
        return result

    return (
        names(rust_block.group(1)) if rust_block else set(),
        names(ts_block.group(1)) if ts_block else set(),
    )


def main() -> int:
    failures: list[str] = []

    # 1. Tauri commands must have a frontend caller.
    runtime = read("desktop/src-tauri/src/runtime.rs")
    m = re.search(r"generate_handler!\s*\[(.*?)\]", runtime, re.S)
    if not m:
        failures.append("cannot derive Tauri commands from generate_handler!")
    else:
        cmds = [c.strip() for c in m.group(1).split(",") if c.strip()]
        frontend = corpus(["desktop/src/"], [".ts", ".tsx"])
        for cmd in cmds:
            if not re.search(rf"\b{re.escape(cmd)}\b", frontend):
                failures.append(f"Tauri command '{cmd}' has no frontend caller")

    # 2. CLI subcommands must be documented on the website.
    cli = read("crates/linux-defender-core/src/cli.rs")
    cli_cmds = set(re.findall(r'"(scan|quarantine|profile|status|history|help|install-privileged-helper)"', cli))
    site = corpus(["website/src/content/"], [".md", ".mdx"])
    for cmd in sorted(cli_cmds):
        if cmd not in site:
            failures.append(f"CLI subcommand '{cmd}' is not documented on the website")

    # 1b. StartupState fields must exist on both sides of the IPC boundary.
    rust_fields, ts_fields = startup_state_fields()
    if not rust_fields or not ts_fields:
        failures.append("cannot derive StartupState fields from Rust/TypeScript")
    else:
        for field in sorted(rust_fields - ts_fields):
            failures.append(f"StartupState field '{field}' is missing from desktop/src/api.ts")
        for field in sorted(ts_fields - rust_fields):
            failures.append(f"StartupState field '{field}' is missing from Rust model.rs")

    # 2b. The in-app documentation link must be allowlisted and use an existing
    # translated label, so it cannot open arbitrary URLs or add an untranslated ID.
    app_source = read("desktop/src/App.tsx")
    if "DOCS_URL" in app_source:
        if "url !== DOCS_URL" not in app_source:
            failures.append("in-app documentation URL is not in the About allowlist")
        if '_("Documentation")' not in app_source:
            failures.append("in-app documentation button does not reuse an existing gettext ID")

    # 3. Active locales must match shipped catalogs.
    linguas = [l.strip() for l in read("po/LINGUAS").splitlines()
               if l.strip() and not l.strip().startswith("#")]
    catalogs = sorted(p.stem for p in (ROOT / "po").glob("*.po"))
    if sorted(linguas) != catalogs:
        failures.append(f"po/LINGUAS {sorted(linguas)} != catalogs {catalogs}")

    # 4. Declarative cross-layer feature matrix.
    cfg = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    layers = cfg["layers"]
    features = cfg["features"]
    if not layers or len(features) < 10:
        failures.append(
            f"cross-layer contracts are too small: {len(layers)} layers, {len(features)} features"
        )
    caches: dict[str, str] = {}
    for feature in features:
        for layer, patterns in feature["layers"].items():
            if layer not in layers:
                failures.append(f"unknown layer '{layer}' in feature '{feature['id']}'")
                continue
            if layer not in caches:
                spec = layers[layer]
                caches[layer] = corpus(spec["paths"], spec["extensions"])
            text = caches[layer]
            for pattern in patterns:
                if pattern.lower() not in text:
                    shown = REDACTED if re.fullmatch(r"[0-9a-f]{40}", pattern) else pattern
                    failures.append(
                        f"feature '{feature['id']}' missing pattern '{shown}' in layer '{layer}'"
                    )

    if failures:
        print("Cross-layer contract failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} cross-layer failure(s)", file=sys.stderr)
        return 1
    print("Cross-layer contracts OK: IPC, CLI, locales, and feature matrix aligned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
