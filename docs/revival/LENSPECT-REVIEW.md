# Lenspect integration and parity review

Review date: 2026-11-11. Source: GitHub REST API and public repository, issue, and pull request pages. The API snapshot reports upstream `main` at `1425067051a4d9eed0f3b8b08bd4f1bf14bfa64c`, last pushed 2026-10-18. The repository is GPL-3.0. This is a public snapshot, not a review of private branches or every fork history.

## Verdict

Linux Defender now implements the behavior requested by Lenspect's open product issues, locally in the native Rust/Tauri/React path. Folder VirusTotal scans show a complete file/size preview and require a separate confirmation, skip symlinks, compare a serialized file identity manifest before scanning and again when opening each file, and enforce 100-file/1-GiB limits. Per-file results and cancellation are surfaced. Single-file VirusTotal checks emit hashing, lookup, upload-byte, and analysis-link progress. URL scanning already offers VirusTotal and urlscan.

Status: backend tests and frontend type/build checks pass; actual in-app dialog behavior, real request-body progress through Reqwest, live keyring/network behavior, and CachyOS desktop testing still need validation. Therefore the feature is implemented but not fully platform-verified.

The gettext template and active catalogs now include these UI messages so extraction/validation stays consistent. Existing translations are preserved; newly added untranslated messages use English fallback and need human translation review.

Lenspect's PR #40 is GPL-3.0 code. Its behavior can inform an independent implementation, but copying or adapting its code into this MIT-licensed repository needs a deliberate licensing decision. No Lenspect code was copied in this review.

## Current product behavior checked

| User task | Linux Defender behavior | Status / gap |
|---|---|---|
| Scan files locally | ClamAV scan page accepts local files and folders; saved profile options are applied by the scanner. | Implemented; local test suites were run in the prior audit, but CachyOS desktop behavior remains unverified. |
| Recursively scan a folder locally | The ClamAV scanner receives a folder target and traverses it through the selected ClamAV backend. | Implemented for local ClamAV. This does not send the folder's files to VirusTotal. |
| Check a file with VirusTotal | VirusTotal v3 checks SHA-256 first, uploads only if unknown, uses the large-file upload URL path above 32 MiB, and supports up to 650 MiB. The UI requires an explicit user action/consent. | Implemented with phase/byte progress, cancellable operation, and an early analysis link. Local backend tests pass; real Reqwest progress and desktop behavior remain to verify. |
| Scan a folder with VirusTotal | Folder action previews all regular files and sizes; a separate click confirms remote use. It skips symlinks, revalidates file identities, caps the scan at 100 files and 1 GiB total, processes sequentially, reports per-file results, and can be cancelled. | Implemented locally. Verify Tauri dialog, cancellation, keyring, and real provider behavior on CachyOS; no files have been submitted in tests. |
| Inspect a URL with VirusTotal | Scan → Website URL provides a VirusTotal URL submission and result link. | Implemented. Confirmation warns that the URL, including query data, is submitted and may be shared. |
| Inspect a URL with urlscan | Scan → Website URL offers urlscan visibility choices with Private selected by default. | Implemented. Confirmation and visibility explanation are present; no real submission was made during this review. |
| See file-upload and analysis progress | Backend emits hashing/checking/uploading/analyzing phases; upload reader reports bytes and analysis ID becomes a fixed-origin report link. | Implemented locally; actual desktop validation remains. |
| Hash lookup before upload | The backend queries `/files/{sha256}` before uploading unknown content. | Implemented and covered by mocked protocol tests. |
| Upload files over 32 MiB | The backend obtains the API's large-file upload URL; hard limit is 650 MiB. | Implemented and covered by mocked tests; real account entitlement/rate limits remain external. |
| Linux local backend | Uses host-installed ClamAV and configured databases, not a bundled scanner. | Implemented; distinct from Lenspect's VirusTotal-only scanner. |

### Folder upload behavior and safety

Folder selection must never silently turn into a remote upload. The app shows a local preview (regular-file list, aggregate size, and skipped/unreadable/symlink counts), then requires a separate confirmation. It skips symlinks, checks identity against the preview, caps traversal at 10,000 entries, limits uploads to 100 files and 1 GiB total, and rejects any single file over 650 MiB. It preserves per-file status and allows cancellation. Hidden files are included and displayed in the preview. A local ClamAV folder scan remains a separate action.

Progress should distinguish hashing, hash lookup, upload bytes, and remote analysis. Do not fake percentage progress during remote analysis. Any early link must be constructed only from a validated analysis ID and the fixed `https://www.virustotal.com/gui/analysis/` origin. Keep keys in the OS keyring, keep request URLs and secrets out of logs, and do not automatically submit URLs or files.

## Lenspect issues

The API returned 13 actual issues (excluding PRs that GitHub also exposes through the issues endpoint): 2 open and 11 closed.

| Issue | State | Summary and Linux Defender disposition |
|---|---|---|
| [#39](https://github.com/vmkspv/lenspect/issues/39) | Closed | AppImage startup failure on Linux Mint 22.3/Ubuntu 24.04; packaging/runtime compatibility remains a Linux Defender validation item, not a Lenspect code port. |
| [#35](https://github.com/vmkspv/lenspect/issues/35) | Open upstream | Upload percentage/bytes and scan status, with a clickable VirusTotal analysis while it runs. Linux Defender now emits and displays phases, upload progress, cancellation, and the in-progress analysis link; desktop and real transport validation remain. |
| [#30](https://github.com/vmkspv/lenspect/issues/30) | Closed | GNOME backend version lag; Linux Defender has its own Rust/Tauri desktop runtime and package matrix. |
| [#25](https://github.com/vmkspv/lenspect/issues/25) | Open upstream | Recursive selection of a folder for VirusTotal. Linux Defender now has a separate remote folder action with preview/confirmation and bounded, per-file processing. |
| [#23](https://github.com/vmkspv/lenspect/issues/23) | Closed | Brazilian Portuguese wording and Sway README; keep human translation review and compositor testing in the normal parity process. |
| [#16](https://github.com/vmkspv/lenspect/issues/16) | Closed | Windows port question; Linux Defender is intentionally Linux-only. |
| [#13](https://github.com/vmkspv/lenspect/issues/13) | Closed | Files larger than 32 MiB; Linux Defender implements the VirusTotal large-file endpoint flow, capped at 650 MiB. |
| [#7](https://github.com/vmkspv/lenspect/issues/7) | Closed | API-key eye-icon accessibility label; recheck current key controls when redesigning settings. |
| [#5](https://github.com/vmkspv/lenspect/issues/5) | Closed | Request for local ClamAV backend; Linux Defender's primary scanner is local host ClamAV, with VirusTotal as optional remote analysis. |
| [#4](https://github.com/vmkspv/lenspect/issues/4) | Closed | Window off-screen on Phosh; Linux Defender needs adaptive-window/mobile-Linux desktop testing if Phosh is added to support targets. |
| [#3](https://github.com/vmkspv/lenspect/issues/3) | Closed | Hash lookup before upload; Linux Defender implements SHA-256 lookup before sending file contents. |
| [#2](https://github.com/vmkspv/lenspect/issues/2) | Closed | Start with a file path; Linux Defender supports path startup and desktop actions, with multi-selection behavior tracked separately. |
| [#1](https://github.com/vmkspv/lenspect/issues/1) | Closed | GNOME icon guideline request; Linux Defender's app branding/icon cleanup still requires release asset validation. |

Closed means Lenspect closed the issue; it does not itself prove Linux Defender compatibility.

## Lenspect pull requests

The API returned 25 PRs: one open and 24 closed. The only open behavior PR is #40. The other PRs are translation contributions; merged translation content is not imported automatically because Linux Defender has its own message catalog and translators should review wording.

| PRs | State | Review |
|---|---|---|
| [#40](https://github.com/vmkspv/lenspect/pull/40) | Open upstream | Recursive VirusTotal folder scanning. Linux Defender implemented the behavior independently with stronger preview, identity checks, and resource limits; no GPL code was copied. |
| [#38](https://github.com/vmkspv/lenspect/pull/38), [#37](https://github.com/vmkspv/lenspect/pull/37), [#36](https://github.com/vmkspv/lenspect/pull/36), [#34](https://github.com/vmkspv/lenspect/pull/34), [#33](https://github.com/vmkspv/lenspect/pull/33), [#32](https://github.com/vmkspv/lenspect/pull/32), [#31](https://github.com/vmkspv/lenspect/pull/31), [#27](https://github.com/vmkspv/lenspect/pull/27), [#26](https://github.com/vmkspv/lenspect/pull/26), [#24](https://github.com/vmkspv/lenspect/pull/24), [#21](https://github.com/vmkspv/lenspect/pull/21), [#20](https://github.com/vmkspv/lenspect/pull/20), [#19](https://github.com/vmkspv/lenspect/pull/19), [#18](https://github.com/vmkspv/lenspect/pull/18), [#17](https://github.com/vmkspv/lenspect/pull/17), [#15](https://github.com/vmkspv/lenspect/pull/15), [#14](https://github.com/vmkspv/lenspect/pull/14), [#12](https://github.com/vmkspv/lenspect/pull/12), [#10](https://github.com/vmkspv/lenspect/pull/10), [#8](https://github.com/vmkspv/lenspect/pull/8), [#6](https://github.com/vmkspv/lenspect/pull/6) | Closed, merged | Language/catalog contributions (Azerbaijani, Georgian, Brazilian Portuguese, Japanese, Arabic, Italian, Spanish, Turkish, Vietnamese, Hebrew, Dutch, Bulgarian). Review relevant terminology and license/attribution if reusing translated strings; no scanner behavior to merge. |
| [#28](https://github.com/vmkspv/lenspect/pull/28), [#22](https://github.com/vmkspv/lenspect/pull/22), [#9](https://github.com/vmkspv/lenspect/pull/9) | Closed, not merged | Translation submissions; no scanner behavior. |

## Forks and limits of this review

The public repository endpoint did not find `SAFETY-CHAT/lenspect-REBORN` at review time (HTTP 404); no fork comparison is claimed for that repository. Upstream lists 14 forks. This review checked Lenspect's current public default branch, issue list, and PR list; it did not diff all 14 forks or every historical branch/commit. Recheck the fork list and API before release. The later repository-rename and publication pass pushed branch `revival/unified-app`; PR #1 was merged into `main`. This Lenspect review still does not compare all upstream forks or historical branches.

## Required parity update rule

For every related scanner release or feature change, record repository and commit/date, review all new/open issues and PR diffs, compare behavior against this matrix and `RELATED-PROJECT-REVIEW.md`, classify each item as ported/deferred/not applicable, check license/privacy/security/limits/platform/localization, add regression coverage, and update the matrix. Never treat a default-branch snapshot, a closed issue, or a passing upstream CI badge as proof of Linux Defender parity. Do not auto-merge upstream changes.
