# Related project and UI merger review

Review snapshot: 2026-11-11. Sources: public GitHub REST API, default-branch checkouts, READMEs/changelogs/security workflows, and public issue/PR discussions. This is point-in-time research, not a review of private branches or every historical commit.

The ClamUI default branch advanced after the earlier v0.5.1 snapshot documented below. This pass checked the official v0.6.0 release and website, then reviewed the newer default-branch commit `30a72f036870e80c487bf95b13aa80bfc906bd4a` (2026-11-11), which fixes update inactivity handling for #307. That runtime fix is ported locally with a configurable inactivity timeout and regression tests. Vietnamese (`vi`) from v0.6.0 is active in the desktop and CLI catalogs. At that earlier review the two open upstream PRs were website dependency changes; #298 is adopted and validated, while #299’s TypeScript 7.0.2 bump is deferred because Astro 7.4.5 `astro check` explicitly rejects TypeScript 7 and requires TypeScript 6. At the 2026-11-25 recheck #298 is closed and ClamUI has six open dependency-bump PRs (see “Current upstream recheck” below). Linux Defender's 0.6.0 version is a development snapshot with local additions; it is not the upstream ClamUI release and has no signed Linux Defender packages. An installed upstream ClamUI remains identified as `io.github.linx_systems.ClamUI` and is not replaced; Linux Defender migrates its legacy settings/data into the Linux Defender XDG directories on first launch and keeps the pre-rename identifiers as compatibility contracts.

Lenspect's issues, all 25 PRs, remaining VirusTotal parity gaps, license boundary, and parity-maintenance rule are recorded in [LENSPECT-REVIEW.md](LENSPECT-REVIEW.md). The dated, request-by-request coverage ledger for the revival chat is [CHAT-AND-PROJECT-AUDIT.md](CHAT-AND-PROJECT-AUDIT.md).

## Direction

Kira wants one installable Linux security-scanning product that keeps ClamTk behavior, gains ClamUI behavior and a modern UI, and can be maintained by reviewing both projects continuously. A literal code merge is not a small patch: ClamTk is Perl/GTK3; ClamUI is a Rust core + Tauri + React/TypeScript desktop app. ClamUI is MIT-licensed; ClamTk retains its GPL/Artistic licensing. MIT code can be incorporated with notices, but the combined product needs license/attribution review before distribution.

The selected local target is one installable product with one primary modern UI and one runtime. ClamUI's Rust/Tauri/React application is the base in this repository; ClamTk behavior parity is recorded in this directory, and its Perl reference tree was retired on 2026-11-16. The final product should not run both language stacks or show two apps. Use host ClamAV and the system FreshClam database. Do not bundle a second engine or signature database. Review, test, then port upstream updates; do not auto-merge.

ClamUI already includes scan profiles, standalone and daemon scanning, scheduling, scan history/logs, quarantine, database/update controls, VirusTotal, file-manager integrations, tray support, and a wider host-security audit. ClamTk brings its GTK workflow, per-user signatures, quarantine/restore behavior, local YARA rules, consent-based VirusTotal/urlscan controls, and distro plugins. The parity inventory is a migration checklist: preserve useful features from both in the one product, then validate each before removing the reference subtree.

### Feature parity target

| Area | Keep from ClamTk | Adopt from ClamUI | Combined target |
|---|---|---|---|
| Engine and updates | ClamAV scan options, FreshClam preference explanation, shared/per-user mode | Host engine discovery, clamd status, database health view | One system ClamAV database by default; show engine/signature age and service state; optional clamd backend only when its behavior matches the selected scan options. |
| Scan workflow | Existing GTK scanning, pause/cancel, preferences | Profiles, multiple selected targets, structured results | One modern profile-based workflow; temporarily retain a compatibility path during migration, then one app entry point; multi-file CLI/context-menu support; exact per-item status and warning counts. |
| History and quarantine | Restore records and the collision-safe unique quarantine names | Searchable history/logs and review flow | One recoverable quarantine store, no automatic deletion, preserve legacy restore-data migration. |
| Scheduling | Existing cron scheduler and status | User-level systemd scheduling and profiles | UI-managed schedules with documented off-machine behavior and per-distro adapters; never silently install/enable services. |
| Extra detections | Local YARA rules; explicit VirusTotal and urlscan actions | Security audit/component view | Local YARA folder selection and standalone scan loading are ported. Website URL mode offers VirusTotal URL analysis or urlscan with Private default visibility; both explain data sharing. VirusTotal file progress and bounded, confirmed folder upload are implemented locally; verify on CachyOS. Keep remote reputation opt-in and distinct from local malware verdicts. |
| Desktop integration | GTK desktop entry and distro add-ons | Tray and file-manager launchers | One app with Dolphin, Nautilus, Nemo, and Thunar Send To actions; preserve `%F` multi-selection and verify each desktop version. Thunar actions are now included in the Flatpak integration manager; desktop validation remains open. |
| Packaging and languages | Preserve ClamTk translations and existing metadata | Flatpak/AppImage/DEB/RPM build matrix and ClamUI localization workflow | Restore ClamTk translation sources, preserve attribution, migrate the needed message catalogs, build CachyOS/Arch first, then CI across distro families. |

### Language and data migration boundary

ClamTk and ClamUI should not become a mixed Perl/Rust runtime. Keep the existing Perl implementation as the behavior reference while the single Rust/Tauri product gains feature parity. Add a one-time, read-only-first migration for ClamTk preferences, scan history, scheduled-scan settings, quarantine payloads and restore records. Preserve the original data as a backup until the new app verifies each imported item. Never migrate the inherited source-embedded VirusTotal key; require a new personal key stored in the OS keyring. Keep the ClamAV engine and official signatures owned by the host package/service.

### ClamTk screen-by-screen parity check

Checked ClamTk's `lib/GUI.pm`, `Shortcuts.pm`, `Prefs.pm`, and feature modules (before the Perl reference tree was retired) against the current React navigation and Rust operation surface. “Present” means a corresponding Linux Defender workflow exists; it does not claim pixel or behavior parity.

| ClamTk screen / behavior | Linux Defender counterpart | Result and follow-up |
|---|---|---|
| Configuration: Settings | Preferences pages for behavior, exclusions, scanner, schedule, YARA, VirusTotal, device/on-access scanning | Broad counterpart exists. Legacy preferences import and exact default/edge behavior are not complete. |
| Configuration: Whitelist | Preferences → Exclusions | Counterpart exists; compare each ClamTk pattern/path rule and prove migration preserves it. |
| Configuration: Network / HTTP proxy | Preferences → Network | UI exists. VirusTotal and urlscan transports deliberately avoid inherited proxy settings in current implementation; verify whether proxy support is required and implement without weakening TLS checks. |
| Configuration: Scheduler | Schedules page and user systemd scheduling | Counterpart exists; not the same cron format or lifecycle. Migrate schedule definitions and validate missed-run/offline behavior on CachyOS. |
| Updates: Update signatures | Database page and FreshClam status/update controls | Uses host FreshClam/shared database. Per-user `single` database mode is not a parity target because it creates a duplicate definition store; communicate this clearly and migrate only when a concrete supported need exists. |
| Updates: Update Assistant | Database/audit views and system timer status | Partial. ClamTk-specific update-mode assistant and all service variants are not ported; FreshClam's system service/timer remains owned by the distro. |
| History | Results and historical scan logs | Counterpart exists; compare old history import, ordering, and failure/detail retention. |
| Quarantine and restore | Quarantine page with review and restore operations | Counterpart exists; legacy payload/restore-record migration is open; verify unique-name collision and rollback safety. |
| Scan file / directory | Scan → Files & Folders; profiles; CLI paths | Counterpart exists for local ClamAV, including recursive targets. Preserve original path identity, multi-selection, exclusions, cancellation, and per-target status. |
| Analysis: file reputation | Scan with VirusTotal; Results page | File hash lookup, upload progress, in-progress analysis link, and bounded folder upload are implemented locally; desktop transport validation remains. Prior submission history/CSV compatibility is not ported. |
| Analysis: Website scan | Scan → Website URL with VirusTotal and urlscan | Provider workflows exist with explicit confirmation; urlscan visibility is selectable and defaults Private. Verify live UI/keyring behavior on CachyOS without submitting private URLs. |
| Startup update/signature warning | Database/Audit health indicators | Partial. Audit detects known FreshClam service/timer patterns, but startup warning timing and every distro service name need a compatibility matrix and live verification. |
| Keyboard shortcuts and launcher path arguments | Tauri shortcuts, command-line paths, desktop actions | Partial. Keep ClamTk shortcuts and CLI invocation behavior in the migration checklist; test desktop multi-select and startup routing on KDE/GNOME/XFCE. |

## ClamUI repository snapshot

The following 60-issue list is the earlier 2026-11-07 snapshot and is superseded by the live 2026-11-11 refresh below.

- Checked-out default-branch head: `32270d53ee2e412d5d46718cfa99eaf9bd346f62` (2026-11-07). Repository reported version 0.5.1; README then said Flathub still distributed historical 0.4.1.
- Stack: Rust headless core + Tauri + React/TypeScript. Packages use host ClamAV; daemon mode requires host `clamd` and `clamdscan`.
- GitHub API snapshot: 60 open issues, 12 closed issues, 2 open PRs (all indexed below).
- Latest commit CI API snapshot: core tests, dependency audit, CodeQL, desktop build, Flatpak, RPM, DEB, and AppImage checks reported success. Two Dependabot status checks failed; details were not exposed by the public summary.
- High-priority open reports: #304 database discovery/load failure, #305 Wayland/NVIDIA startup crash, and #282 related Wayland crash. Maintainer comments say fixes are expected in a later release; not yet validated in a released desktop build.
- Current `CHANGELOG.md` records fixes for #264 (newline paths), #285 (large-scan results after output limit), and #286 (long daemon file-list paths). GitHub still shows those issues open. Treat as code-fixed candidates; verify source tests and released behavior.
- #112's concern that Flatpak bundled/used an internal ClamAV engine appears addressed in current README and source policy: current packages use host ClamAV. Do not carry old issue conclusions forward without version checks.
- Public workflows include dependency audit and CodeQL. This review does not establish the absence of private security alerts.

### All ClamUI issues

Open issues (all 60 returned by the API):
- [#305 ClamUI 0.5.1 crashes on Fedora 44 KDE (Wayland / NVIDIA) – GDK Error 71](<https://github.com/linx-systems/clamui/issues/305>) — ### What happened? ClamUI 0.5.1 installed from Flathub fails to start properly on Fedora 44 KDE running under Wayland with an NVIDIA GPU. When launching the application, its window briefly appears and then closes. The…
- [#304 Clam AV Database still not loading.](<https://github.com/linx-systems/clamui/issues/304>) — ### What happened? This is an issue that was brought up a week ago in #279 . I'm still unable to run a scan. Is there a plan to address this problem anytime soon? I'd like to resume my scheduled scans. ### Steps to…
- [#286 Daemon scans split long paths through clamdscan --file-list and skip files](<https://github.com/linx-systems/clamui/issues/286>) — ## Summary Daemon scans can fail to scan ordinary files whose absolute paths exceed the line capacity of `clamdscan --file-list`. ClamUI routes almost every daemon scan through a generated file list even though the same…
- [#285 Opposing "Full Scan" Results](<https://github.com/linx-systems/clamui/issues/285>) — Setup: Scanning the full system from / in ClamUI. Result: Main scan window claims "Infected" but with 0 threats. The "Details" window ends abruptly with this: [code sample omitted] In Logs -> Historical Logs only this…
- [#282 Error 71 (Protocol error) dispatching to Wayland display (flatpak)](<https://github.com/linx-systems/clamui/issues/282>) — Hi, I'm unable to launch ClamUI after the the latest flatpak update (0.5.1 Rust/Tauri transition) [code sample omitted] This error is a known WebKitGTK/Tauri issue on Wayland, especially with NVIDIA drivers;`…
- [#277 [Feature Request] Improve NixOS + COSMIC desktop integration and security audit detection](<https://github.com/linx-systems/clamui/issues/277>) — Environment NixOS 26.05 COSMIC desktop 1.11 / Wayland Firewall: native nftables, declaratively configured through NixOS Application firewall: OpenSnitch Automatic updates: NixOS system.autoUpgrade / systemd timer File…
- [#264 Daemon scan aborts entirely when any path contains CR/LF/NUL (e.g. HFS+ "Private Directory Data\r" folder) and exclusions or progress are active](<https://github.com/linx-systems/clamui/issues/264>) — **Version:** ClamUI 0.4.1, Flatpak `io.github.linx_systems.ClamUI`, scan backend: daemon (system clamd), Zorin OS (Ubuntu-based). ### Summary When exclusions are enabled (or live progress is used), `DaemonScanner`…
- [#263 Error when scanning directory starting with tilde (~) in its name](<https://github.com/linx-systems/clamui/issues/263>) — Example `clamui '/games/gameX/~mods'`. [code sample omitted] `clamscan` handles it as expected. Would it be possible to handle such a case as a normal directory when it already exists in the filesystem?
- [#252 Scan logs show emails with spoofed domains with no way to follow up](<https://github.com/linx-systems/clamui/issues/252>) — I have just yesterday decided to give ClamAV a try and what I have so far seems to be false positives on emails from several banks. Both the Historical log and the Live Daemon log shows domain spoofing on emails from…
- [#250 Important for Contributors](<https://github.com/linx-systems/clamui/issues/250>) — I am currently in the works of migrating this project to Rust / Tauri, because i felt its a endless dance around dependencies and i personally dislike python pretty much. For those who are contributing languages or code…
- [#247 Official Discord Server of Linx Systems](<https://github.com/linx-systems/clamui/issues/247>) — Hello everyone! i opened a discord server if you want to further discuss development, issues or just want to hang out everyone is welcome! https://discord.gg/TT4zvgksZC
- [#246 Feature Request: Add plastma-firewall detection and compatibility](<https://github.com/linx-systems/clamui/issues/246>) — Firewall GUI (Plasma-Firewall) In CachyOS (KDE Plasma edition), the built-in graphical firewall application is the "Firewall" module within KDE System Settings; the corresponding package is: GUI package: plasma-firewall…
- [#245 Error creating textual authentication agent: Error opening current controlling terminal for the process (`/dev/tty'): No such device or address](<https://github.com/linx-systems/clamui/issues/245>) — With the latest x64 flatpak release 0.4.1, when I try to update virus definitions I get this: [code sample omitted]
- [#241 Add OpenSnitch firewall support](<https://github.com/linx-systems/clamui/issues/241>) — Hello! please consider to add support to OpenSnitch firewall: https://github.com/evilsocket/opensnitch cause on "Audit" settings this firewall is not detected. Thanks a lot!
- [#233 Add a feature to "Manage Network Connections"](<https://github.com/linx-systems/clamui/issues/233>) — So I want a simple GUI feature to manage network connections like. - SSH. - VPNs. - Wireless networks. - Wired networks. - Remote Desktop stuff - Basically any form of connection to your computer. This will protect…
- [#231 Flatpak requires older Gnome runtime](<https://github.com/linx-systems/clamui/issues/231>) — I'm writing to thank you for the ClamUI flatpak, and to encourage you to update the ClamUI flatpak to the current Gnome runtime, as it is the only part of my system that still requires older org.gnome.Platform/x86_64/49.
- [#225 Multi-threading (unable to get above 2 threads)](<https://github.com/linx-systems/clamui/issues/225>) — Hi - I am unable to use multi-threading when running anything through ClamUI. Used clamtop to monitor. If I launch clamdscan --multiscan via command or crontab, then all works as expected, but anything through ClamUI is…
- [#221 Open Minimized To System Tray](<https://github.com/linx-systems/clamui/issues/221>) — In KDE Plasma, I'd like ot get ClamUI to start on boot. I created `ClamUI.desktop` in my `/home/$USER/.config/autostart/` folder using this: [code sample omitted] Then I right-clicked on the ClamUI title in its window,…
- [#217 New Full Scan Error with Unexplained Error Output](<https://github.com/linx-systems/clamui/issues/217>) — I tried to run a full scan. The scan stopped due to an error and gave the following warning: **(It's not even an error!)** [code sample omitted] No idea what this means. **Why are warnings stopping the scan?** Please…
- [#216 Feature: Auto shutdown after scan completed](<https://github.com/linx-systems/clamui/issues/216>) — A nice feature to have if you begin a full scan in the evening and it won't be completed until late night or early morning. When the scan is done the results are logged, threats quarantined and the computer powered…
- [#211 Feature: Add auto-installer for privileged helper when opening the flatpak version](<https://github.com/linx-systems/clamui/issues/211>) — When running ClamUI as a Flatpak, saving configuration changes fails because the sandbox cannot directly write to host system directories like /etc/clamav/. It would greatly improve the user experience if the Flatpak…
- [#208 (request) Why is Chkrootkit the main Rootkit detection in ClamUI when rkhunter exists?](<https://github.com/linx-systems/clamui/issues/208>) — Chkrootkit gets. 1. Less updates. 2. Frequent false positives. 3. Only good for older rootkits. 4. Smaller database. 5. Old and outdated. 6. Only useful if rkhunter misses stuff. While rkhunter has. 1. Bigger and more…
- [#207 (Feature request) Add HIPS?](<https://github.com/linx-systems/clamui/issues/207>) — Inspired by https://help.comodo.com/topic-72-1-766-9163-hips-settings.html So, like, one of ClamAV's problems is there isn't actually a lot of known Linux malware out there. 99% of ClamAV signatures are Windows malware.…
- [#205 GNOME AppIndicator shows placeholder icon when using IconName; IconPixmap works](<https://github.com/linx-systems/clamui/issues/205>) — **ClamUI 0.4.0 Flatpak GNOME Shell 48.7 / Wayland Debian 13 (Trixie) AppIndicator and KStatusNotifierItem Support v64 ClamUI Flatpak runtime: org.gnome.Platform 49** The ClamUI tray item appears and functions normally,…
- [#201 ClamUI 0.3.0 .deb: install-privileged-helper cannot locate bundled polkit policy](<https://github.com/linx-systems/clamui/issues/201>) — Summary ClamUI 0.3.0 installed from the native Debian package fails when attempting to install its privileged configuration helper: sudo clamui install-privileged-helper It reports: Error: Required source file not…
- [#200 Debian 0.3.0 package: install-privileged-helper looks for policy in nonexistent source-tree path](<https://github.com/linx-systems/clamui/issues/200>) — ## Bug: install-privileged-helper expects source-tree layout not present in Debian package ### ClamUI version 0.3.0 ### Installation Debian package: `clamui_0.3.0_all.deb` on Linux Mint Debian Edition 7 (LMDE 7), Debian…
- [#199 Debian 0.3.0 package creates broken systemd scheduled-scan service: No module named 'src'](<https://github.com/linx-systems/clamui/issues/199>) — ## Bug: Scheduled scan systemd service references nonexistent `src` module ### ClamUI version 0.3.0 ### Installation Debian package: `clamui_0.3.0_all.deb` on Linux Mint Debian Edition 7 (LMDE 7), Debian 13 base.…
- [#197 How to set it to automatically start in the system tray](<https://github.com/linx-systems/clamui/issues/197>) — Is there a way to have it automatically minimize to the system tray upon startup?
- [#196 Scan target list out of bounds](<https://github.com/linx-systems/clamui/issues/196>) — the Scan Targets list is out of control. Adding an excessive number of targets causes the window to expand vertically out of bounds where the scan control buttons are pushed out of view. The Scan Targets list could be…
- [#195 Arm64 AppImage](<https://github.com/linx-systems/clamui/issues/195>) — This is missing from the releases tab and I couldn't think of a reason for it to be like that
- [#194 Could not show link](<https://github.com/linx-systems/clamui/issues/194>) — Failed to execute child process gio-launch-desktop (No such file or directory) I'm on kde Logs; [code sample omitted] Error happens when I press the info icon next to open ports.
- [#193 Bundle clamav to the appimage](<https://github.com/linx-systems/clamui/issues/193>) — Any reason not to do this? AppImage is supposed to be portable
- [#187 glob_to_regex does not handle Python 3.14 fnmatch.translate() \z anchor](<https://github.com/linx-systems/clamui/issues/187>) — ## Description The full test suite fails on Python 3.14 because `glob_to_regex()` only strips the `\Z` suffix produced by older versions of `fnmatch.translate()`. Python 3.14 uses `\z` instead. As a result, the…
- [#184 ClamUI should not recommend `apt` on distros without `apt`](<https://github.com/linx-systems/clamui/issues/184>) — Every single suggested fix on this page uses commands my system[^1] doesn't have. The easiest one to do something about is `apt`. I installed ClamUI via the Arch Linux AUR. Distros without Apt are _very_ common. I…
- [#183 --virustotal CLI flag crashes with TypeError, silently falls back to normal ClamAV scan](<https://github.com/linx-systems/clamui/issues/183>) — **ClamUI version:** 0.3.0 (Flatpak, Flathub) **OS:** Linux Mint 22 (Ubuntu 24.04 base) **Install method:** Flatpak ## Steps to reproduce 1. Set up a VirusTotal API key (confirmed present in the system keyring via…
- [#182 [QUESTION] similar repo integration](<https://github.com/linx-systems/clamui/issues/182>) — Hi! Just wanted to ask whether the maintainers are aware of this repo: [https://gitlab.com/dave_m/clamtk](url) and on GitHub: [https://github.com/dave-theunsub/clamtk/issues](url) I think even though outdated, it still…
- [#181 [BUG] Max Archive Recursion error](<https://github.com/linx-systems/clamui/issues/181>) — After setting the value to >101, trying to save, getting the MaxRecursion error, and returning the value to
- [#172 Scan stops with error](<https://github.com/linx-systems/clamui/issues/172>) — Riepilogo: /home/damiano: LibClamAV Error: cli_load(): Can't open file /var/lib/clamav/main.cvd LibClamAV Error: cli_loaddbdir: error loading database /var/lib/clamav/main.cvd LibClamAV Error: cli_loaddbdir: No…
- [#170 ClamUI privileged helper not installed" error when saving configuration (Flatpak)](<https://github.com/linx-systems/clamui/issues/170>) — When attempting to save and apply the configuration changes under Preferenze — Salva, the application fails with a Salvataggio Fallito dialog. The error message states that the privileged helper is missing on the host…
- [#169 Flatpak Database Updater Missing?](<https://github.com/linx-systems/clamui/issues/169>) — I have installed all of the required dependencies for the flapak along with adding the added permissions, but for some reason its still refusing to see the database. I'm running Fedora 44 KDE Plasma Edition I did…
- [#162 _parse_cvd_age() fails on valid CVD headers: stime field absorbs leading bytes of the following gzip stream after ascii decode](<https://github.com/linx-systems/clamui/issues/162>) — **Summary** _parse_cvd_age() in src/core/system_audit.py throws ValueError on valid, healthy .cld files because the stime field (header field 9) gets polluted with binary junk from the immediately-following…
- [#155 [Bug] AppImage: get_clean_env() doesn't strip PYTHONHOME/PYTHONPATH → firewalld falsely reported "not running" in Security Audit](<https://github.com/linx-systems/clamui/issues/155>) — ## Summary On Fedora (AppImage build), the **Security Audit reports "Firewalld is installed but not running" even though firewalld is active and running.** The root cause is that `get_clean_env()` strips…
- [#153 Add support to handle multiple items when the UI is invoked via CLI](<https://github.com/linx-systems/clamui/issues/153>) — This request is about adding support to handle multiple items (files, folders) when the UI is invoked via CLI. This is will allow a better integration with file managers. e.g. nautilus.
- [#150 [Bug] Flatpak scheduled-scan service has malformed ExecStart (whole 'flatpak run …' command is shlex.quoted as one path → 203/EXEC)](<https://github.com/linx-systems/clamui/issues/150>) — ## Summary On the Flatpak build, enabling a scheduled scan generates a **malformed `ExecStart`** in the systemd user service. The entire `flatpak run …` command is passed through `shlex.quote()` as if it were a single…
- [#145 Error when updating database in 0.1.8](<https://github.com/linx-systems/clamui/issues/145>) — Using fedora kde, updated the flatpak a few days ago and am met with this error, Sudo freshclam works fine in the terminal but this error persists
- [#143 INSUFFICIENT PERMISSIONS TO CONFIGURE VIRUS DATABASE IN PREFERENCES](<https://github.com/linx-systems/clamui/issues/143>) — Hi, on Fedora 43, I am unable to modify the virus database configuration in the preferences, even though the /etc/freshclam.conf file is correctly detected and has the following permissions : I am told that I do not…
- [#142 (FEATURE REQUEST) add option (also commands) to enable/disable the freshclam service from running after the scan is over (like i want it only active DURING the scan not after)](<https://github.com/linx-systems/clamui/issues/142>) —
- [#136 [BUG] Database preferences fail to persist after application window preferences restart (Flatpak)](<https://github.com/linx-systems/clamui/issues/136>) — ###System Information (ClamUI) Installation Type: FlatpakRuntime: GNOME 49 (Flatpak runtime) Desktop Environment: X-Cinnamon Python Version: 3.13.13 GTK Version: 4.20.4 (libadwaita 1.8.5) Kernel:…
- [#130 ClamUI (Flatpak) Does Not Detect Installed "Lynis" or "chkrootkit"](<https://github.com/linx-systems/clamui/issues/130>) — I recently installed ClamUI v 0.1.7 (Flatpak) and ran the "Audit" function. It indicated I did not have either "Lynis" or "chkrootkit" installed. However, I did not use the "sudo apt install lynis" or "sudo apt install…
- [#122 [Feedback] Flatpak - Installation scripts for different package managers](<https://github.com/linx-systems/clamui/issues/122>) — Hi! Firstly, I want to thank you for the app, it is really awesome, you did a really nice job and I appreciate that! I think that my issue could be separated into several issues and should not be viewed as a complete…
- [#112 Critical architectural refactoring: Internal ClamAV dependencies and Flatpak sandbox isolation issues](<https://github.com/linx-systems/clamui/issues/112>) — WARNING: I had the opportunity to analyze the project's github and I can say that it was entirely written in vibe-coding and has structural problems that are quite serious for me, the main problem is that the project…
- [#111 Not a serious issue and Not a bug, rather a Personal Observation on the Portmaster Firewall Missing from security Audit Detection module.](<https://github.com/linx-systems/clamui/issues/111>) — Hi, Upon review of the latest update of ClamUi, Which is absolutely awesome, I realized that what I would classify as one of the great "new" features "Audit" which offers amazing guidance for anyone attempting to harden…
- [#110 Debian 12  Fails to Install Daemon Scanner so now ClamUI Crashes.](<https://github.com/linx-systems/clamui/issues/110>) — I installed ClamUI via Flatpak. I'm running Debian 12 and I could scan my system before installing both the "Daemon Scanner Client" and "Daemon Scanner." I decided to install both of the Daemon Scanner components so I…
- [#102 [Bug] When a scan completed, `flathub`'s `0.1.6` returned an error log, whose length exceeded that of the visible viewport.](<https://github.com/linx-systems/clamui/issues/102>) — Without utilising what [`KDAB/hotspot/issues/713#issuecomment-3349512977`](https://github.com/KDAB/hotspot/issues/713#issuecomment-3349512977) describes, the minimum size that the window permits is 100 % of the height…
- [#100 [Bug] `flathub`'s `0.1.6` returns `Gtk-WARNING`s, due to “Broken accounting of active state for widget”.](<https://github.com/linx-systems/clamui/issues/100>) — Normal usage of the application returns warnings to `STDOUT`: [^1] [^1]: [`gitlab.gnome.org/GNOME/glib/-/issues/2738`](https://gitlab.gnome.org/GNOME/glib/-/issues/2738#note_2575540) ~~~console…
- [#95 "Surrogates not allowed" while trying to scan /home directory](<https://github.com/linx-systems/clamui/issues/95>) — Good morning! I'm trying to scan my /home directory, but always do this error: My system info: [code sample omitted]
- [#92 Clarifications on Update Automation and Sandbox Database Paths](<https://github.com/linx-systems/clamui/issues/92>) — Hi, I'm using **ClamUI 0.1.6** (Flatpak) on Linux Mint. The app is now much more stable, but I need some technical clarifications regarding database management and automation: 1. **Current Sandbox Path**: Currently, my…
- [#57 Bug Report - Fedora 43 KDE - Scanner - Configuration File](<https://github.com/linx-systems/clamui/issues/57>) — Distro: Fedora 43 KDE In the settings scanner I need to manually select the right folder Then when I click on Open folder I get Thank you
- [#20 Application window is not adaptive](<https://github.com/linx-systems/clamui/issues/20>) — The height is too large for my screen and there are innaccessible widgets in the bottom
- [#11 Circle application](<https://github.com/linx-systems/clamui/issues/11>) — Would you consider applying for GNOME Circle and adhering to GNOME HIG?

Closed issues visible in the same API snapshot (12):
- [#287 Request - Audit menu firewall](<https://github.com/linx-systems/clamui/issues/287>) — closed; recheck version applicability if revisited.
- [#281 Add Vietnamese (vi) localization](<https://github.com/linx-systems/clamui/issues/281>) — closed; recheck version applicability if revisited.
- [#280 Flatpak helper installation rejects Ubuntu’s sha256sum symlink](<https://github.com/linx-systems/clamui/issues/280>) — closed; recheck version applicability if revisited.
- [#279 Virus database is not available  No ClamAV database files were found in standard host locations](<https://github.com/linx-systems/clamui/issues/279>) — closed; recheck version applicability if revisited.
- [#278 Unnecessary privileged helper installation dialog on Arch Linux](<https://github.com/linx-systems/clamui/issues/278>) — closed; recheck version applicability if revisited.
- [#276 Add privileged helper for rpm-based system or advanced config export (v0.4.1)](<https://github.com/linx-systems/clamui/issues/276>) — closed; recheck version applicability if revisited.
- [#253 Privileged Helper Not Installing](<https://github.com/linx-systems/clamui/issues/253>) — closed; recheck version applicability if revisited.
- [#242 Flatpak: privileged helper install always fails signature check (key ownership check can't pass in sandbox)](<https://github.com/linx-systems/clamui/issues/242>) — closed; recheck version applicability if revisited.
- [#198 Bug pour verification ClamUI](<https://github.com/linx-systems/clamui/issues/198>) — closed; recheck version applicability if revisited.
- [#185 Can't use clamav daemon](<https://github.com/linx-systems/clamui/issues/185>) — closed; recheck version applicability if revisited.
- [#173 Brave , Adguard, UBlockorigin](<https://github.com/linx-systems/clamui/issues/173>) — closed; recheck version applicability if revisited.
- [#163 Dependency problems - policykit bug](<https://github.com/linx-systems/clamui/issues/163>) — closed; recheck version applicability if revisited.

### ClamUI live refresh (2026-11-11)

GitHub REST API snapshot: 61 open issues and 2 open pull requests. The 61st open issue is [#306](https://github.com/linx-systems/clamui/issues/306): a failed configured `DatabaseCustomURL` feed (HTTP 410) appears to prevent later custom URLs from being processed. Linux Defender does not add arbitrary third-party feeds: it ships one reviewed product-default URLhaus export and leaves the explicit Save & Apply step to the user. Do not add other feeds without checking provider integrity, licensing, and failure isolation. Issue [#305](https://github.com/linx-systems/clamui/issues/305) remains open, but maintainers state its Wayland/NVIDIA startup fix is in ClamUI 0.6.0; Linux Defender's Flatpak manifest includes the related WebKit workaround. Issue [#304](https://github.com/linx-systems/clamui/issues/304) remains open as a Debian 12 Flatpak reproduction of #279; host database discovery code is present, but that exact environment is not verified. The current GitHub state is not equivalent to closing these reports.

The post-release updater fix from upstream commit `30a72f0` (#307) is ported locally. Existing open issue reports remain tracked whether or not source fixes are present.

### Dated upstream snapshot (2026-11-25; superseded by the 2026-11-27 sweeps below)

Snapshot GitHub API counts from that date; the 2026-11-27 sweeps and the reviewed pin in `parity-lock.json` are authoritative for current state:

| Repository | Open issues | Open PRs | Default-branch head |
|---|---|---|---|
| `linx-systems/clamui` | 57 | 7 | `6bfc4d50da50463e9e6f70259886a4d78d3af677` (reviewed 2026-11-27; current default-branch head, zero open PRs) |
| `vmkspv/lenspect` | 0 | 0 | `a5507a6c8ec1bdf1f2222e7397d053ff365b3d70` |
| `dave-theunsub/clamtk` | 23 | 4 (#168, #169, #170, #141) | `694833d27c800e7c3ac4ff6dd44f0b2e65025260` |
| `Linux-Defender/Linux-Defender` | 0 | 0 | local `main` (checked at recheck time) |

All reviewed heads in `parity-lock.json` (ten upstream repositories) and the
AUR reference in `packaging-lock.json` were fetched again and match their live
heads; `check-upstream-freshness.py` reports zero drift and zero errors. Older
counts above are historical snapshots, not claims about the current state.

New report reviewed this round: ClamUI issue
[#361](https://github.com/linx-systems/clamui/issues/361) describes a blank
gray window on Flatpak 0.5.1 under X11 with Intel i915. Upstream tried
`WEBKIT_DISABLE_DMABUF_RENDERER=0`, `WEBKIT_DMABUF_RENDERER_FORCE_SHM=1`, and a
fresh profile without a fix; the issue remains open with no confirmed root
cause. **Disposition: monitored, no speculative code change.** Linux Defender
already applies `WEBKIT_DISABLE_DMABUF_RENDERER=1` before webview creation on
NVIDIA proprietary drivers and has a top-level React error boundary with Retry;
neither is claimed to address an Intel/X11 compositing fault. Do not claim this
upstream report is fixed here without a reproduction and a tested mitigation.

### Upstream refresh (2026-11-25, master `14362e804b65f44e9e4e777a1c13b98c36b1a926`)

The smaller UI commits in this range are dispositioned here rather than left implicit: #340 (verdict-first results and right-aligned log actions) is **covered** by `desktop/src/pages/ScanProgressPanel.tsx` and the Results page; #335/#336/#337 (About icon, `clamd.conf` card styling, header blend) and `fd2481dc` (signature database setup copy) are **deferred as cosmetic** — the Guardian design system owns our visual identity and our setup guidance is already checked by `check-host-tool-guidance.py`; `facc4647` (expanded audits/progress preservation) is **covered** by the existing audit domain and coalesced scan progress. No GPL or unreviewed code was copied.

Reviewed the current default branch, which advanced from `30a72f0` (2026-11-11) to `14362e8` (2026-11-20). Dispositions, verified against code rather than the merge status alone:

- **Host-tool component guides and copy-only warning (#357 era Components page):** the component guides are ported and extended. The four distro families (Ubuntu/Debian, Fedora Workstation, Fedora Atomic, Arch Linux) and all eight component commands are present in `desktop/src/pages/Components.tsx`; this pass aligned daemon commands to `systemctl enable --now` and added the missing Fedora Atomic block plus a copy-only note to the website daemon guide. `scripts/check-host-tool-guidance.py` enforces the app/site/upstream alignment.
- **Classic-confinement Snap package (#357/#360):** Linux Defender has its own `snap/snapcraft.yaml` and launcher; no upstream code copied. Integration asset parity is enforced by `scripts/check-integration-parity.py`.
- **Dashboard layout (#351), Preferences autosave/Flush UI (#350):** deliberately deferred/superseded, as recorded in `docs/clamui-fork/STATUS.md`; Linux Defender keeps `Overview` and explicit **Save & Apply**.
- **Scan-profile description overlap (#333), sidebar descender clipping (#348), accent via XDG portal (#334), editable path lists (#345), On-Access authorization fix (#349), trusted local tool symlinks (#347), audit/firewall/opensnitch expansions (#322/#323, #329/#338):** independently implemented or already recorded in `STATUS.md`; no blind code copy.
- **Fail2ban Wayland command copying (#332):** our core already exposes Fail2ban per-distro commands in `host.rs`; the Wayland clipboard path uses the scoped native clipboard helper rather than an X11 selection.

Newer upstream work is reviewed here, not auto-merged. Licensing, privacy, credentials, cancellation, platform scope, and tests are checked before any adoption.

### Upstream refresh (2026-11-25, master `c424a42d71597aa3116b680a97b0b9cdfd094bb0`)

Upstream commit `c424a42` (#362) adds descriptive notes and `<code>` formatting for On-Access behavior settings. Ported into `desktop/src/pages/ConfigPreferences.tsx`: the four behavior toggles now show static-literal explanations with translator notes for `fanotify`, `inotify`, and `DDD`, and exact technical terms are wrapped without putting markup into gettext msgids. Four new IDs were merged into all ten catalogs with English fallback pending human review. No upstream catalog churn was copied.

### Upstream refresh (2026-11-25, master `d14019b7edd15d583c9006e0f489c4c68b943229`)

Upstream commit `d14019b` replaces em dashes with hyphens in website copy. **Deliberately not adopted:** Linux Defender's contributor rules require the Unicode em dash `—` for prose breaks, and our website already passes its link/style checks. No code, catalog, or configuration behavior changed. Recorded so the newer snapshot is reviewed rather than silently missed.

### Upstream refresh (2026-11-26, master `e26e1e40dbfcdacfa32bed85343367913f50b966`)

The reviewed ClamUI pin moved from `d14019b` to `e26e1e40` after two merged PRs; both were reviewed from their diffs rather than from merge status alone.

- **#365 — `cookie` 0.18.3, `form_urlencoded` 1.2.3, `url` 2.5.9 for RUSTSEC-2026-0594/-0592:** **already satisfied here.** Our locked workspace uses exactly those versions (verified in `Cargo.lock` and `flathub/cargo-sources.json`), and `cargo audit` passes in the Dependency Audit workflow. No further change needed.
- **#363 — CI path filters, PR concurrency cancellation, Rust caching, and job timeouts:** **behavior adopted where it fixes a real defect.** Superseded pull-request runs previously continued and produced cascades of stale failures/warnings (visible in the Actions history for PR #16). All PR-triggered workflows now use a PR-scoped `concurrency` group with `cancel-in-progress: ${{ github.event_name == 'pull_request' }}`; pushes to `main`, manual runs, schedules, and reusable calls stay unique and are never cancelled. `scripts/check-workflows.py` enforces this with documented exemptions for `auto-assign.yml` (opened only) and `dependabot-refresh.yml` (its own guarded generation group). Job timeouts were also ported: all jobs with a runner now declare `timeout-minutes` (5–60 by workload). Path filters and Rust caching are deliberately deferred: `check-all.sh` must run on every PR here, and adding a third-party cache action is not needed for correctness.

The new head is pinned in `parity-lock.json` with review date 2026-11-26; `check-upstream-freshness.py` reports zero drift for all ten upstream references. The weekly checker's review issues (#21 and #22) are closed with these dispositions; unreviewed upstream content is still never auto-merged.

### Upstream tab sweep (2026-11-26, default branch `master` `e26e1e40dbfcdacfa32bed85343367913f50b966`)

All five upstream tabs were reviewed from the GitHub API: repository branches/commits, 57 open issues, 7 open PRs, 100 recent Actions runs, and the Security tab. The default branch is still `master` at our reviewed pin; upstream's `main`, `feature/live-view`, `feature/system-audit`, and the top-issues review branch are all hundreds of commits behind and contain no new behavior. `diag/startup-diagnostics-361` (PR #366) is the only branch ahead.

The 410 upstream files were compared to our 647 tracked files after normalizing rebranded names. The only missing behavior-bearing component was `website/src/components/TerminalDemo.astro`; a **SFW, Linux Defender-branded adaptation** now renders in the Hero: static illustrative `linux-defender-cli scan` output, GNOME-style headerbar, no external scripts, links, or adult/third-party content, decorative `aria-hidden`. Everything else on the normalized missing list is either a rebrand (icons, desktop files, Flatpak manifests, Nautilus scripts), a deliberately superseded page (`Dashboard`, `ScanOverview`, `scanHistory`, screenshots), the logos we replace with the Guardian shield, a `CNAME` for upstream's custom domain, or the `packages.yml` gating workflow deferred in row 72. GitHub-managed dynamic workflows cannot be ported as files; our Dependabot Updates entry is active and our checked-in CodeQL now covers the same languages as upstream's dynamic quality run. We tested enabling GitHub default code-scanning setup via the API (languages `actions`, `javascript`, `javascript-typescript`, `python`, `typescript`, `extended` suite, weekly). GitHub disabled our advanced `codeql.yml` and the next advanced analysis failed with **"CodeQL analyses from advanced configurations cannot be processed when the default setup is enabled"**. Default setup cannot analyze Rust, so we restored `state: not-configured`, re-enabled the advanced workflow, and reran the failed analysis green. **Do not enable default setup again** while the advanced workflow is the source of truth; the advanced workflow already includes `+security-and-quality` queries. The separate Code Quality setup API (`/code-quality/setup`) is also unavailable here (HTTP 404: "Code quality is not available for this repository"), so upstream's `dynamic/github-code-quality/codeql` entry cannot be enabled from this repository; our checked-in quality queries are the enforced equivalent.

- **PR #366 — blank-window startup diagnostics (#361/#315):** does not fix the blank window; it records native milestones and reports why React never mounted. **Behavior ported independently and more narrowly:** the frontend calls the existing `app.startup_ready` operation after mount; the core records the marker through the existing domain dispatcher, and a native watchdog writes one debug warning after ten seconds if React has not mounted. No new Tauri command, capability, permission file, or generated boot JavaScript was copied — our `UiErrorBoundary` already renders a retryable error instead of a blank window. Regression test: `crates/linux-defender-core/tests/startup.rs`.
- **Dependency PRs #352–#356 and #299:** **already satisfied or superseded** — our lock has `rusqlite` 0.43.0, `zbus` 6.5.0 for the desktop crate (with 5.19.0 only as a transitive dependency), the current minor-patch frontend/website locks, and desktop TypeScript 7.0.2 while website stays on 6.0.3 where its checker requires it. No blind lockfile copy.
- **Issue #285 (opposing "Full Scan" results / truncated stdout):** the upstream fix branch was already deleted, but the behavior is covered here by `final_results_keep_late_threats_skips_and_warnings_for_both_backends` and `explicit_zero_summary_after_truncation_overrides_progress_hint`: late threats survive the display cap and status stays honest.
- **Issue #264 (CR/LF/NUL paths abort daemon scans):** still open upstream. **Covered here:** daemon scans route LF/CR (and over-long) paths through stdin and keep them out of the file list; NUL paths are rejected before any host command. Both branches have unit tests. The two older records of this issue were contradictory; this is the single current disposition.
- **Other open issues** (#306 custom-feed failure isolation, #183 CLI VirusTotal crash, #155 host-env leakage, #162 CVD age parsing, #187 glob regex anchors, #252 log privacy, #263 tilde paths, #277 NixOS/COSMIC): reviewed against our existing implementation and records; none revealed an unported behavior that passes our security/privacy/licensing checks. Open upstream reports are not claimed fixed here.
- **Upstream Actions:** every failure in the last 100 runs belongs to unmerged branches (`fix/285-truncated-infection-count`, `ci-demo/*`, `ci/optimize-workflows`, `fix/audit-cookie-url`); the default branch is green. Their path-filter/concurrency work was already reviewed and adopted in the previous pass.
- **Security tab:** the API returned HTTP 403 for upstream Dependabot/code-scanning alerts and 404 for secret scanning, so alert contents could not be inspected. This is an access limitation, not a clean bill of health; our own repositories report zero alerts.

### Legacy personal projects reviewed (2026-11-26)

Two old personal sources were scanned in full at the user's request: the Sololearn playground `WQMCKCuGYHMa` and `CherrieFurry/LizXRown-Eipril-Animations` (default branch `main`: `LICENSE`, `README.md`, a 101 KB `index.html`, a 95 KB `script.js`, and a 1.2 KB `style.css`; the deployed GitHub Pages file is byte-identical to the repo's `index.html`).

**Disposition: no source copied; one safe metadata pattern adapted.** The only useful piece here was `<meta name="author">`, now present in our own site layout as `<meta name="author" content="Linux Defender contributors">` — a SFW adaptation, not the old project's text or attributes. Everything else was left out after a piece-by-piece review:

- The repository declares **EPL-2.0** (weak copyleft), not MIT. Moving its source verbatim into this MIT-licensed project would need an explicit relicensing decision. Independently implemented behavior is allowed, but none of the behavior here is worth reimplementing.
- The HTML is invalid: `<title title=... value=...>`, a `link:` pseudo-attribute, `<link>`/`<script>` with both `href` and `src`, closing `</link>`, two elements with `id="middle"`, `<br></br>`, and obsolete `align`/`font-size` attributes. Our `check-built-links.py` rejects duplicate IDs, and Starlight/HTML-Proofer would reject the rest; Lighthouse would lose accessibility/SEO points.
- It embeds third-party adult-content iframes plus `trafficjunky` and `api.hubtraffic.com` tracking, and loads old jQuery 3.2.1 and PrefixFree 1.0.7 from CDNs. Those conflict with the strict Tauri CSP, privacy guarantees, and the product's purpose.
- `<grammarly-desktop-integration>` / `<grammarly-mirror>` are injected by a browser extension (the deployed page carries Grammarly's `data-gr-ext-installed` marker); they are not application markup, do nothing in WebKitGTK, and adding inert custom elements would be misleading. The SFW equivalent in Linux Defender is the real native clipboard/export boundary plus the retryable React error boundary, both already implemented.
- StyleFix/PrefixFree (Lea Verou, MIT) was a 2013 vendor-prefix helper. Its license would allow copying with notice, but the behavior is obsolete on modern WebKitGTK and our Vite build; bundling the minified library would add dead weight and a second JS library. Its only useful idea — declaring who made the page — is adapted via our new `author` meta tag. The CSS is a table-cell centering layout already superseded by the Guardian flex/grid system.

A repo-wide grep confirms none of those markers exist in Linux Defender source, docs, or built site. This record exists so a future sweep does not treat the old projects as unported parity work.

### Lazaret fork review (2026-11-26)

`wvhulle/lazaret` is an MIT-licensed GTK4/Rust hard fork of ClamUI (`linx-systems/clamui`, also MIT) at `9829dde`. Its fork branch `Linux-Defender:patch-1` (since deleted) added only a generic GitHub Security Policy template, so there was no code patch to import. Linux Defender already ships an equivalent, project-specific policy: `SECURITY.md` (private advisory reporting), `SECURITY.txt` (RFC 9116), the published `contributing/security` guide, and links from the README and website footer. The generic template's link-only behavior is therefore already covered; no template text was copied. Three read-only agents reviewed its docs/features, Rust crates, and all GitHub tabs; dispositions:

- **Ported:** FreshClam output now recognises custom signature databases (`.hdb`, `.ndb`, `.ftm`, `.idb`, `.ldb`) as updates — this covers the product-default URLhaus `.ndb` feed, which previously could be recorded as "no result". Path-valued ClamAV directives now reject `..` traversal. Both have regression tests.
- **Checked, already correct here:** file-manager/CLI handover replaces target lists (no duplicate rescan), and config overrides clear stale repeated directive lines. No change needed.
- **Deferred deliberately:** per-user trust-by-hash store, automatic quarantine re-verification after signature updates, CIRCL hashlookup, MalwareBazaar and Talos sample reporting, live clamd tuning with expiring protection reductions, setting provenance UI, and structured admin audit journal. Each needs new UI/privacy/state decisions or a privileged-service redesign; none is an unreviewed upstream fix we are ignoring. Their upstream commits and privacy implications are recorded here so they are not treated as forgotten parity work.
- **GitHub tabs:** issues disabled, PRs and code scanning inaccessible with this token, no Actions runs (CI is Woodpecker/Forgejo/Nix), no releases on GitHub. License obligation is only to retain the MIT notice; no GPL code was copied.

### ClamAV Bytecode Compiler reference (2026-11-25)

Reviewed `Cisco-Talos/clamav-bytecode-compiler` at `a1830a442110325d04708145437a5312fc6ab6f9` (GPL-2.0, latest release `clambc-1.4.0`). It compiles cross-platform ClamAV bytecode signatures for advanced detection. **Disposition: reference only, not adopted.** Linux Defender never bundles an engine or signature database, uses the host `clamscan`/`freshclam`/`clamd` boundary, and implements local `.yar`/`.yara` support independently under MIT. Its GPL-2.0 code cannot be copied into this repository without an explicit licensing decision. Its head is pinned in `parity-lock.json` and watched by `Upstream Freshness`.

### Open ClamUI pull requests

- [#318 fix(scan): keep summary infection counts when threats are truncated](https://github.com/linx-systems/clamui/pull/318): opened 2026-11-16 from the fork `Linux-Defender/clamui` against `master`. It ports the #285 count behavior to upstream `clamui-core` (summary lower bound, at-least-one for exit code 1, accumulator and aggregate sums) and to the desktop result notice. The local account has read-only access to `linx-systems/clamui`, so this is a fork PR, not a direct push. Its core tests, clippy, frontend check, and frontend build pass locally.
- [#299 TypeScript 5.9.3 → 7.0.2](https://github.com/linx-systems/clamui/pull/299): website-only. Deferred: Astro 7.4.5 `astro check` fails with TypeScript 7.0.2 and reports that TypeScript 6 is required.
- [#298 website dependency group update](https://github.com/linx-systems/clamui/pull/298): website manifest/lockfile only; adopted and validated in Linux Defender website check/build. This does not alter ClamTk parity.

### ClamUI issue dispositions verified against this runtime (2026-11-16)

Rechecked the current open ClamUI reports against the Rust/Tauri implementation after commits through `39d81ce`. “Covered” means the owning code path and regression test exist in this repository; it does not mean the upstream report is closed or that the behavior was exercised interactively.

| ClamUI issue | Linux Defender implementation | Status |
|---|---|---|
| [#317](https://github.com/linx-systems/clamui/issues/317) Lynis hangs on a prompt | Deep audits run `lynis audit system --cronjob --quiet` through pkexec; audit host commands receive closed stdin so an unexpected prompt gets EOF, and a timeout now terminates the whole audit process group so wrappers cannot keep the output pipes open. Regression tests cover both the prompt and the descendant-holding-pipes case. | Covered locally |
| [#315](https://github.com/linx-systems/clamui/issues/315) blank screen on launch | Native startup sets `WEBKIT_DISABLE_DMABUF_RENDERER=1` before webview creation when the NVIDIA proprietary driver is present, matching the Flatpak runtime. A top-level React error boundary now shows the error and a Retry button instead of leaving an empty window when rendering fails. Other blank-screen causes still need the user’s log output. | Mitigation added; root cause unconfirmed |
| [#306](https://github.com/linx-systems/clamui/issues/306) failed custom database URL stops later sources | The configuration UI validates and preserves each `DatabaseCustomURL` entry, and update results surface per-database progress plus freshclam’s failure text. The order and stop-on-failure behavior belong to the host freshclam client; Linux Defender documents the workaround instead of rewriting host source order. | Documented; host behavior |
| [#285](https://github.com/linx-systems/clamui/issues/285) “Infected” with zero threats | The scanner now reads the `Infected files:` summary and keeps a count of at least one when ClamAV exits with a detection but the per-file lines were truncated. The UI shows that count and the existing “details unavailable” warning instead of “0 threats”. The same behavior is proposed upstream in [PR #318](https://github.com/linx-systems/clamui/pull/318). | Covered; regression test |
| [#305](https://github.com/linx-systems/clamui/issues/305) / [#282](https://github.com/linx-systems/clamui/issues/282) Wayland/NVIDIA startup failure | Flatpak manifest carries the WebKit workaround; the native runtime now applies it automatically for NVIDIA drivers. | Mitigation available; needs CachyOS/KDE validation |
| [#264](https://github.com/linx-systems/clamui/issues/264) daemon scan aborts on CR/LF/NUL paths | Daemon scans route paths containing LF/CR (or over the clamdscan line limit) through stdin and keep the file list free of them. | Covered; unit tests |
| [#263](https://github.com/linx-systems/clamui/issues/263) directory containing `~` | Only a leading `~` or `~/` is expanded; a `~` later in the path is left literal. | Covered |
| [#246](https://github.com/linx-systems/clamui/issues/246) Plasma Firewall detection | Audit probes `plasma-firewall`/`plasma5-firewall`/`plasma6-firewall` package ownership and reports it as a backend manager, not as policy evidence. | Covered |
| [#245](https://github.com/linx-systems/clamui/issues/245) no textual Polkit agent | Packaging/runtime environment issue: a graphical Polkit agent must be running for pkexec. Not replaced with password prompts inside the app. | Open; environment |
| [#241](https://github.com/linx-systems/clamui/issues/241) OpenSnitch detection | Audit inventories OpenSnitch as an optional network/application firewall monitor; it does not claim policy verification. | Partial inventory |
| [#225](https://github.com/linx-systems/clamui/issues/225) daemon scans use few threads | Daemon scans currently expand targets into file lists, so `clamdscan --multiscan` parallelism is not exposed. | Open feature |
| [#221](https://github.com/linx-systems/clamui/issues/221) / [#197](https://github.com/linx-systems/clamui/issues/197) start minimized to tray | `start_minimized` preference, tray availability check, and close-to-tray policy are implemented with tests. | Covered; desktop UX unverified |
| [#217](https://github.com/linx-systems/clamui/issues/217) ClamAV warnings stop a full scan | Known nonfatal LibClamAV warnings (limits, truncation, unrar, bytecode timeout) are classified as warnings/skips rather than scan failure; hard errors still fail. | Covered |
| [#216](https://github.com/linx-systems/clamui/issues/216) shut down after scan | Not implemented; needs a scoped shutdown action and explicit consent. | Open feature |
| [#205](https://github.com/linx-systems/clamui/issues/205) GNOME tray placeholder with IconName | the SNI tray publishes `IconPixmap` data from the app icon rather than relying on `IconName`. | Covered |
| [#201](https://github.com/linx-systems/clamui/issues/201) / [#200](https://github.com/linx-systems/clamui/issues/200) packaged helper cannot find its Polkit policy | Helper/CLI installer resolves the packaged policy path, stages with fixed modes, and rejects mutable prefixes; tests cover staging and symlink destinations. | Covered; needs installed-package validation |
| [#199](https://github.com/linx-systems/clamui/issues/199) Debian package creates a broken Python scheduled-scan service | This runtime has no Python service; the Rust scheduler writes quoted systemd units and cron entries with regression tests for specifier/`$`/adversarial target escaping. | Covered |
| [#196](https://github.com/linx-systems/clamui/issues/196) scan target list pushes controls out of view | The Scan page target list is bounded to `min(40vh, 420px)` with its own scroll area. | Covered |
| [#195](https://github.com/linx-systems/clamui/issues/195) arm64 AppImage | AppImage packaging remains x86_64-only per the current release matrix. | Open |
| [#194](https://github.com/linx-systems/clamui/issues/194) `gio-launch-desktop` missing | External URLs and paths go through the `open` crate’s platform fallbacks rather than a hard-coded `gio-launch-desktop` call. | Covered by implementation |
| [#184](https://github.com/linx-systems/clamui/issues/184) recommends `apt` on non-apt distros | Audit/component install commands are selected from `/etc/os-release` for Debian, Fedora, Fedora Atomic, and Arch families. | Covered |
| [#183](https://github.com/linx-systems/clamui/issues/183) `--virustotal` CLI crashes | This CLI has no `--virustotal` route; VirusTotal is an explicit UI/API workflow with consent. | Not applicable |
| [#170](https://github.com/linx-systems/clamui/issues/170) / [#169](https://github.com/linx-systems/clamui/issues/169) Flatpak helper/database missing | Host database discovery and the versioned pkexec helper exist; Flatpak reaches host tools through `flatpak-spawn --host`. | Covered; Flatpak desktop validation open |
| [#153](https://github.com/linx-systems/clamui/issues/153) multiple CLI/file-manager items | upstream `clamui scan` accepts multiple paths, preserves each target’s identity, and reports per-target results. | Covered |
| [#150](https://github.com/linx-systems/clamui/issues/150) malformed Flatpak ExecStart | The Rust scheduler builds the Flatpak launcher as separate, quoted arguments; tests cover escaping. | Covered |
| [#142](https://github.com/linx-systems/clamui/issues/142) enable/disable FreshClam service | Update Assistant reports and controls the supported host FreshClam service/timer, including Arch’s `clamav-freshclam-once.timer`, using nonblocking systemd requests. | Covered; authorization/desktop validation open |
| [#95](https://github.com/linx-systems/clamui/issues/95) non-UTF-8 paths fail | Paths cross the native/headless boundary in a byte-preserving wire form, and CLI targets now resolve through the same encoding so a UTF-8 symlink to a non-UTF-8 file is not corrupted (regression test). | Covered |
| [#20](https://github.com/linx-systems/clamui/issues/20) / [#102](https://github.com/linx-systems/clamui/issues/102) window too tall | Main content uses a page scroll container, dialogs are viewport-bounded, and the scan target list is now height-bounded. | Mitigated; small-screen validation open |

## ClamTk desktop integration repositories

### Tray and desktop action comparison

ClamTk has no tray implementation in its current source; upstream issue [#142](https://github.com/dave-theunsub/clamtk/issues/142) requests one. The ClamUI tray code already used by this unified app toggles the window on primary/left click. Its secondary/right-click menu offers Show, Quick Scan, Full Scan, Update Database, scan profiles, and Quit. Keep that single tray implementation; actual left/right-click behavior still needs testing in CachyOS KDE Plasma and GNOME (including their SNI/AppIndicator watcher requirements).

ClamUI already provides file-manager actions for Dolphin, Nautilus, and Nemo. Linux Defender now includes Thunar “Send To” scan and VirusTotal actions in its Flatpak integration manager. The ClamTk companion projects document Dolphin/Konqueror right-click actions, Nautilus actions, Nemo actions, and the Thunar “Send To” action, but their repositories are unmaintained. Port the user-facing behavior into Linux Defender’s packaging instead of copying those legacy add-ons wholesale. Ensure every integration passes all selected paths; `%F` multi-selection must not silently scan only the first item. The Thunar action’s install/remove behavior has unit coverage, but needs real XFCE/Thunar testing.

| Repository | Reviewed snapshot | Open issues / PRs | Review and disposition |
|---|---|---|---|
| [clamtk-kde](https://github.com/dave-theunsub/clamtk-kde) | `8102f93a0800e627715c5e14e8e61e5ee9ad5ac0` (2024-03-30); release `v0.20`; `clamtk-kde.desktop` uses `ServiceTypes=KonqPopupMenu/Plugin`, `MimeType=all/allfiles;inode/directory;`, `Exec=clamtk %F`, `X-KDE-StartupNotify=true;`. | Issues #1 multi-file scan, #2 missing Dolphin service-menu entry for old KDE Neon .deb; no open PRs. | **Behavior ported:** the three Dolphin/Konqueror service menus now use `all/allfiles;inode/directory;` so text, images, and archives get the action too; a regression test guards the MIME and service keys. `%F` already passes every selected path. `X-KDE-StartupNotify` is intentionally not added (the app supplies its own launch feedback). |
| [clamtk-gnome](https://github.com/dave-theunsub/clamtk-gnome) | `d006384dd4a2c311c1d437e8fea9a627218b5d63` (2024-03-30); release `v6.16`; Python extension resolves `GFile` paths and launches with list-form `subprocess.Popen(["clamtk", filename])`; separate folder-background item labelled “Scan directory for threats...”. | 9 open issues; PR #18 ports to Nautilus 43/API 4. | The default tree already contains the Nautilus 4.0 import and `*args` callback changes proposed by open PR #18, so there is no separate patch to cherry-pick. **Already covered:** list-form launching and multi-target pass-through. **Deliberately deferred:** the folder-background menu item would require a `nautilus-python` extension, conflicting with the no-Python-runtime preference; our Nautilus scripts handle selected paths only. |
| [nemo-sendto-clamtk](https://github.com/dave-theunsub/nemo-sendto-clamtk) | `e47f2c486e43c9e65e3aa4e906465a9601ec66b8` (2024-03-30); release `v0.07` (`0.07-2` deb); `Selection=Any`, `Quote=double`, `Exec=clamtk %F`. | No open issues/PRs; one closed translation PR. | **Covered:** our Nemo actions use `Selection=any`, `%F`, and no shell wrapper; current Nemo already escapes shell metacharacters, so `Quote=double` is legacy robustness rather than a security requirement. No code copied. |
| [thunar-sendto-clamtk](https://github.com/dave-theunsub/thunar-sendto-clamtk) | `583e270f114074b639c5b8282cc9d50d9dd1d576` (2024-03-30); release `v0.08-2`; desktop entry uses `TryExec=clamtk`, `%F`, `OnlyShowIn=XFCE;`, and ~50 localized `Name`/`Comment` fields. | No open issues; open PR #3 is README-only. | **Covered:** our Thunar Send To actions pass `%F` through the same multi-target scanner. `TryExec`/localized labels are intentionally not copied: native and Flatpak assets must stay launcher-aligned, and adding new gettext IDs requires catalog parity. Do not merge README-only changes into core. |
| [build_files](https://github.com/dave-theunsub/build_files) | `3adf6b6e18d6af3b824aa0e9ecc4ebce011734b6` (2024-01-27). | Not tracked. | **Packaging precedent only.** Lists distro build inputs for ClamTk and all four plugins. No build dependency; our six package formats are maintained independently. |
| [thunar-sendto-shredder](https://github.com/dave-theunsub/thunar-sendto-shredder) | `78cf7592d6a543f376ab1fcb49d42125ee73c752` (2019-04-11). | Not relevant. | **Integration-pattern reference only.** Its destructive shredding semantics are explicitly not ported; Linux Defender never bulk-deletes without consent and recoverable restore. |

All six heads are pinned in `parity-lock.json` and watched by the weekly
`Upstream Freshness` workflow. When any of them moves, review the diff before
refreshing the pin — never auto-merge unreviewed upstream content.

### Integration fixes adopted from this review (2026-11-25)

These were implemented independently under MIT from the behaviors above; no
GPL/Artistic source was copied:

- **Dolphin MIME coverage:** all three copies of the `service.desktop` assets now
  advertise `all/allfiles;inode/directory;`, and the VirusTotal variants
  `all/allfiles;`. Previously `application/octet-stream;` hid the action for
  common file types.
- **Repair integrity:** `install_integration` now compares on-disk bytes and
  replaces stale or modified managed assets during repair instead of treating
  mere presence as success. Symlinks are never read through; `O_NOFOLLOW`
  rejects them.
- **Nautilus log hygiene:** the native and Flatpak scripts no longer write
  selected paths, raw arguments, or `PATH` to the cache log, and they report
  the launcher's exit status via `PIPESTATUS[0]` rather than `tee`'s status.
- **Legacy helper:** the invalid app ID in `scripts/install-nemo-actions.sh`
  was corrected to `io.github.linuxdefender.linuxdefender`.

### Companion issue and PR inventory

- KDE: #1 multi-file scan; #2 missing installed menu item (both 2016; reproduce on current KDE).
- GNOME: #20 COPR packaging, #19 install/menu visibility, #17 Nautilus 43 compatibility, #16 Arch packaging, #12 icon, #8 history mismatch, #4 Nautilus version warning, #3 multi-file scan, #2 translations. PR #18 remains open although its Nautilus API changes are already in default; no cherry-pick needed. Most reports concern old OS/ClamTk 5.x; verify #17 on current GNOME and address multi-file behavior in the revived CLI.
- Nemo: no open issues/PRs. Closed PR #1 corrects a German translation.
- Thunar: no open issues. Open PR #3 only adds openSUSE links to the README; confirm package availability before adopting.

## MidnightBSD packaging reference

[MidnightBSD/mports PR #1935](https://github.com/MidnightBSD/mports/pull/1935) merged 2026-10-23. It updates only `security/clamtk` port files, switching to `piposeimandi/clamtk` 6.19. The PR says that fork has four commits from 2025-07 and no later activity at review time. This is a packaging precedent, not a modern UI or code base to merge wholesale.

## Arch/AUR packaging reference

[`Estemobs/aur-clamui`](https://github.com/Estemobs/aur-clamui) was reviewed at `27193c8711ec16de34dee81b742977087a56a57b` (2026-08-29, MIT). Its `aur/PKGBUILD` targets the **old Python/GTK4 ClamUI 0.3.0** line: Python build hooks, `python-*` dependencies, GTK4/libadwaita, upstream `linx_systems` desktop/policy/icon names, and an upstream tarball SHA-256. None of that matches Linux Defender's Rust/Tauri/GTK3/WebKitGTK 4.1 application, so nothing was copied.

Disposition: **implemented independently** as `aur/PKGBUILD` plus `aur/linux-defender-privileged-helper/PKGBUILD` in this repository. They build the Rust/Tauri binaries with the frozen Bun frontend, install rebranded `io.github.linuxdefender.linuxdefender` assets, install the version-matched root-owned helper and Polkit policy separately, compile the ten gettext catalogs, and leave ClamAV and its database host-owned. Sway/wlroots support is exposed through `waybar` and `xdg-desktop-portal-wlr` `optdepends` plus tray/installation documentation; the app's SNI tray needs no Python or `libdbusmenu` binding. The recipes are **not published to the AUR** yet, and real Sway desktop validation remains open.

## Security and quality decisions

- Preserve host ClamAV/FreshClam ownership by the OS package/service. The UI should display engine version, database age, update source, and service state; OS package managers update software while FreshClam updates definitions.
- Keep detections reviewable. No bulk deletion or automatic quarantine without clear consent and recoverable restore. Preserve ClamTk's unique quarantine-name fix.
- Port a daemon backend only with adversarial path tests: long paths, CR/LF/NUL, cancellation, exclusions, exact result paths, truncated output, and threat counts.
- Keep privileged operations behind a narrowly scoped, signed/versioned helper and Polkit policy. Avoid downloading/executing helpers in-app without a separately verified trust design.
- Keep VirusTotal hash lookup/file upload separate and consent-based; keep urlscan explicit/private-first; keep YARA and Fangfrisch-style feeds opt-in and distinct from official FreshClam definitions.
- HIPS, firewall/network administration, and rootkit-removal tools are not antivirus. Security-audit results must be accurately scoped and must not imply guaranteed protection.

## Local integration progress

The public [Linux-Defender/Linux-Defender](https://github.com/Linux-Defender/Linux-Defender) repository contains the merged revival history on `main`. ClamTk behavior parity is documented in this directory; its Perl `reference/clamtk` subtree was retired on 2026-11-16. The former ClamUI revival's YARA work is ported. Several app/package/data identifiers still say ClamUI as compatibility identifiers; visible branding is Linux Defender. No Linux Defender release is published yet.

The upstream ClamUI `main` head `6836eea` is an ancestor of the selected `master` head, not a newer release. It diverges from master due later commits; the default master branch restores scanner handling/tests and current dependencies, so main was not merged separately. Continue comparing branches when upstream history changes.

ClamTk's 23 open issues and four open PR dispositions above are still the ledger; review does not equal a fix. Local verification in the unified checkout: `cargo fmt --check --all` passed; the focused platform integration suite passed (7/7 at that review; 11/11 at the 2026-11-25 recheck), including Thunar install/remove, `%F`/VirusTotal action checks, KDE MIME coverage, and repair-by-bytes coverage. The frontend TypeScript/Vite build passed after the Thunar UI type update. A full `cargo test --workspace --locked` run now passes with zero failures; the two environment-gated tests (GTK clipboard under `xvfb-run`, signed-RPM bootstrap) remain ignored by design. Previously, mocked VirusTotal tests passed (8), and translation checks passed (10 locales, 1,275 messages at that snapshot; current catalogs contain the full source message set, tracked in `docs/translations/README.md`). The actual window, tray clicks, themes, Thunar/XFCE actions, auto-update services, and CachyOS package still require desktop validation. All reviewed work has been pushed to `main`.

## Nine-repository merger review (2026-11-20)

A second sweep reviewed nine same-name or same-category GitHub repositories, plus the upstream ClamUI default branch, against this single Rust/Tauri/React runtime. None of the repositories contained a four-entry official base-database list: every scanner that enumerated ClamAV databases used `main`, `daily`, and `bytecode` (each `.cvd` or `.cld`). The earlier local 4→3 change was in the suggested third-party feed list, not in the official database set. The URLhaus suggestion was removed when the anonymous `https://urlhaus.abuse.ch/downloads/urlhaus.ndb` endpoint started returning HTTP 410; URLhaus now requires a free abuse.ch Auth-Key for its ClamAV signature export, and Linux Defender restored it as a built-in provider with a product-default key, added to the freshclam draft automatically. The Suggested button still fills only RFXN (`rfxn.hdb`, `rfxn.ndb`) and the three InterServer files; URLhaus is added automatically.

License boundary: only Herodium is MIT. Linux Defender reimplemented behaviour from the GPL and custom-licensed projects and copied no code, strings, rules, or data from them. Behaviour adoption must stay independently written and tested at the owning boundary.

| Repository | Reviewed revision | License | Disposition |
|---|---|---|---|
| [`ramnezer/herodium`](https://github.com/ramnezer/herodium) | `main` @ `5f3b8ec` | MIT | Adopt behaviour: identity-bound remediation, bounded live-scan queues, recovery walks, health model, trust-checked tool execution. No code copied yet. |
| [`demosthenesk/Linux-Defender`](https://github.com/demosthenesk/Linux-Defender) | `main` @ `9c7dac7` (v1.8.5) | GPL-2.0-or-later | Reimplement select behaviour: quarantine rescan after signature change, pause/resume updates, write-ahead scan records. Do not copy code or bundle ClamAV. |
| [`asafelobotomy/xanadOS-Search_Destroy`](https://github.com/asafelobotomy/xanadOS-Search_Destroy) | `2b91c1a4` (2026-03-23) | GPL-3.0-only | Reimplement select behaviour: three-database inventory, cache invalidation keyed on signature version, read-only firewall status. Ignore the broken watcher, placeholder web protection, and cached-root model. |
| [`seanpm2001/Linux_Defender`](https://github.com/seanpm2001/Linux_Defender) | `f5ab300b` (2025-05-26) | GPL-3.0 plus non-free extra terms | Nothing to adopt; documentation-only stub with no executable scanner. |
| [`Ellath3may0/linux-defender`](https://github.com/Ellath3may0/linux-defender) | shallow `main` snapshot | MIT declared, no LICENSE file | Reimplement read-only anti-persistence heuristics, config-integrity hashing, and `/etc/passwd`-derived account model. No destructive remediation. |
| [`VisAwesme/Linux-Defender`](https://github.com/VisAwesme/Linux-Defender) | `cd1cddc` (2025-04-13) | Custom LDPL 1 (non-free) | Ignore; dummy signature list, credential leak, destructive uninstaller. |
| [`NetKnightsClub/Linux-Defender`](https://github.com/NetKnightsClub/Linux-Defender) | `df0435d` (2025-05-12) | Custom LDPL 1 | Ignore; byte-identical mirror of the above except the README warning. |
| [`jkniazi1232/Linux-Guard`](https://github.com/jkniazi1232/Linux-Guard) | `f158825` (2024-11-28) | None | Ignore; unlicensed 50-line MD5 matcher with incorrect hashes and false positives. |
| [`TraderOutfit/Maxsecure-Antivirus-2026`](https://github.com/TraderOutfit/Maxsecure-Antivirus-2026) | repository snapshot | None | Ignore and treat as a malware-distribution lure; no code was downloaded or executed. |

### Implemented in this pass

- Official base-database inventory now reports `main`, `daily`, and `bytecode` separately from the count of custom signature families, in both the audit section and the updater database status. A missing base database is a warning/failure instead of being folded into the generic freshness check.
- Quarantine entries can be re-scanned against the current signatures from the Quarantine page. Payloads are integrity-checked first; results distinguish still detected, no longer detected (probable false positive), integrity failure, and scan error. Scanning happens in place and never copies a payload out of the vault.
- The suggested feed list adds RFXN and uses HTTPS for InterServer.
- URLhaus is restored as a built-in provider: the anonymous endpoint returns HTTP 410 Gone, and abuse.ch now requires a free abuse.ch Auth-Key. Linux Defender ships a product-default key, so every install gets the URLhaus feed automatically: `urlhaus.key_status` reports the default as configured, and the feed is added to the freshclam draft automatically when a configuration loads. Save & Apply remains the explicit write step for the draft. Preferences shows URLhaus as a provider row with no key entry or Delete control; `urlhaus.key_save` replaces the default and `urlhaus.key_delete` disables it until a new key is saved. The added feed is `https://urlhaus-api.abuse.ch/v2/files/exports/<auth-key>/urlhaus_clamav.ndb`, and the key is stored in freshclam.conf as part of the feed URL. The Suggested button still fills only RFXN (`rfxn.hdb`, `rfxn.ndb`) and the three InterServer files; URLhaus is added automatically. Regression coverage: `crates/linux-defender-core/tests/config.rs` — `urlhaus_feed_url_round_trips_as_a_custom_signature_url`; `urlhaus::tests` (feed URL shape and validation, the product default being used when nothing is saved, and `urlhaus.key_delete` disabling it).
- `clamscan` can now be invoked with non-UTF-8 quarantine payload names through an `OsString` command path.

### ClamUI + ClamTk parity gap matrix

"Parity" means a corresponding Linux Defender workflow exists; it does not claim pixel or behavior parity.

| Area | ClamUI | ClamTk (retired tree; behavior source) | Linux Defender | Gap or decision |
|---|---|---|---|---|
| Core modules | audit, audit/firewall, cli, common, config, credentials, credits, headless, host, host_probe, i18n, logs, network/public_ip, platform, portmaster, privileged, profiles, quarantine, scan_parser, scanner, scheduler, settings, threat, updater, virustotal | same set; system scanner, GTK/Qt UI, perl glue | identical core module set plus `urlhaus` (Linux Defender extension for the restored provider); `historical_summary` exists in both sources | No missing core module. |
| CLI | help, scan, quarantine <list|restore|delete>, profile, status, history, install-privileged-helper, --version | same subcommands plus quiet/autostart/syslog helpers of ClamTk style | Linux Defender CLI preserves the seven subcommands (help, scan, quarantine, profile, status, history, install-privileged-helper) and quarantined-file restore | Parity. |
| Tray | desktop tray and file-manager launchers | tray plus Nemo/Thunar/Nautilus/Send To and KDE addons | tray (`desktop/src-tauri/src/tray.rs`) and the same file-manager integrations | Parity. |
| Pages | Audit, Components, ConfigPreferences, Database, Logs, Network, Preferences, Profiles, Quarantine, Results, Scan, SettingsPreferences, Statistics | GTK screens: ClamTk, ClamTk Views, ClamTk Tray, ClamTk, ClamTk, plus update utilities | Audit, Components, ConfigPreferences, Database, Logs, Network, Overview (extra), Preferences, Profiles, Quarantine, Results, Scan, SettingsPreferences, Statistics, Urlscan (extra) | Superset; see the screen-by-screen table above for per-screen notes. |
| Suggested feeds | none | none in the suggested flow | RFXN (`rfxn.hdb`, `rfxn.ndb`) + InterServer over HTTPS by default; the URLhaus feed is enabled by default via the product-default Auth-Key (the pasted key; a user can paste their own to replace it or Delete to disable) | Linux Defender keeps the useful suggested set; ClamUI has no equivalent today, so there is no parity gap to close. |
| Online checks | virus total file scan | virus total file scan, plus ClamTk `ldconfig` style extras | virus total + urlscan, explicit consent, private default; ClamTk virus-total integration preserved | Extension, not a gap. |
| Scheduling | user systemd schedules; missed-run semantics | cron schedules; per-user mode | user systemd scheduler + per-profile targets, UI-managed schedules, documented off-machine behavior | Same capability class. |
| Audit | ClamAV health, firewall (open ports), macOS framework, automatic updates, intrusion detection, SSH hardening, Portmaster health | same audit categories | same audit categories; Linux Defender ports Permission-less `clamscan`/`freshclam` invocations | Parity. |
| Secrets and config | protected config via `/usr/bin/clamui-apply-preferences` and `PKEXEC_UID` | host ClamAV config editing | protected config via `/usr/bin/linux-defender-apply-preferences` with pre-rename helper compatibility | Parity plus name migration. |

### Deferred, with reasons

- A real-time filesystem watcher needs a bounded queue, dirty coalescing, recovery walk, ClamAV temporary-directory exclusion, and honest failed/unsupported state. That is a separate module with its own tests; shipping a watcher that cannot start would repeat xanADOS's failure.
- Scan-result caching requires an identity captured from one open descriptor plus signature and engine versions; it must never act as an extension-based skip list.
- Config-integrity hashing and anti-persistence audit rows are new capability, not part of the ClamAV database fix, and need their own target set and false-positive tests before they appear as findings.
- Update pause/resume affects our own `freshclam` child only; a frozen download holds the database lock, so it needs explicit UI states and tests.
- The shared Google Doc link was not publicly readable during this review, so no content from it is reflected here.

### Rejected outright

- Root services, `/etc/clamav` rewriting, firewall/ipset enforcement, process killing, kernel/eBPF monitors, and AppArmor level switching from Herodium.
- Bundling ClamAV or its database, as demosthenesk's AppImage does.
- XOR "encryption" for quarantine payloads and restore paths that do not re-verify identity or hash.
- `--database` directories that shadow the official set, world-writable/symlink refusal as a scanning gate, and silent success on partial database updates.
- Placeholder web protection, cached root sessions, API keys in query strings or stdout, and default-on detection uploads.

## ClamUI #370 / #371 / #368 reviewed 2026-11-26

- **Implemented:** openSUSE Tumbleweed/Leap detection (exact `ID`, so MicroOS is not misdetected), `zypper` install commands in core and the Components page, `/usr/bin` and `/bin` fallback in `host_binary`, and the #368 access-control fix (`getenforce` via `host_binary`, no false AppArmor warning with active SELinux). Regression tests cover the new behavior.
- **Deferred:** the `os-update.timer` automatic-updates audit rows and the `/run/reboot-needed` reboot flag from #370; adding them requires new gettext IDs and audit-row tests, and the timer is specific to openSUSE's transactional update tooling. Revisit with dedicated tests before adopting.
- **Deferred:** FUSE-mounted file streaming and pathless clamd error attribution (#369, open upstream PR #372), and the bounded in-memory result store for very large scans (same PR). These change scan execution and result ownership; a blind port would risk scan correctness regressions.

## Upstream sweep 2026-11-27 (reviewed pin c4852cf)

- **Implemented:** PR #372's pathless clamd error attribution (`fd[N]: ... ERROR` / `stream: ... ERROR` now rewritten to the scanned path; `crates/linux-defender-core/src/scan_parser.rs`) and its bounded in-memory/latest-result handoff (`desktop/src/resultStore.ts`, wired into Scan and Results) were ported as narrow, independently tested changes. PR #371's `which`-missing fallback is now genuinely reachable (`host.rs`: `which_host_binary` no longer short-circuits `host_binary`; `fallback_binary_paths` covers `/usr/sbin`, `/sbin`, `/usr/bin`, `/bin`). PR #370's openSUSE install guidance is in `installation.md` and `reference/scan-backends.md`, guarded by `check-host-tool-guidance.py`.
- **Implemented (2026-11-27 later pass):** PR #372's FUSE `statfs`/`--stream` routing, adapted to our scanner with an injected `FuseDetector` probe, per-device caching, a separate `--stream` phase, and unit tests; error attribution was already present. OpenSUSE `os-update.timer` audit rows and `/run/reboot-needed` remain deferred. Website TypeScript 7.0.2 (PR #299) was re-tested and hard-rejected: `astro check` refuses TS7 unconditionally and all `@volar/*` peers require `<7`.
- **No action:** PR #373 (12 cargo bumps), #354 (superseded), #356 (rusqlite 0.43.0), #355 (zbus 6.5.0 local, ahead of 6.3.0), #352/#353 (desktop/website bun groups) are all satisfied locally at equal or higher versions; reported drift is gone after pinning `c4852cf`. Issues #306 (upstream freshclam owns custom-URL ordering; our troubleshooting page documents the 410 behavior), #361/#315 (unconfirmed blank-window root cause), #285/#264/#263 (already covered) need no change. PR #366's extra blank-window permissions remain intentionally unported; our watchdog and error boundary cover the user-visible behavior.
- **Access limits:** upstream Security endpoints return 404 with this read-only token, discussions are disabled, and the wiki does not exist. Releases/assets add nothing; no aarch64 AppImage. The only upstream workflow deliberately not ported remains `packages.yml`.

### PR #366 native startup diagnostics (implemented subset)
Upstream PR #366's bounded native milestone timeline, main-thread probe, and three-way verdict are implemented in `desktop/src-tauri/src/startup_trace.rs` and wired in `runtime.rs`. The `CLAMUI_STARTUP_TRACE=1` stderr echo and the extra `frontend_ready`/`frontend_report` IPC commands are omitted: no new command or capability is needed for the existing `app.startup_ready` signal and React error boundary. The pre-React fallback is now the CSP-safe classic script `desktop/public/boot-diagnostics.js` plus a hidden placeholder in `desktop/index.html`, which reports resource/script errors or an 8-second stall without network access or new IPC. `scripts/inspect-blank-window.py` is the adapted read-only local probe; it warns that the inspector itself can freeze startup and must be cross-checked with a no-inspector run.

### Upstream PR #374 / commit 3960c74 (merged 2026-11-27)
Ported the two behavioral refinements to the #368 access-control fix: a SELinux mode is now trusted only when `getenforce` exits 0, and a `disabled` SELinux row is skipped when AppArmor is already enabled (only one major LSM is active). The upstream split of probing from decision and its catalog churn are diagnostic/testing structure only; local audit tests already cover the parsers. The reviewed pin later moved to `6bfc4d5` (final sweep, all PRs closed); freshness check is green.

### ClamAV alternative-tool sweep (2026-11-27)

Sources reviewed: `https://cybersectools.com/alternatives/clamav` (34 commercial EPP products), `https://www.reddit.com/r/linuxmint/comments/1qc1bof/clamtkclamav_alternatives/` (19 comments), and `https://linuxsecurity.expert/tools/clamav/alternatives/` (full open-source list and licenses).

- **Adopted:** rkhunter (GPLv3 host binary, invoked only through the existing explicit `pkexec` deep-scan path; no code vendored) as a third deep scan alongside Lynis and chkrootkit, combined into one "Run all security scans" action.
- **Already satisfied:** chkrootkit (existing deep scan), YARA (local `.yar`/`.yara` rules through ClamAV), LMD/RFXN signatures (`rfxn.hdb`/`rfxn.ndb` suggested feeds), PHP web-shell coverage (InterServer `shell.ldb`), and safe-browsing/firewall guidance in the docs.
- **Documented/deferred:** Malscan (old, web-server focused; automatic feed fetching would violate the explicit-apply boundary), hBlock/Maltrail (network/hosts-level, different category), MultiScanner/Malice/Maltrail/SSMA/Loki/Dagda/BANG/Cuckoo/Mal Tindex/YaraGuardian/yarGen/Viper/bingrep/uitkyk (analyst/lab tools, sandboxes, or rule generators — out of category for a desktop frontend and some require daemons), yarGen/YARA library and ClamAV bytecode compiler (reference-only to avoid vendoring), and commercial EPP/AV (ESET, Microsoft Defender, McAfee, Bitdefender, Avast, Avira, etc.; proprietary licences, cloud submission, and multi-engine conflict with the host-ClamAV boundary).
- **Rejected outright:** EvilAbigail, WeBaCoo, sshLooter, Diamorphine (offensive/attack or rootkit samples), and USB kill switches — no place in a protective desktop scanner.
- The Reddit thread also confirmed ClamAV itself is still maintained and that ClamTk was the retired component; occasional scanning of Windows email attachments remains a valid host-ClamAV use case.

### Upstream ClamUI issue #306 (failed custom database URL)
Cannot change host freshclam's ordering — the host owns its `DatabaseCustomURL` sequence. We close the reporting gap instead: `updater.rs` extracts the host and final file name from "Update failed for custom database URL" and shows a translated message naming them, warning that later custom databases may not have been attempted. The key-bearing path component is discarded, so no Auth-Key is leaked.

### Upstream PR #299 (website TypeScript 7.0.2) — hard reject, revalidated 2026-11-27
Tested in a temporary copy: `bun install` succeeds (bun does not enforce peer ranges) and `astro build` passes, but `bun run check` (`astro check`) exits 1 with "astro check does not currently support TypeScript 7.0" — a hard runtime version guard, not a fixable type error. `@astrojs/check@0.9.12` declares `typescript: ^5 || ^6` and all four `@volar/*@2.4.31` packages declare `<7`; the documented TS-7 migration path (`@astrojs/ts-content-mapper`, TS 7.1+) is not published. Local website stays on TypeScript 6.0.3; the deferral is evidence-based.

### Deferred items resolved in the 2026-11-27 closing pass
- **FUSE `--stream` scanning:** implemented with pure, injectable helpers and tests (no real mount needed).
- **Upstream PR #366 milestone tracing:** implemented as a native-only `startup_trace.rs` with bounded milestones, first-IPC markers, and a three-way watchdog verdict (setup unfinished / main thread blocked / page never mounted). No new command, capability, or permission; the boot diagnostic is a CSP-safe classic script only.
- **Issue #306:** failed custom database reporting now names the host and final file name of the failing URL, with the key-bearing path discarded; host freshclam ordering is unchanged.
- **Translation review:** 64 more msgids adopted from pre-Rust MIT ClamUI catalogs (8 error strings × 8 locales, source `d665e49`). All remaining English-identical strings are new with no upstream source.
- **Website TypeScript 7:** hard-rejected with exact `astro check`/peer evidence; local stays on 6.0.3.
- **Recurring CodeQL `js/unused-local-variable`:** fixed at the source via `noUnusedLocals`/`noUnusedParameters` in all three TypeScript projects plus a fail-closed guard checker.

### Packaging corrective pass (2026-11-27)
- Fixed: Flatpak README now points at the real integration asset directory; the unreferenced duplicate `flathub/*.desktop` was removed; all six formats now ship the MIT `LICENSE`; Debian no longer stages a build-only signing key; the Debian app `Recommends` (rather than hard-depends on) the optional version-matched helper; the RPM helper ships `%license`; and the AUR optional helper is version-pinned. New `check-packaging-license.py` guard enforces these.
- Deferred with reason: `Replaces`/`Conflicts`/`Obsoletes` metadata for pre-rename `clamui*` **packages**. The compatibility contracts preserved here are executables, paths, logs, cron markers, and helper protocol; the old package names belong to a separate upstream product. Declaring package-level conflicts could remove an unrelated installed ClamUI without the user's consent, and no Linux Defender package has been published yet, so there is no same-project upgrade path to repair.
- Release artifacts: `release.yml` attaches DEB, RPM, and AppImage builds. Flatpak and Snap are built by their own tag-triggered workflows and by `Build All Packages`, but are not attached to the draft release because there is no Flatpak remote or Snap Store publication yet. This distribution path is stated in the release notes rather than pretending an unpublished bundle is a release asset.

### Agent-sweep deferrals (2026-11-27)
- Upstream audit acknowledge/revoke buttons and "essentials only" overview (PRs #338/#323): the Rust core already implements `acknowledgements`, `essential`, and status logic, but the frontend types/UI do not expose them. Deferred pending a dedicated UI design; recorded here so the earlier "covered" claim is no longer overstated.
- Path-list Move up/Move down UI (PR #345): `moveEntry` exists in `desktop/src/pathList.ts` but is not wired into the editor. Deferred with the reorder UI.
- Newline/CR filenames sent over clamd stdin are line-delimited; no NUL-safe transport exists without a protocol change. These are skipped/reported rather than silently mis-scanned where detected, and the limitation is documented.

## Fine-comb sweep deferrals (2026-11-28, reviewed at `58c6a683`)

The 23-agent read-only fleet found no new upstream behavior to port (all ten
pinned heads match; ClamUI has zero open PRs). The following local residuals
were reviewed and deliberately deferred with reasons; none is a regression:

- **Non-UTF-8 clamscan argv** (`scanner.rs:1227`): the daemon backend already
  preserves raw bytes; changing the clamscan backend to `OsString` plumbing
  touches command execution end-to-end and needs dedicated byte-level tests.
- **VirusTotal in-flight cancellation** (`virustotal.rs:507-569`): requires a
  transport API change to abort a blocking read; polling, folder loops and
  sleeps already honor cancellation.
- **systemd/cron directory ownership hardening** (`scheduler.rs:316-334`):
  host-specific permission semantics; needs per-distro verification before a
  fail-closed rule can be enforced safely.
- **`open_path` check/use TOCTOU and tray readiness timing**: both need a real
  desktop reproduction; the native helper still re-validates destinations.
- **SNI profile label sanitization** (`tray.rs:332-355`): labels come from
  persisted profiles; a sanitizer needs the same normalization as persistence.
- **DEB ELF-architecture verification and post-build metadata assertion**:
  the RPM builder already does this; porting it to both DEB builders needs
  cross-arch CI runs before it can be trusted.
- **Release preflight `verify-tag` job**: tag/ref validation already runs in
  the final release job; moving it earlier changes a human-only workflow and
  is deferred until a release is actually prepared.
- **Latent checker blind spots** (`check-ipc-operations.py` whole-module scan,
  `check-cross-layer.py` hardcoded CLI names, `check-dead-files.py` bare-name
  matches, `support-parity-contracts.json` union-mode sanitization): tightening
  these regexes can create false failures on valid historical references; each
  needs a staged rollout with its own negative tests.
- **Imported-skill payload wording**: `.agents/skills` payloads are hash-locked;
  changing a line requires a reviewed upstream diff and both hashes in
  `skills-lock.json`, not an incidental edit.

## Fine-comb fleet waves 1-5 residual deferrals (2026-11-28)

Reviewed at `ca283909` with 50+ read-only agents across every layer. These residuals are real but deliberately deferred with reasons; none is a regression and all are guarded or documented so they cannot be forgotten:

- **Host command joined-reader hang** (`host.rs:93`, `audit.rs:259`): a descendant inheriting stdout after the direct child exits can block `join()` past the deadline. No current caller backgrounds such a child; fixing needs process-group kill plus nonblocking bounded reads in both helpers.
- **Crontab UTF-8 rewrite** (`scheduler.rs:435-499`): a lossy round-trip could alter unrelated non-UTF-8 entries. Needs byte-preserving rewrite or an explicit refusal path and a multi-distro crontab test.
- **Profile storage invalid-shape backup / invalid entry drops** (`profiles.rs:446-477`): valid JSON with a bad shape or one invalid entry is overwritten without backup. Needs a normalization/backup contract like `settings.rs` plus compatibility tests.
- **Config save validates untouched directives** (`config.rs:727`): a pre-existing invalid value blocks an unrelated save. Needs a split between submitted-key validation and merged-document cross-key invariants.
- **Legacy migration symlinks and aside-name cap** (`common.rs:170-228`): symlinked entries are followed and only five `.migrated-N` candidates are tried. Needs a preflight rejection of symlinks and an unbounded unique-name loop.
- **Scheduler cancellation during auto-quarantine** (`scheduler.rs:1117-1153`): cancellation is checked after the scan but not inside the per-threat loop. Needs a prompt `Ok(130)` per iteration with rollback-safe state.
- **Release tag preflight** (`release.yml:19-47`): tag/ref validation still runs in the final job after signed builds. Moving it earlier changes a human-only workflow and is deferred until a release is prepared.

Fixed in these waves (not deferred): MCP endpoint/path/mode, gettext plural and dynamic literals, scheduler launcher injection and dual-backend cleanup guard, quarantine overflow/fsync/name validation, CLI argv/flag/nested-action/path sanitization, Debian helper key embedding, AppImage squashfs permissions (upstream PR #378), VT stats fail-open, scanner id/output/history/stdin, rkhunter warning parsing, bounded CVD header, host probe sanitization, frontend races and IPC validation, fail-open gates, audit launch buttons, and six-format docs.
