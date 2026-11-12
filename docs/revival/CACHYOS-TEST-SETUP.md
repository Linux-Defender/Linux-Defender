# CachyOS developer setup and smoke test

The source checkout does not bundle Rust/Cargo or Bun. Install the distro packages and Tauri's Arch Linux build dependencies first. These commands use CachyOS/Arch repositories; `pacman -Syu` performs a full system upgrade, as Arch-based systems do not support partial upgrades.

```fish
sudo pacman -Syu --needed base-devel curl wget file openssl appmenu-gtk-module libappindicator-gtk3 librsvg xdotool webkit2gtk-4.1 rustup bun
rustup default stable
fish_add_path ~/.cargo/bin
```

Confirm the tools and run tests:

```fish
cargo --version
bun --version
cd /home/kiras/Linux-Defender
git fetch origin
git switch rebrand/linux-defender-identity
git pull --ff-only
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cd desktop
bun install --frozen-lockfile
bun run build
bun run tauri dev
```

This tests the pushed identity-rebrand branch from PR #3. It does not merge or install the app system-wide. To test the current `revival/unified-app` branch instead, skip the `git switch` and `git pull` lines.

For the new VirusTotal folder/progress feature, first run the mocked backend tests above. In the app, configure a personal VirusTotal API key in Preferences, open Scan, choose the folder icon in the scan actions, and inspect the complete file list and total size before clicking **Upload and scan folder**. Use a temporary folder with harmless files only; confirm the scan shows each file and progress, then use **Cancel scan** to verify cancellation. For URL checks, use only a non-sensitive public test URL and explicitly accept VirusTotal/urlscan sharing terms. Do not use malware samples or private files/URLs for this UI check.

The first Rust build can take several minutes. The last command opens the development app; it does not install a system-wide release. Test scans only on files you choose, verify cancellation and quarantine/restore with harmless test files, check light/dark themes and Wayland/X11, and confirm FreshClam status. Never submit a file to VirusTotal or urlscan unless you understand and explicitly accept its sharing settings.

Current sandbox results: formatting, frontend build, URLscan (4), platform integration (8), scheduler (8), translation extraction/checks, and desktop runtime (17) pass. The full workspace run hits four privileged-helper tests that require filesystem/tool access unavailable in this sandbox. Skipping those allowed 103 core tests and 17 desktop tests to pass, but the CLI subprocess suite stopped progressing after 13 of 18 reported completion and hit a 60-second cutoff. Five remaining CLI cases each also hit a 12-second cutoff when isolated. Run the full suite on CachyOS to distinguish sandbox limitations from host failures.

Thunar action unit tests pass, but the in-app integration manager is currently Flatpak-only; the native CachyOS development build will not show that manager yet. To validate the actual Thunar menu, build/install the Flatpak and enable its Thunar Send To actions in Settings → Behavior → File Manager Integration on a machine with Thunar installed. URL Scan uses a private-by-default submission, but do not submit a sensitive URL during testing. KDE tray clicks and Dolphin menus can be tested in the normal CachyOS session. A successful build is not a visual desktop test or a claim of complete protection.
