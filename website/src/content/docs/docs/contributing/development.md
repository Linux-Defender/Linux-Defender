---
title: Development and packaging
description: Build and validate the Linux Defender Rust core, Tauri desktop, packages, tests, and website.
---

## Prerequisites

Linux Defender 0.6.0 is a development snapshot built on the upstream v0.6.0 source baseline. It has a headless Rust core (`crates/linux-defender-core`) and a Tauri 2 desktop (`desktop/src-tauri`) with a React/TypeScript frontend (`desktop/`). The desktop needs the Linux WebKitGTK **4.1** API and GTK 3 development libraries. Python is not an application build or runtime dependency. Linux Defender packages are not yet published.

### Debian or Ubuntu

```bash
sudo apt update
sudo apt install build-essential pkg-config libssl-dev libgtk-3-dev \
  libwebkit2gtk-4.1-dev librsvg2-dev libxdo-dev curl wget file \
  flatpak-builder
```

Install current stable Rust with `rustup` and Bun using your distribution package manager or their official installers. Confirm the tools before continuing:

```bash
rustc --version
cargo --version
bun --version
```

The Flatpak recipes use the GNOME Platform/SDK 51 and build for the host's native Flatpak architecture (`x86_64` or `aarch64`). Add Flathub and install the SDK plus the extensions into the explicit user installation before a local build:

```bash
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user --arch="$(flatpak --default-arch)" flathub \
  org.gnome.Sdk//51 \
  org.freedesktop.Sdk.Extension.node24//26.08 \
  org.freedesktop.Sdk.Extension.rust-stable//26.08
```

Clone the Linux-Defender repository and switch to `main`, the single development and release branch:

```bash
git clone https://github.com/Linux-Defender/Linux-Defender.git
cd Linux-Defender
git switch main
```

The inherited native package workflows use an Ubuntu 22.04-compatible baseline to retain the intended glibc floor. Linux Defender's modified packages still need clean builds and installation tests before any distribution claim; a local build on a newer distribution does **not** establish compatibility with Ubuntu 22.04 or older hosts.

`scripts/check-build-wiring.py` verifies this whole dev path in the static checks: `tauri.conf.json` must invoke the desktop Vite server on the pinned `127.0.0.1:1420`, `desktop/bun.lock` must exist for the frozen install, and the patched `vendor/glib-0.18.5` crate must stay wired through `[patch.crates-io]` with its soundness fix intact. `cargo machete` also runs there so unused Rust dependencies (declared but never used by any crate) fail the check.

`cargo check` may print warnings from `vendor/glib-0.18.5` about elided lifetimes or parentheses. That directory is a pinned, patched copy of the EOL glib 0.18 line required by the GTK3/WebKitGTK 4.1 Tauri stack; upstream published no 0.18.6, and the patch carries the RUSTSEC-2024-0429 soundness fix. Those warnings are expected on newer Rust toolchains and are not application warnings. The workspace manifest intentionally declares only dependencies that a crate actually uses, so the dev build stays free of unused-dependency warnings.

## Work on the app

From the repository root, install the locked frontend dependencies and start Tauri:

```bash
( cd desktop && bun install --frozen-lockfile )
bun run --cwd desktop tauri dev
```

Use the Tauri command for desktop development; do not substitute direct `cargo run`. Tauri development uses its configured `build.devUrl`, while the native custom-protocol production binary embeds `frontendDist`. `scripts/local-run.sh` wraps the same workflow for quick source runs (`--deps` syncs locked dependencies, `--run -- /path` passes a target); it never replaces the validation commands below.

For a **visual-only** check of the React layout without launching Tauri, start `bun run --cwd desktop dev` and open `http://127.0.0.1:1420/visual-harness.html` in a browser. That page is a development-only entry that injects mocked native IPC before the app mounts, so the real components and CSS render in a normal browser and can be inspected with screenshots, the accessibility tree, and Lighthouse. It is not part of the production build (Vite only builds `index.html`) and its mock data is not a substitute for exercising the host ClamAV bridge, helper, or event stream in the real app.

To see the **real Tauri/WebKitGTK window** (native form controls can render differently from Chromium), run the app with `bun run --cwd desktop tauri dev`, focus its window, and run `bash scripts/capture-app-window.sh [out.png]`. The script uses Spectacle on KDE/Wayland, gnome-screenshot on GNOME, grim on wlroots/Sway/Hyprland, and ImageMagick/scrot/ffmpeg on X11, then prints the PNG path; open that file with an image-capable tool. Supported assistants expose this as a `/capture-app` command, so any agent can inspect the actual desktop UI rather than assuming the browser rendering matches.

The GUI runs through Tauri/WebKitGTK. For the headless core CLI, use the native binary directly; this route must not initialize a WebKit window:

```bash
cargo run -p linux-defender-core --bin linux-defender-cli -- help
cargo run -p linux-defender-core --bin linux-defender-cli -- scan --help
cargo run -p linux-defender-core --bin linux-defender-scheduled-scan -- --dry-run
```

The `linux-defender` command preserves seven subcommands: `scan`, `quarantine`, `profile`, `status`, `history`, `help`, and `install-privileged-helper`. Keep their flags, JSON/text output, standard streams, and exit semantics compatible. `linux-defender-scheduled-scan` remains a separate executable.

The CLI accepts conventional bundled scan flags and compatible attached `history` arguments. Use `--` before a target whose name looks like an option, for example `linux-defender scan -- --virustotal`; this keeps it a scan target rather than treating it as a flag.

The installed command surface is:

```bash
linux-defender scan /path/to/target
linux-defender quarantine list --json
linux-defender profile list --json
linux-defender status --json
linux-defender history --limit 20 --json
linux-defender help scan
sudo linux-defender install-privileged-helper
linux-defender-scheduled-scan --dry-run
```

`install-privileged-helper` is the inherited manual native/source-host path. Its real installation requires root and stages a compiled helper with its polkit policy; retain it only for **mutable** source hosts. Linux Defender has not published signed helper packages, so its release-driven helper installer is not ready for use. Fedora Atomic contributors must use verified RPM layering and reboot for manual repair, never this source installer against immutable `/usr`. The Flatpak rejects this host command, so do not use `sudo flatpak`.

For source-host development, build only the headless binaries, then use the non-privileged staging mode in a directory you own:

```bash
cargo build --locked -p linux-defender-core --bins
stage_dir="$(mktemp -d)"
./target/debug/linux-defender-cli install-privileged-helper --prefix "$stage_dir"
```

On a mutable native host, the actual installation is a separate, privileged action; do not run Cargo as root:

```bash
sudo ./target/debug/linux-defender-cli install-privileged-helper
```

### Debugging

Use structured Rust logging while starting the desktop:

```bash
RUST_LOG=linux_defender_core=debug,linux_defender=debug bun run --cwd desktop tauri dev
```

Use the Tauri/WebKit developer tools for frontend state and the terminal for Rust/core diagnostics. Never replace native IPC with a browser filesystem, shell, or process permission. The only frontend request boundary is Tauri's allowlisted `request` command and `linux-defender-event` event stream.

### Optional coding-agent skills

These optional, project-local skills assist compatible coding agents; they are not application dependencies and do not change the build or runtime requirements. From the repository root, install only the selected skills:

```bash
npx skills@1.7.4 add apollographql/skills --skill rust-best-practices
npx skills@1.7.4 add vercel-labs/agent-skills --skill vercel-react-best-practices
npx skills@1.7.4 add addyosmani/web-quality-skills --skill accessibility
```

Do not use `-g` or bulk-install an upstream repository. Imported payloads belong in `.agents/skills`; `.claude/skills` provides compatibility links. The three imported skills are locally adapted with Linux Defender enforcement rules. `skills-lock.json` records each source, selected `skillPath`, the reviewed upstream hash (`upstreamHash`), the enforced local payload hash (`computedHash`), a `locallyAdapted` flag, and the review date. Refresh only a named skill intentionally: review the upstream diff, update the imported file, and refresh both hashes and the date in the same change. `bash scripts/check-all.sh` verifies every imported skill still matches its locked local hash and that every skill is named in `AGENTS.md`, `CLAUDE.md`, or this guide, so no skill is forgotten.

### Automatic consistency enforcement

`AI-ENFORCEMENT.md` is the canonical rules file for every assistant; the `linux-defender-enforcement` skill points to it. Tool-specific adapters are optional contributor aids documented in the repository's internal AI tooling index; they never replace `AGENTS.md`, git hooks, and CI. The rules are enforced, not merely documented:

- `bash scripts/check-all.sh` is the single source of truth for static checks: broken doc links, orphaned files anywhere in the repo, cross-layer contracts, version and app-identity agreement, host signature database health (presence, age, EICAR), gettext (including the generated `po/TRANSLATION-REVIEW.md` human-review report, host-tool guidance, and static integration assets), skill hashes and wiring, stale branding, dead frontend modules, all six packaging formats, format-correct file-manager assets, host-ClamAV setup guidance in app and site, Sway wiring, and website sidebar/component wiring.
- `bash scripts/audit-consistency.sh` adds the heavy builds, tests, clippy, git sync, and CI status.
- `./scripts/hooks/install-hooks.sh` installs a pre-commit hook (all static checks plus Rust format and TypeScript type-check) and a pre-push hook (the full audit).
- Consistency Audit CI runs both scripts on every push and pull request, and weekly on `main`.

Cross-layer features are declared in `scripts/cross-layer-contracts.json`. Add an entry whenever a feature spans two or more layers (core, native runtime, frontend, website docs, packaging); `scripts/check-cross-layer.py` also derives Tauri commands, CLI subcommands, and active locales from source so a feature cannot land in only one layer.

Several scheduled workflows keep dependencies, skills, signatures, documentation links, and packaging fresh. `Refresh Dependabot sources` (`dependabot-refresh.yml`) rebuilds locked Flatpak dependency sources for Dependabot pull requests. `Upstream Freshness` (`upstream-freshness.yml`) runs `scripts/check-upstream-freshness.py` weekly: it compares each imported skill against the current upstream file and opens a review issue on drift. `Signature Database` (`signature-database.yml`) installs host ClamAV, runs `freshclam`, and executes `scripts/check-signatures.py` and `scripts/check-signature-feeds.py` weekly. Each format has a peer workflow badge, including `Build AUR` (`build-aur.yml`), which validates the app/helper PKGBUILDs and `.SRCINFO`; `Build All Packages` calls all six build workflows. `Packaging Sync` (`packaging-sync.yml`) runs `scripts/check-repo-consistency.py` and `scripts/check-packaging-consistency.py` weekly (with a named `check-aur-consistency.py` wrapper kept for AUR-only work), so every package format (DEB, RPM, Flatpak, AppImage, Snap, AUR app and helper) keeps the same version and app id, and compares reviewed packaging references from `packaging-lock.json` via `scripts/check-packaging-freshness.py`. Upstream content is never auto-merged — review provenance and license first, and never bundle an engine or signature database in any package. The URLhaus Auth-Key is redacted from all output.

ClamAV and gettext guidance is authored for this project; the contributor rules and the existing [architecture](/Linux-Defender/docs/contributing/architecture/) and [translation](/Linux-Defender/docs/contributing/translating/) pages remain authoritative. The React guidance applies to the client UI: exclude Next.js and other server-only changes. Check native accessibility in Tauri/WebKitGTK—Chrome accessibility scores alone do not prove the desktop application is accessible.

### Data compatibility

Linux Defender uses the following XDG layouts. On first startup it moves the prior ClamUI directories to these names without deleting their contents. If both old and new data directories are non-empty, startup merges the legacy files into the current tree and renames the old directory `<name>.migrated` (nothing is deleted):

```text
$XDG_CONFIG_HOME/linux-defender/settings.json
$XDG_CONFIG_HOME/linux-defender/profiles.json
$XDG_DATA_HOME/linux-defender/logs/
$XDG_DATA_HOME/linux-defender/quarantine.db
$XDG_DATA_HOME/linux-defender/quarantine/
$XDG_DATA_HOME/linux-defender/debug/
```

The Flatpak equivalents live beneath `~/.var/app/io.github.linuxdefender.linuxdefender/`. The first launch also checks the previous Flatpak app directory and moves the old settings and data subdirectories when the new paths are empty. Preserve atomic settings writes, unknown settings keys, existing JSON/SQLite schemas, privacy migrations, restrictive file modes, and profile/import compatibility. The core must remain GTK-widget and Tauri independent so these behaviors also work through the CLI.

### Host and privilege boundaries

Linux Defender uses host `clamscan` and `freshclam`; daemon mode also uses host `clamd` and `clamdscan`. Under Flatpak, calls cross the explicit `flatpak-spawn --host` boundary. Do not bundle or emulate ClamAV.

Protected configuration changes use the inherited authenticated protocol-v4 helper at `/usr/bin/linux-defender-apply-preferences` and `io.github.linuxdefender.linuxdefender.policy`. Preserve its allowlists, `PKEXEC_UID` validation, exit codes, and compatibility with an already-installed trusted helper. The helper is native Rust, not a Python wrapper. Linux Defender has not published its own signed helper package, so the in-app release installer cannot complete from this project yet. Keep the trust boundary fail-closed; never bypass a missing or invalid signature.

## Test before a pull request

Use the [bug report or feature request forms](https://github.com/Linux-Defender/Linux-Defender/issues/new/choose) for issues, and summarize your changes and actual verification in the pull request template.

Run the applicable checks from the repository root:

```bash
bun run --cwd desktop check
bun run --cwd desktop build
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Clippy compiles the production Tauri crate, whose `generate_context!` embeds `desktop/dist`; build the frozen frontend assets before running it.

For a single command that also checks gettext catalogs, stale branding, dead frontend modules, git sync, and GitHub Actions status, run the full local audit:

```bash
bash scripts/audit-consistency.sh
```

This is the same check the weekly Consistency Audit workflow runs. Fix every failure before pushing.

Exercise the real CLI and persisted compatibility fixtures in addition to unit tests. Test clean, EICAR, cancellation, scheduling dry-run, privileged-helper rejection, and compatible CLI output. For desktop work, manually verify Tauri startup, navigation, events, native dialogs, tray behavior, and file-argument forwarding.

Recorded migration evidence includes Rust workspace tests and strict Clippy, real Tauri/AppImage/Flatpak EICAR scans through the host bridge, prior XDG JSON/SQLite/keyring compatibility, and desktop copy/ZIP-export coverage. It is not a zero-regression guarantee and does not claim exercised protected host writes, VirusTotal uploads, physical-device hardware, Wayland, or an aarch64 build of the current migration revision.

## Packaging boundaries

Linux Defender currently has build definitions for Debian packages, a Flatpak, an x86_64 AppImage, and Fedora helper RPMs. These are packaging targets, not a tested all-distro support guarantee, and no signed Linux Defender release is published. CachyOS/Arch has AUR source recipes in `aur/` for the app and matching helper; they are not submitted to the AUR yet.

A Debian release is a version- and architecture-matched application/helper pair. Flatpak declares GNOME 51 and dependencies for `x86_64` and `aarch64`, but a local build validates only its native architecture. AppImage remains x86_64. Fedora RPMs are helper-only. Every format retains the host ClamAV boundary.

Build with the maintained native packaging entry points:

```bash
./debian/build-deb.sh
# Package the three binaries built on the Ubuntu 22.04-compatible baseline.
LINUX_DEFENDER_ARTIFACT_DIR=/absolute/path/to/ubuntu22/target/release ./debian/build-deb.sh dist
UPDATE_INFORMATION='gh-releases-zsync|Linux-Defender|Linux-Defender|latest|Linux-Defender-*-x86_64.AppImage.zsync' ./appimage/build-appimage.sh
```

### Fedora helper RPM packaging

```bash
./rpm/build-privileged-helper-rpm.sh dist
LINUX_DEFENDER_ARTIFACT_DIR=/absolute/path/to/ubuntu22/target/release LINUX_DEFENDER_RPM_ARCH=x86_64 ./rpm/build-privileged-helper-rpm.sh dist
```

The scripts can produce local `x86_64` or `aarch64` helper artifacts when built for the matching target; they contain the Rust helper and canonical policy, not the GUI or ClamAV. A local RPM is unsigned and is not an eligible installer asset. Only a matching signed RPM published with its detached signature can be used by the in-app Fedora installer. The RPM builder requires Cargo, `readelf` from `binutils`, and the `rpm`/`rpmbuild` package tools; a local source compilation also needs the usual Rust C toolchain, `pkg-config`, and GLib development files. It builds only the helper, so it needs neither Python nor the Bun/Tauri GUI toolchain. `LINUX_DEFENDER_ARTIFACT_DIR`, `CARGO_TARGET_DIR`, and `CARGO_BUILD_TARGET` select a prebuilt or nondefault Cargo artifact; `LINUX_DEFENDER_RPM_ARCH` asserts `x86_64` or `aarch64` against the helper ELF.

`debian/build-deb.sh` is the authoritative Debian entry point: it produces the application/helper pair and stages the policy and scheduled-scan payload. `LINUX_DEFENDER_ARTIFACT_DIR` must contain executable `linux-defender`, `linux-defender-scheduled-scan`, and `linux-defender-apply-preferences` binaries from the baseline build. The AppImage build produces `Linux-Defender-<VERSION>-x86_64.AppImage`; when `UPDATE_INFORMATION` points to a published Linux Defender release feed, it also produces `.zsync` metadata. Until a signed Linux Defender release includes those assets, the AppImage update feed cannot update users.

### Dependabot and Flatpak sources

Dependabot checks Cargo, the desktop and website Bun projects, and GitHub Actions weekly. Minor and patch version updates are grouped per project; major updates and security updates remain separate.

`desktop/bun.lock` is the canonical desktop lockfile; `desktop/yarn.lock` is only its Bun-generated export for Flatpak's offline source generator. Eligible Cargo and desktop Dependabot pull requests automatically refresh the coupled lockfile export and Flatpak source JSON files; website and Actions updates do not need this refresh. The Dependabot branch must include current `main`; for an older pull request, comment `@dependabot rebase` first. If a refresh fails or an existing Dependabot pull request needs one, run **Dependabot source refresh** in GitHub Actions with its pull request number as `pr_number`, or use the command below, replacing `123` with that number:

```bash
gh workflow run dependabot-refresh.yml --ref main -f pr_number=123
```

Review the generated changes and the verification workflow results on the pull request. For a manual local refresh, export the Yarn lockfile and regenerate both Flatpak source lists using the generator prerequisites described below:

```bash
( cd desktop && bun install --frozen-lockfile --yarn )
scripts/generate-flatpak-sources.sh
```

## Flatpak builds and Flathub releases

### Local Flatpak checkout build

`flathub/io.github.linuxdefender.linuxdefender.local.yml` is a developer checkout recipe. It uses `type: dir`, includes the working tree, and is not an immutable release manifest. Use a fresh directory under the checkout so the build target, Builder state, and exported repository are owned by you and on the same filesystem. This command neither installs nor replaces an existing Flatpak, and it does not delete an existing build directory:

```bash
mkdir -p target
flatpak_workdir="$(mktemp -d "$PWD/target/flatpak.XXXXXX")"
flatpak-builder --user --arch="$(flatpak --default-arch)" \
  --state-dir="$flatpak_workdir/state" \
  --repo="$flatpak_workdir/repo" \
  "$flatpak_workdir/build" \
  flathub/io.github.linuxdefender.linuxdefender.local.yml
```

The checked-in Flatpak manifest currently has the same checkout-source form. It is useful for local development, but neither checkout YAML is the immutable manifest required for an official release.

### Immutable Flatpak release packaging

An official Rust Flatpak submission requires exactly three checked-in packaging inputs: a canonical YAML whose application source is a concrete public Git URL and full commit pin, `flathub/cargo-sources.json`, and `flathub/bun-sources.json`. `cargo-sources.json` derives from the settled `Cargo.lock`; `bun-sources.json` derives from the canonical `desktop/bun.lock` and its Bun-produced `desktop/yarn.lock` export. Do not hand-edit their checksums or retain legacy Python source JSON as a Rust packaging input.

When updating a Rust dependency, constrain the resolver to the intended package (for example, `cargo update -p <crate> --precise <version>`) before regenerating the Cargo source input. Do not refresh the whole Cargo graph merely to update one dependency.

The product lockfile remains `desktop/bun.lock`. After settling frontend dependencies, intentionally export its paired Yarn lockfile before generating Flatpak sources:

```bash
( cd desktop && bun install --frozen-lockfile --yarn )
```

Run the generator from a clean checkout whose intended source commit is already public and whose lockfiles match that commit. It requires `flatpak-cargo-generator.py` plus `flatpak-node-generator` (the node generator requires Python 3.11+):

```bash
release_commit="$(git rev-parse HEAD)"
scripts/generate-flatpak-sources.sh \
  --release-url https://github.com/Linux-Defender/Linux-Defender.git \
  --release-commit "$release_commit" \
  --release-output flathub/io.github.linuxdefender.linuxdefender.release.yml
```

This rewrites both checked-in source JSON files and writes the Git-pinned release manifest explicitly. Review all three files together: the generated manifest replaces the complete checkout `dir` source block, including its exclusions, with the URL and exact commit while retaining the other source entries and JSON includes. This produces GitHub Flatpak release packaging input and a candidate Flathub submission manifest; it does not update the live Flathub store.

Build that generated manifest locally only in a fresh directory below the checkout, so Builder state, the build directory, and exported repository stay on the same filesystem and are owned by you:

```bash
mkdir -p target
flatpak_release_dir="$(mktemp -d "$PWD/target/flatpak-release.XXXXXX")"
flatpak-builder --user --arch="$(flatpak --default-arch)" \
  --state-dir="$flatpak_release_dir/state" \
  --repo="$flatpak_release_dir/repo" \
  "$flatpak_release_dir/build" \
  flathub/io.github.linuxdefender.linuxdefender.release.yml
```

This local build neither installs nor replaces a Flatpak, and it proves only the host architecture. The manifest retains legacy compatibility identifiers and is not ready to publish as a Linux Defender Flatpak. Complete an application-ID and data migration first, then validate `x86_64` and `aarch64`, obtain Flathub review, and publish only after signed release assets and migration behavior are ready. Linux Defender has no published Flathub package or signed release bundles yet.

Before publishing, inspect package payloads for the right architecture, native command names, helper/policy paths, and absence of a Python application runtime. Build compatibility still requires proof from the baseline environment and target package/OS; do not infer it from this development guide.

## Write documentation

The Starlight source is `website/src/content/docs/docs/`. Reuse the existing focused pages, use repository-page `/Linux-Defender/docs/.../` links, and keep the existing sidebar structure unless navigation truly changes. Root `README.md` and `CONTRIBUTING.md` are short discovery pointers; `CHANGELOG.md` and `RELEASE_NOTES.md` remain canonical release sources rendered by MDX imports.

Website commands:

```bash
( cd website && bun install --frozen-lockfile )
bun run --cwd website check
bun run --cwd website build
```

Do not edit generated `website/public/` or `website/dist/`. Keep the active `de`, `en`, `es`, `fr`, `hu`, `it`, `nb`, `pt_BR`, `vi`, and `zh_CN` gettext catalogs in `po/` and listed in `po/LINGUAS`; Rust build tooling and packaging export each catalog for the core and UI. Localized historical scan-summary recognition is embedded build data, not an archived catalog source, and catalog extraction, loading, and packaging have no Python runtime dependency. See [translation](/Linux-Defender/docs/contributing/translating/) for the catalog workflow.

## Update the application icon

`icons/io.github.linuxdefender.linuxdefender.svg` is the source icon; `icons/io.github.linuxdefender.linuxdefender.png` is its checked-in 128×128 rendering. When the SVG changes, regenerate and commit both files once. Builds install the committed PNG and never convert it at runtime.
