# Security Policy

## Report a vulnerability

**Do not report vulnerabilities in public issues.** Use [GitHub's private vulnerability reporting](https://github.com/Linux-Defender/Linux-Defender/security/advisories/new). If the form is unavailable, contact the repository maintainers privately before sharing technical details; do not publish an exploit or sensitive proof of concept.

Include the affected commit or version, impact, reproduction steps or proof of concept, and a suggested mitigation when known. The project is a development snapshot without a published security-response SLA or a published release. Release workflows already sign Debian, RPM, and AppImage artifacts with the repository's checked-in signing key; verify signatures before installing any future release. Flatpak and Snap are built and verified by CI but are not attached as signed release assets, and AUR offers source recipes only. No Linux Defender release packages are currently published.

`SECURITY.txt` provides the machine-readable RFC 9116 contact and policy links.

See the detailed [security guide](website/src/content/docs/docs/contributing/security.md) for scope and safe-use guidance.

## Allowed dependency advisories

`cargo audit` reports five **unmaintained** (not vulnerable) advisories with no
patched version available: `chrono` (RUSTSEC-2026-0543), `proc-macro-error`
(RUSTSEC-2024-0370, via the EOL GTK 0.18 macro stack), `zvariant`, `zbus_names`
and `zvariant_derive` (RUSTSEC-2026-0372; with RUSTSEC-2026-0370 and RUSTSEC-2026-0371 for `zvariant` and `zbus_names`, via the zbus 5 chain still
used by `ksni` and notification plugins). The direct `zbus` dependency is
already on 6.5.0. These are allowed warnings, not vulnerabilities; GitHub
Dependabot has zero open alerts. Revisit when a patched release exists or when
the GTK/zbus 5 stacks can be migrated with locked, tested changes.
