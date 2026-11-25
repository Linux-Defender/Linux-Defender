# Upstream repositories and related projects

Reviewed 2026-11-25 with HTTP status checks. This is the canonical inventory of
**external** repositories and sites referenced by the revival research. It
covers ClamUI, ClamTk, and Lenspect, so it lives in [`revival/`](README.md)
alongside the parity reviews rather than in the ClamUI-fork-only folder.

Only entries that resolve are listed. Earlier drafts named
`linx-systems/clamui-website`, `linx-systems/lenspect`,
`ClamAV-Petit/ClamTk`, and `linx-systems/clamui-related`; none of those GitHub
repositories exist (HTTP 404). They were corrected from the authoritative
upstream README, the published reviews, and GitHub's repository API.

| Project | URL | Status | Role in the revival |
| --- | --- | --- | --- |
| ClamUI (upstream) | <https://github.com/linx-systems/clamui> | Active | The Rust/Tauri/React product this repository forked. `master` is the source branch; MIT. |
| ClamUI website and docs | <https://clamui.com/docs/> | Active | Upstream documentation site (not a GitHub repository). Linux Defender publishes its own docs on its own site. |
| Our ClamUI contribution fork | <https://github.com/Linux-Defender/clamui> | Active | Used only to send unbranded fixes upstream (for example PR #318); not a second application. |
| Lenspect | <https://github.com/vmkspv/lenspect> | Active (GPL-3.0) | Sister antivirus frontend. Behavior was reviewed independently; no GPL code was copied into this MIT repository. See [LENSPECT-REVIEW.md](LENSPECT-REVIEW.md). |
| ClamTk (upstream) | <https://github.com/dave-theunsub/clamtk> | Active | Perl/Tk frontend; its behavior parity is the source of the revival checklist. See [CLAMTK-RESEARCH.md](CLAMTK-RESEARCH.md) and [CLAMTK-ISSUE-PR-TRACKER.md](CLAMTK-ISSUE-PR-TRACKER.md). |
| ClamTk community fork | <https://github.com/clamtk/clamtk> | Active | Community continuation referenced in ClamTk issue discussions; behavior reference only. |
| ClamTk Flathub packaging | <https://github.com/flathub/com.gitlab.davem.ClamTk> | Archived | Historical Flatpak packaging for the EOL app; useful for packaging comparisons, not a dependency. |
| ClamTk historical GitLab | <https://gitlab.com/dave_m/clamtk> | Active | Original project host referenced in upstream issue quotes. |
| ClamAV Bytecode Compiler | <https://github.com/Cisco-Talos/clamav-bytecode-compiler> | Active (GPL-2.0, release `clambc-1.4.0`) | Upstream tool for building ClamAV bytecode signatures. Reviewed as a signature-format reference only; not vendored, bundled, or integrated into this MIT-licensed product. Linux Defender uses the host ClamAV database and its own independently implemented local YARA support. |

## Repository ownership and licensing

- **MIT**: ClamUI and this repository. Preserve original notices when adopting upstream work.
- **GPL-3.0**: Lenspect. Its behavior may be implemented independently, but its code must not be copied into Linux Defender without an explicit licensing decision.
- **GPL-2.0**: ClamAV Bytecode Compiler. Reference only; no code or build dependency was adopted.
- **Perl/Artistic/GPL mix**: ClamTk and its plugins. Treat as behavior reference only; the Perl reference tree was retired after parity was captured.

## Keeping this inventory current

`scripts/check-upstream-urls.py` verifies every URL in the table above and is
wired into `scripts/check-all.sh`. Network failures are reported but do not
fail offline checks; an HTTP 404 does. When an upstream repository moves,
update this file and the linked review documents in the same change.
