# Revival research index

This folder holds the research and decisions behind the Linux Defender revival:
the rebrand and source consolidation, and the behavior parity work for all
related scanners — not just ClamUI. Start here to find the authoritative record
for any upstream project.

## Project records

| Project | Records |
| --- | --- |
| All projects | [UPSTREAM-REPOSITORIES.md](UPSTREAM-REPOSITORIES.md) — canonical, link-checked inventory of external repositories and sites (ClamUI, ClamTk, Lenspect). |
| ClamUI / related projects | [RELATED-PROJECT-REVIEW.md](RELATED-PROJECT-REVIEW.md) — parity matrix and upstream issue/PR disposition. |
| ClamUI releases | [UPSTREAM-CHANGELOG.md](UPSTREAM-CHANGELOG.md) — upstream changelog snapshot. |
| ClamTk | [CLAMTK-RESEARCH.md](CLAMTK-RESEARCH.md) — first-pass research log; [CLAMTK-ISSUE-PR-TRACKER.md](CLAMTK-ISSUE-PR-TRACKER.md) — issue/PR findings and local dispositions. |
| Lenspect | [LENSPECT-REVIEW.md](LENSPECT-REVIEW.md) — GPL behavior review, license boundary, and independently implemented features. |
| Rebrand and consolidation | [REBRAND-AUDIT.md](REBRAND-AUDIT.md), [SOURCE-CONSOLIDATION.md](SOURCE-CONSOLIDATION.md). |
| Local validation | [CACHYOS-TEST-SETUP.md](CACHYOS-TEST-SETUP.md). |
| Conversation record | [CHAT-AND-PROJECT-AUDIT.md](CHAT-AND-PROJECT-AUDIT.md) — consolidated requirement ledger for the whole revival conversation. |

ClamUI-fork-specific porting status lives in
[`../clamui-fork/STATUS.md`](../clamui-fork/STATUS.md). Published user and
contributor documentation lives in
[`../../website/src/content/docs/`](../../website/src/content/docs).

## Adding a new related project

Put the research in this folder, add a row above, add the repository to
[UPSTREAM-REPOSITORIES.md](UPSTREAM-REPOSITORIES.md), and update the parity
matrix in [RELATED-PROJECT-REVIEW.md](RELATED-PROJECT-REVIEW.md). The link
checker verifies the inventory on every commit, and the dead-file checker
requires every new document to be referenced from here.
