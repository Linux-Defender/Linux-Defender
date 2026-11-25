# Linux Defender contributor guide

Linux Defender is a Linux desktop frontend for **host-installed ClamAV**. Its Rust/Tauri/React source incorporates an MIT-licensed upstream foundation. The Linux Defender product name is the only user-facing brand. Retain original contributor notices and historical upstream references where required, and retain old command, data, helper, and secret-service identifiers only as compatibility contracts until their migration has dedicated tests. The production application is Rust: a headless core, a Tauri 2 native runtime, and a React/TypeScript frontend.

The public desktop, AppStream, and Flatpak identity is `io.github.linuxdefender.linuxdefender`; Tauri's private bundle identifier is `io.github.linuxdefender.linuxdefender`. Do not substitute one for the other in public identity assets.

## Mandatory enforcement (read first)

Every AI model and contributor must follow [`AI-ENFORCEMENT.md`](AI-ENFORCEMENT.md), the canonical rules file with skill-style frontmatter. This repository is **tool-agnostic**: the universal enforcement path is this `AGENTS.md`, the git hooks, and CI — it works the same in Claude Code, OpenCode, Codex, Aider, Cursor, Continue, Zed, or any other assistant. Tool-specific adapters only *add* convenience; they never replace the universal checks. Rules are never copied into a plugin or hook. Before declaring any task done, run **`bash scripts/check-all.sh`** and fix every failure; for full verification run `bash scripts/audit-consistency.sh`. These are not optional: the same checks run in the pre-commit and pre-push hooks and in `Consistency Audit` CI. Cross-cutting features must be declared in `scripts/cross-layer-contracts.json` and wired in every consuming layer; dead links, dead files, stale docs/skills/site, version/identity drift, stale signature databases, and un-wired modules fail the check automatically. `scripts/check-repo-consistency.py` verifies versions and the app id agree across the workspace, Tauri crate, desktop package, AppStream metadata, and Flatpak release notes, and that every workflow and maintenance script is referenced. `scripts/check-signatures.py` verifies the host ClamAV database is current and detects EICAR; `scripts/check-signature-feeds.py` verifies the product-default URLhaus export with the Auth-Key redacted. The host engine and signature database are never bundled by any package format.

## Security first

Security takes precedence over convenience, performance, and package size.

- **Least privilege:** define explicit capabilities in `desktop/src-tauri/capabilities/` for each window or webview and select them in `tauri.conf.json`. Grant only required permissions; do not use broad default permission sets or wildcard grants.
- **CSP and navigation:** keep a restrictive CSP in `desktop/src-tauri/tauri.conf.json`, with `script-src`, `connect-src`, and other directives limited to required sources. Avoid `unsafe-inline` and `unsafe-eval`; reject untrusted webview/window navigation.
- **IPC trust boundary:** treat all frontend arguments as untrusted. Validate every argument in Rust before dispatch or side effects, including operation IDs, paths, URLs, and value bounds; sanitize untrusted text before display or logging. Frontend checks are not authorization.
- **Scoped native access:** scope filesystem, shell, and network plugin permissions narrowly. Custom commands must enforce their own allowlists and operation ownership. Keep native opening, exports, clipboard actions, and external URLs tied to explicit user requests; prefer maintained, scoped Tauri plugins where they fit the existing core and privileged-helper boundaries.
- **Isolation:** prefer Tauri's isolation pattern when frontend dependencies expand the attack surface; it supplements rather than replaces Rust-side validation and capability restrictions.

## Native commands and state

- Expose IPC handlers with `#[tauri::command]` and register them only through `tauri::generate_handler!`. Return `Result<T, E>` with serializable errors; use `thiserror` for structured Rust errors and expose only sanitized frontend details.
- Use `async fn` for I/O-bound handlers; offload blocking core scans, SQLite operations, and process work rather than blocking the UI or async executor. Preserve the headless core boundary.
- Manage shared runtime state through `tauri::State`, with `Arc` and `Mutex`/`RwLock` where needed. Prefer `tokio::sync` primitives for asynchronous contention; never hold blocking lock guards across `.await`.
- Keep implementation details private or `pub(crate)`; export only APIs required across crate boundaries.

## Architecture and boundaries

| Area | Responsibility |
| --- | --- |
| `crates/linux-defender-core/` | Headless domain operations, XDG persistence, ClamAV host integration, scheduling, quarantine, i18n, and the privileged-helper protocol. It has no Tauri or widget dependency. |
| `desktop/src-tauri/` | Tauri commands, event bridge, native dialogs, single-instance handling, lifecycle, safe opening/export helpers, and the Rust SNI/DBusMenu tray. |
| `desktop/src/` | React pages, navigation, rendered translations, notifications, and the typed frontend API. |
| `data/` | Application identity, AppStream metadata, desktop integration, and icons. |
| `debian/`, `flathub/`, `appimage/` | Distribution-specific packaging; keep the same app identity and host-ClamAV boundary in every format. |
| `website/` | The published Astro/Starlight documentation site. |

The frontend has one request path to the native runtime; the runtime forwards only allowlisted operations to the core. Core events currently use `{ event, data }` on the channel `linux-defender-event` (the old `clamui-event` name is retired). Do not add arbitrary frontend filesystem, shell, process, remote-navigation, or generic IPC access. Keep slow work off the UI thread and scope cancellation to its operation ID.

The Rust core and desktop are the only application implementation. Make behavior changes in their owned source boundaries and preserve the established core-to-runtime-to-frontend contract.

## Upstream parity maintenance

When reviewing or adopting work from ClamTk, Lenspect, or another related scanner, keep the parity matrix in `docs/revival/RELATED-PROJECT-REVIEW.md` current. Record the upstream repository, reviewed default-branch commit/date, issue or PR identifiers, and whether each behavior is implemented, intentionally deferred, or still open. Review issue reports and PR diffs independently; a merged upstream PR is not proof that the behavior exists here. Port behavior into this single Rust/Tauri/React runtime and add a regression test at the owning boundary. Check privacy, network disclosure, credentials, file and URL limits, cancellation, accessibility, localization, platform compatibility, and license obligations before adoption. Do not copy GPL-licensed Lenspect code into this MIT-licensed project without an explicit licensing decision; behavior can be independently implemented and tested. Re-run the parity review when changing a related integration and before release.

The authoritative fork status — what was ported from upstream ClamUI, what is deliberately deferred (scanner concurrency, full Flush UI), and what is superseded (Dashboard/ScanOverview/scanHistory) — lives in [`docs/clamui-fork/STATUS.md`](docs/clamui-fork/STATUS.md). Keep it current when porting. Compatibility identifiers (`clamui-apply-preferences`, `~/.config/clamui`, `clamui.log*`, cron markers, Nautilus fallbacks) are retained with dedicated tests; do not "rebrand" them away.

The generated [documentation map](docs/DOC-MAP.md) links every tracked Markdown/MDX document, and `scripts/generate-doc-map.py --check` enforces it on every commit. Run `python3 scripts/generate-doc-map.py` after adding or removing a doc.

The [revival research index](docs/revival/README.md) is the entry point for all related-project work: the link-checked [upstream repository inventory](docs/revival/UPSTREAM-REPOSITORIES.md) (ClamUI, ClamTk, Lenspect), the parity matrix, the ClamTk and Lenspect reviews, and the rebrand records. Keep the inventory's URLs current; `scripts/check-upstream-urls.py` verifies them on every commit, and `scripts/check-external-links.py` verifies every external link in all tracked documentation in the full audit and in the weekly `Doc Links` workflow. Reviewed upstream heads for ClamUI and Lenspect are pinned in `parity-lock.json` and watched by the weekly `Upstream Freshness` workflow.

The consolidated [revival-chat requirement ledger](docs/revival/CHAT-AND-PROJECT-AUDIT.md) records every request from the whole conversation, where it is satisfied, and which check re-verifies it. Keep it current when new requests arrive.

For a full parity/consistency/dead-code/stale-reference audit, use the `linux-defender-parity` skill and run [`scripts/audit-consistency.sh`](scripts/audit-consistency.sh) (also run weekly in the Consistency Audit CI workflow). For integration work (file-manager actions, tray, host ClamAV, safe open/export/clipboard, online services, scheduling), use the `linux-defender-integrations` skill.

## Consistency, staleness, and dead code

Before declaring any port or refactor done, run `bash scripts/audit-consistency.sh` (or use the `linux-defender-parity` skill). It checks:

- **Cross-file consistency:** verify the Rust core, Tauri runtime, frontend API types, translations, docs, packaging manifests, and CI workflows agree. A new IPC field must exist in `StartupState`, the Rust `StartupState`, and any event payloads; a new UI string must be in the POT and all 10 catalogs.
- **Dead code:** a ported module must either be wired to a caller or removed/superseded. Check with `grep -rl "<module>" desktop/src --include=*.ts --include=*.tsx | grep -v "/<module>."` for frontend modules and `cargo clippy -- -D warnings` (which flags unused Rust items) for the core. Document any intentional non-use in `docs/clamui-fork/STATUS.md`.
- **Stale references:** `grep -rniE 'clamui\.com|linx.systems|clamui@|rooki\.xyz|io\.github\.linx'` in live files must return only intentional historical/compat references (docs/revival, CHANGELOG, LICENSE, upstream fork docs). Fix anything else.
- **Generated files:** never hand-edit `po/*.mo`, `desktop/dist/`, `website/public/` generated assets, or `desktop/src-tauri/gen/`. Refresh the POT with `./scripts/update-pot.sh` and merge catalogs with `msgmerge`, then verify with `msgfmt -c` and `msgcmp`.
- **Wiring and modes:** `scripts/check-gate-wiring.py` fails on a checker no gate runs or a gate pointing at a missing script; `scripts/check-file-modes.py` fails when a shebang script or Debian maintainer script loses its executable bit; `scripts/check-source-invariants.py` fails if the URLhaus draft is auto-applied, the retired `clamui-event` channel returns, or the Tauri CSP loosens.
- **CI parity:** before pushing, make sure the full workflow set is green (builds for every package format, Test, Lint, CodeQL, Dependency Audit, Translations, Website). A failure on HEAD is not acceptable even if the code "looks fine" locally.

## Build and test entry points

Toolchain manifests are the source of truth. Work on one file or one small function at a time; after every Rust edit run `cargo check`, after every TypeScript/Astro edit run `bun run --cwd desktop check` (or `npm run build`/`npx tsc --noEmit` where appropriate). Fix any compiler error or warning immediately and re-run until clean before replying to the user. Typical local commands are:

```bash
cargo test --workspace --locked
cargo fmt --check --all
( cd desktop && bun install --frozen-lockfile )
bun run --cwd desktop check
bun run --cwd desktop build
cargo clippy --workspace --all-targets --locked -- -D warnings
bun run --cwd desktop tauri dev
cargo run -p linux-defender-core --bin linux-defender-cli -- help

```

`cargo clippy` compiles the production Tauri crate, whose `generate_context!` embeds `desktop/dist`; run the frozen frontend install and build first.

Rust core tests live under `crates/linux-defender-core/tests/` alongside module-local tests. Add focused consumer-visible, data-compatibility, or security invariants beside the owning module; avoid implementation-text or mock-only tests.

Tests are necessary but not sufficient: also exercise the real app on this host when verifying behavior. Run the headless CLI (`./target/debug/linux-defender-cli status --json`, `history`, and an EICAR `scan`), check the local debug log at `~/.local/share/linux-defender/debug/linux-defender.log` and `~/.local/share/linux-defender/logs/`, and confirm the Tauri build starts (CI covers the full GUI build on the Ubuntu 22.04 baseline). A green unit suite does not prove the host ClamAV bridge, helper, or tray work.

For website changes, do the same: `bun run --cwd website check/build`, run `bun run --cwd website dev` (or `preview`) and load the home page plus at least one docs page in a browser with no console errors, and run a Lighthouse audit on the **production preview** (the dev toolbar adds a "Learn more" link that fails the SEO link-text check and is not part of the site). `scripts/audit-consistency.sh` verifies website build/links/sidebar targets/unused components.

For gettext changes, validate extraction and catalogs with:

```bash
./scripts/update-pot.sh --check
./scripts/check-potfiles.sh
./scripts/check-translations.sh
```


The website is a separate Bun project:

```bash
cd website
bun install --frozen-lockfile
bun run check
bun run build
```

CI builds native artifacts on the Ubuntu 22.04-compatible baseline. A build on a newer host does not establish that compatibility.

## Release builds and dependency hygiene

- Configure release profile settings in the workspace `Cargo.toml` for size (`lto`, reduced `codegen-units`, optimized `opt-level`, `panic = "abort"`, `strip`). Check scan responsiveness and failure handling under the release profile before shipping.
- Keep the system WebKitGTK WebView; do not bundle a browser runtime. Keep Tauri, Rust dependencies, and frontend packages current through the repository's locked dependency workflows. Run `cargo audit` and `bun audit` when updating dependencies and address relevant advisories.

## Coding-agent skills

Project-local coding-agent skills are optional development aids, not build or runtime dependencies. Their canonical imports are in `.agents/skills`; `.claude/skills` provides compatibility links. For installation details, see the [Development guide](website/src/content/docs/docs/contributing/development.md).

Three skills (`accessibility`, `rust-best-practices`, `vercel-react-best-practices`) are imported from upstream and locally adapted with Linux Defender enforcement rules. `skills-lock.json` records the source, selected path, reviewed upstream hash (`upstreamHash`), enforced local payload hash (`computedHash`), and review date — not a commit. Refresh only a deliberately selected upstream skill: review the diff, update the payload, and refresh both hashes/date in the same change. The `linux-defender-*` skills are maintained locally in this repo and are not in the lock file. `scripts/check-all.sh` verifies imported skills still match their locked hashes AND that every skill is named in this file, `CLAUDE.md`, or the development guide (so no skill is forgotten).

- AI rules: use the thin `linux-defender-enforcement` skill, which points to `AI-ENFORCEMENT.md` — it is a rules file with skill-style frontmatter, not a separate copy of the rules. An optional Claude Code plugin package at `.claude/plugins/linux-defender-enforcement/` bundles a pointer skill, `/capture-app` command, and an enforcement-reviewer agent; it declares no hooks, so it never duplicates the always-on settings hooks. Validate it with `claude plugin validate .claude/plugins/linux-defender-enforcement`.

**Universal baseline (all tools):** install the git hooks with `./scripts/hooks/install-hooks.sh` so pre-commit and pre-push enforce the same checks for every contributor and model regardless of assistant; CI repeats them for every push/PR. `AGENTS.md` and `AI-ENFORCEMENT.md` are the tool-neutral instructions any assistant can read.

**Optional adapters (no tool is privileged):**

- **Claude Code:** `.claude/settings.json` injects the rules at `SessionStart`, re-reminds on `UserPromptSubmit`, and runs `check-all.sh` on `Stop`. The optional plugin package and `.claude/skills` links add a pointer skill, command, and reviewer agent; no rules are copied.
- **Aider:** `.aider.conf.yml` reads `AGENTS.md` and `AI-ENFORCEMENT.md` into every chat.
- **OpenCode:** rules are loaded as instructions and via a configured adapter that reads the canonical file at runtime; this is one adapter among several.
- **Other AGENTS.md readers** (Cursor, Continue, Zed, Windsurf, etc.): the universal baseline above applies directly.

A local MCP server in `mcp/linux-defender-assist/` exposes read-only/proposal tools for translation review, desktop capture, tray/helper probing, and online-service preflight; it never invokes `pkexec`, writes catalogs, or submits data externally.

Tool-independent checks also run automatically: `Upstream Freshness` (`scripts/check-upstream-freshness.py`) opens a review issue when an imported skill drifts; `scripts/check-packaging-consistency.py` verifies all six formats (DEB, RPM, AppImage, Flatpak, Snap, AUR) in every commit; `Packaging Sync` (`packaging-sync.yml`) checks the same plus reviewed packaging references in `packaging-lock.json` weekly; dependency auto-refresh is handled by `dependabot-refresh.yml`; `scripts/check-build-wiring.py` verifies the documented `bun run --cwd desktop tauri dev` path end to end (Vite port 1420, frontend dist, frozen lockfile, patched vendored glib); and `cargo machete` catches unused Rust dependencies. None of these depend on which assistant you use.

- Rust changes: use `rust-best-practices`.
- React client changes: use `vercel-react-best-practices`; apply it to `desktop/src/`, not Next.js or server patterns.
- Accessibility work: use `accessibility`, then validate the actual Tauri/WebKitGTK desktop rather than relying only on browser scores.
- Gettext messages, catalogs, plural forms, translator notes, or extraction: use `linux-defender-gettext` and the translation guide it points to.
- Porting/parity, cross-file consistency, dead code, stale branding, or "is everything synced": use `linux-defender-parity` and run `bash scripts/check-all.sh`, then `bash scripts/audit-consistency.sh`.
- Integrations (file-manager actions, tray/D-Bus, host ClamAV, privileged helper, safe open/export/clipboard, VirusTotal/urlscan, scheduling): use `linux-defender-integrations`.
- Globally managed IPC and release skills remain optional; contributors do not need them to work on Linux Defender.

## Runtime, data, and security rules

- **Host ClamAV:** every package format uses the host `clamscan` and `freshclam`; daemon scanning additionally needs host `clamd` and `clamdscan`. Flatpak reaches host tools through `flatpak-spawn --host`. Never bundle or substitute the engine or its definition database.
- **Durable data:** retain the existing XDG JSON and SQLite layouts, including settings, profiles, logs, quarantine records/payloads, debug logs, and scheduler-owned system state. Writes must be atomic where the existing contract requires it; preserve unknown settings and existing migration behavior.
- **Privileges:** protected host configuration goes only through `/usr/bin/linux-defender-apply-preferences`, its polkit policy, destination allowlists, and `PKEXEC_UID` checks. A pre-rename `/usr/bin/clamui-apply-preferences` stays accepted under the identical root-owned, immutable-import trust checks until the helper package replaces it. Maintain protocol-v4 compatibility with a trusted installed helper during upgrades. Do not weaken the boundary or bootstrap trust.
- **Secrets and untrusted input:** keep VirusTotal keys out of settings payloads, errors, events, and logs; use the established keyring contract. Sanitize external process text before persistence or presentation. Keep quarantine file operations no-follow, integrity-checked, and rollback-safe.
- **Tauri:** preserve the strict CSP, reject untrusted webview/window navigation, and use native helpers only for explicit user-requested paths, exports, clipboard actions, and approved external URLs.

## User-facing compatibility

Preserve all seven `linux-defender` CLI subcommands, their flags, output schemas, stream destinations, and exit behavior. `linux-defender --help` and every CLI route must stay headless; `linux-defender-scheduled-scan` and `linux-defender-apply-preferences` are native entry points with their established contracts. The pre-rename `clamui*` executable names remain accepted as compatibility aliases, and existing `~/.config/clamui`/`~/.local/share/clamui` data stays readable through its migration path.

Reuse existing gettext message IDs and plural behavior from `po/`/`po/LINGUAS`; active locales are `de`, `en`, `es`, `fr`, `hu`, `it`, `nb`, `pt_BR`, `vi`, and `zh_CN`. All user-facing gettext calls need static literal arguments: choose conditional translated branches outside helpers, then interpolate after translation or plural selection. Use the existing plural API, never new `file(s)`-style pseudo-plurals. Write `—` (prose break), `–` (range), and `…` directly; do not use ASCII ` - ` or `--` as prose separators. For a literal containing a dash, range, quotation, markup, or quoted UI label/command/key/package/file literal, put a `// Translators:` comment immediately above that literal argument—not above a lone call opener. State whether a quoted UI label must match its label translation or whether a protected literal stays unchanged. See the [translation guide](website/src/content/docs/docs/contributing/translating.md) for translator conventions. Do not add a Python runtime requirement to build or load catalogs.

## Packaging and documentation

Keep Flatpak builds for x86_64 and aarch64 on GNOME 51, the x86_64 AppImage, and architecture-specific Debian application and privileged-helper packages. Native Tauri packages require the system GTK 3 and WebKitGTK 4.1 runtime. Debian application and helper packages must have matching version and architecture. Use checked-in package scripts and manifests rather than copying packaging logic.

Published documentation lives in `website/src/content/docs/docs/`. Start with:

- [Installation](website/src/content/docs/docs/installation.md) for runtime and package requirements.
- [Development](website/src/content/docs/docs/contributing/development.md) for source, validation, and packaging workflows.
- [Architecture](website/src/content/docs/docs/contributing/architecture.md) for IPC, tray, and native-runtime boundaries.
- [Configuration](website/src/content/docs/docs/reference/configuration.md) for persistent data and privileged host settings.
- [Troubleshooting](website/src/content/docs/docs/troubleshooting.md) for user-facing recovery guidance.

The visual identity is documented in [`docs/DESIGN.md`](docs/DESIGN.md): Guardian color
tokens, typography, component rules, and the brand-asset regeneration steps shared by
the app and the website.

Use repository-page `/Linux-Defender/docs/.../` links in website content (the site `base` is `/Linux-Defender`). Keep root discoverability files concise, release content sourced from `CHANGELOG.md` and `RELEASE_NOTES.md`, and generated `website/public/` assets untouched.
