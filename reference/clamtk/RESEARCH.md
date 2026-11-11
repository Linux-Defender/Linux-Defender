# Historical ClamTk first-pass research (2026-11-10)

This file preserves the unique research log from the original upstream checkout during folder consolidation on 2026-11-11. It is a historical snapshot, not the current status. For updated issue/PR findings and current ClamUI/desktop integration research, use [REVIVAL-TRACKER.md](REVIVAL-TRACKER.md) and [RELATED-PROJECT-REVIEW.md](RELATED-PROJECT-REVIEW.md). In particular, the old signature-age note was superseded by Kira's later FreshClam update log.

---

# ClamTk research and first-pass checks

Updated: 2026-11-10

## Local copy

- Installed executable: `/usr/bin/clamtk`, owned by Arch package `clamtk 6.18-1`.
- User configuration is in `~/.config/clamtk`.
- This checkout is the original upstream repository at `/home/kiras/ClamTk`; its Git history and `origin` remote are intact.
- The working tree is clean. No files from the installed package or its user configuration were changed.
- Installed ClamAV reports `1.5.4`; ClamTk is a graphical frontend and is separate from the ClamAV scanning engine.

## Project status and related work

- Upstream's latest tagged release is 6.18 (January 2024). The maintainer's March 30, 2024 notice says they retired from maintenance and mentions recurring close-time crashes, slow signature loading without feedback, and a desire for a redesign.
- A community repository at `piposeimandi/clamtk` contains a 6.19 line of work dated July 2025. Its visible changes refactor the update UI, point its version check at that fork, and update release metadata. FreeBSD's port history says it switched to this fork in February 2026 as the most active fork it found. The available evidence does not establish that it is actively maintained today.
- Debian and Fedora continue carrying downstream packages, but their package versions/status are distribution maintenance and do not by themselves demonstrate current upstream development.
- ArchWiki describes ClamAV as a malware scanner/toolkit, not a full traditional endpoint protection suite. The GUI does not change what the underlying scanner detects.

## First-pass checks

- Perl syntax check: `clamtk` and every module in the original checkout passed `perl -Ilib -c`.
- Perl syntax check: `clamtk` and every module in the community fork passed `perl -Ilib -c`.
- GUI execution could not be checked in this environment because no graphical display is available (`Gtk-WARNING: cannot open display`). The attempted launch did not modify app settings.
- `Perl::Critic` is not installed, so that optional static-analysis check was unavailable.
- No automated test suite was present in the source checkout. These syntax checks are not behavior, packaging, security, or scan tests.

## Expanded public issue and fork review

GitHub's repository pages showed 23 open issues and 127 closed issues (150 total), plus 4 open and 14 closed pull requests (18 total) when reviewed on 2026-11-10. The 55 entries visible in the upstream fork network are copies/forks, not evidence of 55 active maintainers or a user count.

The open issue titles repeatedly call out the areas to address: app crashes (#167), responsiveness while signatures load (#159), scan logging (#158), dark-mode controls (#149), confusing automatic-update/scheduler behavior (#147 and #127), and missed jobs when a laptop is off (#164). These reports span old releases and distros; they are leads for regression tests, not proof each is still reproducible on ClamTk 6.18.

The 67-comment automatic-update report (#127) documents a key product distinction: ClamTk schedules jobs through the host's cron mechanism, so a disabled cron service means no run; the “computer automatically receives updates” choice means an external package/system updater supplies signatures, not that ClamTk will schedule updates itself. A cron schedule also misses a run while the computer is off. A new scheduler should detect its backend, show whether a job is actually enabled, clarify that distinction in plain language, and offer a missed-run policy.

Fork spot-check: `piposeimandi/clamtk` has a 6.19 code continuation whose last inspected commit is July 3, 2025. A local Git comparison confirms it shares upstream commit `694833d` and is four commits ahead with no upstream-only commits. The changes include a major update-window rewrite, moves Perl modules under `lib/ClamTk/`, and adjusts release metadata. FreeBSD said it switched to that fork in February 2026, useful evidence of downstream use but not proof of current activity. Two other prominent fork names (`clamtk-REBORN` and `clamNEXT`) had unchanged 2024 README text and zero stars at inspection. I have not compared every fork's full git history yet. The current three open upstream PRs are from `vitlav`; their diffs address redraw after signature updates, clearing stale icon selection, and reset of freshclam cooldown state when using a private mirror. They have no reviews listed on the PR pages. The fourth open PR (#141) is an older schedule-status display change. The 14 closed PRs are inventoried by title/state; I have not reviewed all their patches individually.

The issue index for all 150 issues has been inventoried. I read the update-scheduling thread (#127), missed-run request (#164), responsiveness report (#159), and latest crash report (#167) in detail. The other issue bodies/comments still need a targeted pass; old closed issues are useful history but many refer to obsolete distros and ClamTk releases.

## Safe engine test and current update health

- Created the standard harmless EICAR antivirus test string in `/tmp`, scanned it with the installed ClamAV engine, then removed the test file. ClamAV detected `Eicar-Test-Signature` as expected; this tests the engine's EICAR signature, not ClamTk's GUI or broad malware detection.
- The scan also warned that the signature database was older than 7 days. The installed database files were dated October 16, 2026, about 25 days before this review. The local engine therefore needs its official signature update mechanism restored before this machine can rely on current definitions.
- I did not run `freshclam` because it would update the machine-wide database and the current sandbox cannot write that system path. I did not alter update services or settings.
- ClamAV's own documentation says ClamAV is not a traditional endpoint-security suite. A better GUI can improve update visibility, scan usability, and safe quarantine workflows, but cannot promise complete protection.

## Suggested development direction

Keep this original-upstream checkout as the clean reference. The community fork is four commits ahead with no upstream-only commits, so it is a credible base candidate; review its exact update UI and version-check behavior before adopting it. The most concrete maintainer-reported candidates are close-time crashes and poor feedback while ClamAV signatures load. If this becomes a public GitHub project, preserve upstream attribution/license notices and describe it as a community continuation; publishing has not been done.

## Sources

- Original project: https://github.com/dave-theunsub/clamtk
- Maintainer's retirement notice: https://github.com/dave-theunsub/clamtk/issues/163
- Upstream releases: https://github.com/dave-theunsub/clamtk/releases
- Community fork: https://github.com/piposeimandi/clamtk
- FreeBSD port history referencing its fork switch: https://www.freshports.org/security/clamtk
- ArchWiki ClamAV notes: https://wiki.archlinux.org/title/ClamAV
- ClamAV documentation: https://docs.clamav.net/
- Current upstream issue index: https://github.com/dave-theunsub/clamtk/issues
- Current upstream pull request index: https://github.com/dave-theunsub/clamtk/pulls
- Upstream fork network: https://github.com/dave-theunsub/clamtk/network/members
- Automatic-update confusion report: https://github.com/dave-theunsub/clamtk/issues/127
- Missed-schedule report: https://github.com/dave-theunsub/clamtk/issues/164
- Current responsiveness report: https://github.com/dave-theunsub/clamtk/issues/159
- EICAR test guidance: https://docs.clamav.net/faq/faq-misc.html
