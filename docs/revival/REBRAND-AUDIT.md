# Linux Defender identity and upstream audit

Reviewed 2026-11-12 against the local `rebrand/linux-defender-identity` worktree and current public GitHub APIs.

## Product identity

Linux Defender is the user-facing product name. The app title, app ID, desktop metadata, icons, packaging identities, installer copy, website, repository guidance, and the current changelog/release notes use Linux Defender. The app ID is `io.github.linux_defender.LinuxDefender`; first launch migrates the previous ClamUI native or Flatpak settings/data directories when the destination is empty. If both source and destination contain files, startup stops and leaves both copies unchanged.

The source tree still contains historical project names in several technical contracts: Cargo crate and executable names, CLI invocations, the privileged helper and polkit path, gettext domain, event channel, keyring service, and old directory identifiers. Existing installed helpers, scheduled scans, saved API keys, and user data depend on these. They are not public product branding, but they do still appear in developer and user documentation. Renaming them requires compatibility launchers/protocols and tests, plus a separate migration for helper installation, cron/systemd schedules, keyring access, translations, and logs. This pass does not claim every old identifier has been removed.

The MIT license retains the original upstream copyright notice alongside the Linux Defender contributors' notice. Preserve both notices when distributing substantial portions of MIT-licensed source; the old notice is attribution, not the current product name. See the [MIT license terms](https://opensource.org/license/mit).

## Release signing

The repository-pinned public key identifies `Linux Defender Release Signing`, fingerprint `28CA212A766A6D51273EBBD277B8EC8622C91282`, created 2026-11-12 and expiring 2028-11-11. GitHub Actions secrets named `GPG_PRIVATE_KEY` and `GPG_PASSPHRASE` are configured. Secret values are not readable through the CLI and were not exposed. No signed Linux Defender helper release has yet been published; key presence alone does not validate a signed artifact.

## Latest ClamUI update

The upstream [ClamUI v0.6.0 release](https://github.com/linx-systems/clamui/releases/tag/v0.6.0) was published 2026-11-11. Default branch head checked: `fd2481dcf95c889cf623017433cc2ff17fbe427e` (2026-11-11 22:00 UTC).

- `30a72f0` changes FreshClam's update timeout to an inactivity timeout. The equivalent configurable behavior and tests are already in Linux Defender.
- `fd2481d` removes URLhaus from the recommended feed setup. Linux Defender removes URLhaus from its suggestion and provider UI; users can still add their own custom URLs. The provider's current API documentation says authentication is required: [URLhaus API](https://urlhaus.abuse.ch/api/).
- The two open ClamUI PRs are website dependency changes: [#298](https://github.com/linx-systems/clamui/pull/298) (eight grouped updates), and [#299](https://github.com/linx-systems/clamui/pull/299) (TypeScript 7.0.2). The latter remains deferred because Astro's current check rejected that compiler version in the reviewed snapshot.
- Do not merge the ClamUI branch wholesale: it is a divergent upstream branch and would remove Linux Defender work, including URL reputation and other local integrations. Compare individual commits and port only reviewed behavior.

## Other linked upstreams

The links Kira supplied for ClamTk and its forks/companions, ClamAV, VirusTotal, urlscan, Lenspect, MidnightBSD packaging, and Linux Defender are inventoried in `RELATED-PROJECT-REVIEW.md`, `CLAMTK-ISSUE-PR-TRACKER.md`, and `LENSPECT-REVIEW.md`. The latest API recheck confirmed 23 open ClamTk issues and the four known open PRs (#168, #169, #170, and #141); ClamTk issue [#163](https://github.com/dave-theunsub/clamtk/issues/163) is still open. The ClamTk KDE/GNOME/Nemo/Thunar companion repositories were last pushed in March 2024. Lenspect has open issues #25 and #35 and PR #40; ClamUI has the two PRs above. The `SAFETY-CHAT/clamtk-REBORN` and `SAFETY-CHAT/lenspect-REBORN` repositories return 404. The current ClamAV upstream release checked was [1.5.4](https://github.com/Cisco-Talos/clamav/releases/tag/clamav-1.5.4). This review covers linked repositories/default branches and the known issue/PR snapshots; it is not an exhaustive audit of every historical branch or every fork.

The Linux Defender [Contributing guide](https://github.com/Linux-Defender/Linux-Defender?tab=contributing-ov-file) remains the repository's publishing/contribution entry point. Website deployment and app-release readiness are separate: a signing key and successful website deployment do not constitute published, installable app packages or automatic app updates.
