#!/usr/bin/env python3
"""Check (and optionally prepare) a Linux Defender release safely.

Release is a human decision. This script never pushes a tag and never
dispatches the Release workflow: pushing a ``v*`` tag is the only thing that
starts signed package builds and a draft GitHub release. By default it is
read-only and offline; ``--check-ci`` adds a live status query, and
``--create-tag VERSION`` creates *only a local annotated tag* after every
readiness check passes.

Usage:
    python3 scripts/release-readiness.py
    python3 scripts/release-readiness.py --check-ci
    python3 scripts/release-readiness.py --create-tag 0.6.1

The version-agreement source of truth is scripts/check-repo-consistency.py;
this checker calls it instead of duplicating its rules.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE_NOTES = ROOT / "RELEASE_NOTES.md"
CHANGELOG = ROOT / "CHANGELOG.md"
SIGNING_KEY = ROOT / "signing-key.asc"
SIGNING_DOC = ROOT / "website/src/content/docs/docs/contributing/signing.md"
FINGERPRINT = "28CA212A766A6D51273EBBD277B8EC8622C91282"
RELEASE_WORKFLOW = "release.yml"
SEMVER = re.compile(r"^\d+\.\d+\.\d+([-+][0-9A-Za-z.]+)?$")


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def api(path: str) -> object:
    token = os.environ.get("GH_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True
    ).stdout.strip()
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Authorization": f"Bearer {token}", "User-Agent": "linux-defender-readiness",
                 "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-ci", action="store_true", help="require all runs on HEAD to be successful")
    parser.add_argument("--create-tag", metavar="VERSION", help="create a local annotated tag (never pushes)")
    args = parser.parse_args()

    problems: list[str] = []
    notes: list[str] = []

    dirty = git("status", "--porcelain")
    if dirty:
        problems.append("working tree is not clean:\n" + dirty)
    else:
        notes.append("clean working tree")

    head = git("rev-parse", "HEAD")
    origin = git("rev-parse", "origin/main", check=False)
    if origin and head != origin:
        problems.append(f"HEAD {head[:12]} differs from origin/main {origin[:12]}")
    else:
        notes.append(f"HEAD matches origin/main ({head[:12]})")

    branches = git("branch", "--format=%(refname:short)").splitlines()
    if branches != ["main"]:
        problems.append(f"expected only local branch 'main', found: {branches}")
    else:
        notes.append("only local branch is main")

    tags = git("tag", "--list", "v*").splitlines()
    if tags:
        problems.append(f"local v* tags exist and would collide with a release tag: {tags}")
    else:
        notes.append("no local v* tags (pushing one would start Release)")

    consistency = subprocess.run(
        [sys.executable, "scripts/check-repo-consistency.py"], cwd=ROOT, capture_output=True, text=True
    )
    if consistency.returncode != 0:
        problems.append("version/identity consistency failed:\n" + consistency.stdout + consistency.stderr)
    else:
        notes.append(consistency.stdout.strip())

    version = re.search(r'^version\s*=\s*"([^"]+)"', read_text(ROOT / "Cargo.toml"), re.M)
    if not version:
        problems.append("cannot read workspace version")
    else:
        current = version.group(1)
        notes.append(f"workspace version {current}")
        head_note = read_text(RELEASE_NOTES).splitlines()[0] if RELEASE_NOTES.exists() else ""
        if current not in head_note or "development snapshot" in head_note:
            problems.append(
                f"RELEASE_NOTES.md still describes {current} as a development snapshot; "
                "rewrite its heading/intro for a release candidate"
            )
        else:
            notes.append("RELEASE_NOTES.md presents this version as a release")
        changelog = read_text(CHANGELOG)
        if not re.search(r"^## \[Unreleased\]", changelog, re.M):
            problems.append("CHANGELOG.md has no [Unreleased] section")

    if not SIGNING_KEY.is_file():
        problems.append("signing-key.asc is missing")
    elif FINGERPRINT not in read_text(SIGNING_DOC):
        problems.append("published release-verification page does not state the signing fingerprint")
    else:
        notes.append("signing key and published fingerprint are present")

    if not (ROOT / ".github/workflows" / RELEASE_WORKFLOW).is_file():
        problems.append("release workflow is missing")

    if args.check_ci:
        try:
            data = api(f"/repos/Linux-Defender/Linux-Defender/actions/runs?head_sha={head}&per_page=100")
            runs = data.get("workflow_runs", [])
            failed = [r["name"] for r in runs if (r["conclusion"] or r["status"]) != "success"]
            pending = [r["name"] for r in runs if r["status"] != "completed"]
            if not runs or failed or pending:
                problems.append(f"CI on HEAD not fully green: failed={failed}, pending={pending}")
            else:
                notes.append(f"{len(runs)} CI run(s) on HEAD are green")
        except Exception as exc:
            problems.append(f"could not query CI status: {type(exc).__name__}: {exc}")

    if args.create_tag:
        if not SEMVER.match(args.create_tag):
            problems.append(f"--create-tag expects dotted semver (for example 0.6.1), got {args.create_tag!r}")
        elif version and args.create_tag != version.group(1):
            problems.append(
                f"tag v{args.create_tag} does not match workspace version {version.group(1)}; "
                "update all version declarations first"
            )

    print("Release readiness:")
    for note in notes:
        print(f"  OK   {note}")
    if problems:
        print("Release readiness problems:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    if args.create_tag:
        tag = f"v{args.create_tag}"
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", f"Linux Defender {args.create_tag}"],
            cwd=ROOT, check=True,
        )
        print(f"\nLOCAL TAG CREATED: {tag}")
        print("DO NOT PUSH until you are ready: 'git push origin " + tag + "' starts signed builds")
        print("and creates a draft GitHub release. Review RELEASE_NOTES.md and the draft first.")
    else:
        print("\nREADY: no tag created. Use --create-tag <version> when the notes are release-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
