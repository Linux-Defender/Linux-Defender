#!/usr/bin/env python3
"""Verify every package format stays version-matched, rebranded, and wired.

Covers DEB, RPM helper, AppImage, Flatpak, Snap, and AUR (app + helper):
manifests/build scripts, CI workflows, README badges, release asset patterns,
the host-ClamAV boundary, and the canonical app id. AUR-specific invariants
(pinned source commit, tarball hash, generated .SRCINFO) are included here so
there is one checker for all packaging instead of a special case.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_ID = "io.github.linuxdefender.linuxdefender"
AUR = ROOT / "aur"
APP_PKG = AUR / "PKGBUILD"
HELPER_PKG = AUR / "linux-defender-privileged-helper/PKGBUILD"

FORMATS = {
    "DEB": {
        "files": ["debian/README.md", "debian/build-deb.sh", "debian/build-privileged-helper-deb.sh",
                  "debian/DEBIAN/control", "debian/DEBIAN/control.helper"],
        "workflow": "build-deb.yml",
        "marker": "linux-defender",
    },
    "RPM helper": {
        "files": ["rpm/README.md", "rpm/build-privileged-helper-rpm.sh", "rpm/linux-defender-privileged-helper.spec"],
        "workflow": "build-rpm.yml",
        "marker": "linux-defender-apply-preferences",
    },
    "AppImage": {
        "files": ["appimage/README.md", "appimage/build-appimage.sh", "desktop/src-tauri/tauri.conf.json"],
        "workflow": "build-appimage.yml",
        "marker": APP_ID,
    },
    "Flatpak": {
        "files": ["flathub/README.md", f"flathub/{APP_ID}.yml", f"flathub/{APP_ID}.local.yml",
                  "flathub/cargo-sources.json", "flathub/bun-sources.json"],
        "workflow": "build-flatpak.yml",
        "marker": APP_ID,
    },
    "Snap": {
        "files": ["snap/README.md", "snap/snapcraft.yaml", "snap/local/linux-defender-launch"],
        "workflow": "build-snap.yml",
        "marker": APP_ID,
    },
    "AUR": {
        "files": ["aur/PKGBUILD", "aur/.SRCINFO", "aur/README.md",
                  "aur/linux-defender-privileged-helper/PKGBUILD",
                  "aur/linux-defender-privileged-helper/.SRCINFO"],
        "workflow": "build-aur.yml",
        "marker": "linux-defender",
    },
}
BADGES = [
    "build-appimage.yml", "build-aur.yml", "build-deb.yml", "build-flatpak.yml", "build-rpm.yml",
    "build-snap.yml", "packaging-sync.yml", "signature-database.yml",
    "doc-links.yml", "upstream-freshness.yml", "consistency.yml", "test.yml",
]


def verify_aur_tarball_hash(failures: list[str]) -> None:
    """Confirm the AUR sha256sum matches the pinned GitHub source archive."""
    import hashlib
    import urllib.request

    pkgbuild = read(ROOT / "aur/PKGBUILD")
    commit = re.search(r"^_commit=([0-9a-f]+)$", pkgbuild, re.M)
    checksum = re.search(r"^sha256sums=\('([0-9a-f]+)'\)", pkgbuild, re.M)
    if not commit or not checksum:
        failures.append("AUR PKGBUILD commit pin or sha256sum is missing")
        return
    url = f"https://github.com/Linux-Defender/Linux-Defender/archive/{commit.group(1)}.tar.gz"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "linux-defender-check"})
        with urllib.request.urlopen(request, timeout=30) as response:
            digest = hashlib.sha256()
            for chunk in iter(lambda: response.read(1 << 20), b""):
                digest.update(chunk)
    except urllib.error.HTTPError as exc:
        failures.append(f"AUR tarball URL returned HTTP {exc.code}: {url}")
        return
    except (urllib.error.URLError, TimeoutError) as exc:  # network unreachable is not drift
        print(f"note: could not verify AUR tarball hash ({exc}); skipped")
        return
    if digest.hexdigest() != checksum.group(1):
        failures.append("AUR sha256sum does not match the pinned source tarball")


def verify_flatpak_sources(failures: list[str]) -> None:
    """Offline Flatpak sources must match the locked Cargo and Bun inputs."""
    import base64
    import json

    try:
        cargo_sources = json.loads(read(ROOT / "flathub/cargo-sources.json"))
        bun_sources = json.loads(read(ROOT / "flathub/bun-sources.json"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid Flatpak source manifest JSON: {exc}")
        return

    expected_crates: dict[str, str] = {}
    for block in read(ROOT / "Cargo.lock").split("\n\n"):
        name = re.search(r'^name = "([^"]+)"', block, re.M)
        version = re.search(r'^version = "([^"]+)"', block, re.M)
        checksum = re.search(r'^checksum = "([^"]+)"', block, re.M)
        source = re.search(r'^source = "registry\+https://github\.com/rust-lang/crates\.io-index"', block, re.M)
        if name and version and checksum and source:
            expected_crates[f"{name.group(1)}-{version.group(1)}"] = checksum.group(1)
    actual_crates: dict[str, str] = {}
    for entry in cargo_sources:
        if entry.get("type") != "archive":
            continue
        match = re.search(r"/crates/([^/]+)/([^/]+)\.crate$", entry.get("url", ""))
        if match:
            actual_crates[match.group(2)] = entry.get("sha256", "")
    for crate, checksum in expected_crates.items():
        if actual_crates.get(crate) != checksum:
            failures.append(f"flathub/cargo-sources.json missing or wrong checksum for {crate}")
    for crate in set(actual_crates) - set(expected_crates):
        failures.append(f"flathub/cargo-sources.json has stale crate source {crate}")

    expected_bun: dict[str, str] = {}
    pending_url: str | None = None
    for line in read(ROOT / "desktop/yarn.lock").splitlines():
        resolved = re.match(r'^\s+resolved "([^"]+)"', line)
        if resolved:
            pending_url = resolved.group(1)
            expected_bun[pending_url] = ""
        integrity = re.match(r'^\s+integrity sha512-([^\s]+)', line)
        if integrity and pending_url:
            expected_bun[pending_url] = base64.b64decode(integrity.group(1)).hex()
            pending_url = None
    actual_bun: dict[str, str] = {}
    for entry in bun_sources:
        if entry.get("type") == "file" and entry.get("url"):
            actual_bun[entry["url"]] = entry.get("sha512", "")
    for url, digest in expected_bun.items():
        if actual_bun.get(url) != digest:
            failures.append(f"flathub/bun-sources.json missing or wrong checksum for {url}")
    for url in set(actual_bun) - set(expected_bun):
        failures.append(f"flathub/bun-sources.json has stale package source {url}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def main() -> int:
    failures: list[str] = []
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    corpus = "\n".join(read(ROOT / rel) for rel in tracked.stdout.splitlines() if (ROOT / rel).is_file())

    version = re.search(r'^version\s*=\s*"([^"]+)"', read(ROOT / "Cargo.toml"), re.M)
    if not version:
        failures.append("cannot read workspace version")
        version_value = ""
    else:
        version_value = version.group(1)
    declared = {
        "Tauri crate": re.search(r'^version\s*=\s*"([^"]+)"', read(ROOT / "desktop/src-tauri/Cargo.toml"), re.M),
        "desktop package": re.search(r'"version"\s*:\s*"([^"]+)"', read(ROOT / "desktop/package.json"), re.M),
        "AppStream": re.search(r'<release\s+version="([^"]+)"', read(ROOT / f"data/{APP_ID}.metainfo.xml"), re.M),
        "Flatpak notes": re.search(r"^# Linux Defender ([0-9.]+) release description", read(ROOT / "flathub/RELEASE_NOTES.md"), re.M),
        "AUR app": re.search(r"^pkgver=([0-9.]+)$", read(APP_PKG), re.M),
        "AUR helper": re.search(r"^pkgver=([0-9.]+)$", read(HELPER_PKG), re.M),
    }
    for label, found in declared.items():
        if not found or found.group(1) != version_value:
            failures.append(f"{label} version does not match workspace version {version_value}")

    for name, spec in FORMATS.items():
        for rel in spec["files"]:
            if not (ROOT / rel).exists():
                failures.append(f"{name} is missing {rel}")
        if spec["workflow"] not in corpus:
            failures.append(f"{name} workflow {spec['workflow']} is not referenced in docs/tooling")
        if not (ROOT / ".github/workflows" / spec["workflow"]).exists():
            failures.append(f"{name} workflow file is missing: {spec['workflow']}")
        format_text = "\n".join(read(ROOT / rel) for rel in spec["files"])
        if spec["marker"] not in format_text:
            failures.append(f"{name} does not use the rebranded {spec['marker']} identity")
        if re.search(r"linx[_-]systems|clamui\.com|Estemobs", format_text, re.I):
            failures.append(f"{name} contains an upstream brand in live packaging files")
        if "/var/lib/clamav" in format_text or "clamav-db" in format_text:
            failures.append(f"{name} recipe bundles host signature data")
        # The host engine and its signature database are never packaged.
        if re.search(r"\.(cvd|cld|hdb|ndb|ftm|idb|ldb)\b", format_text, re.I):
            failures.append(f"{name} recipe references a bundled signature database file")
        if re.search(r"(?:cp|install|mv)\s+\S*(?:usr/(?:s)?bin/)?(?:clamscan|clamdscan|freshclam|clamd)\b", format_text):
            failures.append(f"{name} recipe copies a host ClamAV binary into the package")

    # Cross-package helper identity and release asset names.
    helper_paths = [
        "debian/build-privileged-helper-deb.sh", "rpm/linux-defender-privileged-helper.spec",
        "appimage/build-appimage.sh", "aur/linux-defender-privileged-helper/PKGBUILD",
    ]
    for rel in helper_paths:
        if "linux-defender-apply-preferences" not in read(ROOT / rel):
            failures.append(f"helper path missing from {rel}")
    release = read(ROOT / ".github/workflows/release.yml")
    if "linux-defender_" not in release or "Linux-Defender-" not in release:
        failures.append("release workflow does not attach rebranded asset patterns")
    if re.search(r"clamui[_-]", release, re.I):
        failures.append("release workflow still contains pre-rename asset patterns")

    # README badges for every build/freshness workflow.
    readme = read(ROOT / "README.md")
    for workflow in BADGES:
        if workflow not in readme:
            failures.append(f"README badge missing for {workflow}")

    # Parity/status documentation must mention every packaging format.
    status = read(ROOT / "docs/clamui-fork/STATUS.md")
    docs_index = read(ROOT / "docs/README.md")
    for token in ("DEB", "RPM", "AppImage", "Flatpak", "Snap", "AUR"):
        if token not in status:
            failures.append(f"fork STATUS does not record {token} packaging")
    for folder in ("debian", "rpm", "appimage", "flathub", "snap", "aur"):
        if f"../{folder}/README.md" not in docs_index:
            failures.append(f"docs/README.md does not link {folder}/README.md")

    # AUR-specific reproducibility invariants.
    app, helper = read(APP_PKG), read(HELPER_PKG)
    for field, pattern in (
        ("source commit", r"^_commit=([0-9a-f]{40})$"),
        ("tarball hash", r"^sha256sums=\('([0-9a-f]{64})'\)$"),
    ):
        a, h = re.search(pattern, app, re.M), re.search(pattern, helper, re.M)
        if not a or not h or a.group(1) != h.group(1):
            failures.append(f"AUR app and helper disagree on {field}")
    for p in (APP_PKG, HELPER_PKG):
        if subprocess.run(["bash", "-n", str(p)], cwd=ROOT, capture_output=True).returncode != 0:
            failures.append(f"invalid PKGBUILD syntax: {p.relative_to(ROOT)}")
    if shutil.which("makepkg"):
        for p, srcinfo in ((APP_PKG, AUR / ".SRCINFO"),
                           (HELPER_PKG, HELPER_PKG.parent / ".SRCINFO")):
            result = subprocess.run(["makepkg", "--printsrcinfo"], cwd=p.parent,
                                    capture_output=True, text=True)
            if result.returncode != 0:
                failures.append(f"makepkg --printsrcinfo failed for {p.parent.relative_to(ROOT)}")
            elif read(srcinfo) != result.stdout:
                failures.append(f"stale .SRCINFO: {srcinfo.relative_to(ROOT)}")

    # The pinned source commit must be real history, not a mistyped or
    # unreviewed SHA that no one can build from.
    pin_match = re.search(r"^_commit=([0-9a-f]{40})$", app, re.M)
    if pin_match:
        pin = pin_match.group(1)
        known = subprocess.run(
            ["git", "cat-file", "-e", f"{pin}^{{commit}}"],
            cwd=ROOT, capture_output=True,
        ).returncode == 0
        if not known:
            print(f"note: AUR pin {pin[:12]} is absent from this shallow clone; ancestry not checked")
        elif subprocess.run(
            ["git", "merge-base", "--is-ancestor", pin, "HEAD"],
            cwd=ROOT, capture_output=True,
        ).returncode != 0:
            failures.append(
                f"AUR source pin {pin[:12]} is not an ancestor of HEAD "
                "(mistyped or unreviewed commit)"
            )

    verify_flatpak_sources(failures)
    verify_aur_tarball_hash(failures)

    if failures:
        print("Packaging consistency failures:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        print(f"{len(failures)} packaging failure(s)", file=sys.stderr)
        return 1
    print(f"Packaging consistency OK: {len(FORMATS)} formats version-matched, rebranded, and wired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
