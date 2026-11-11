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
git switch revival/unified-app
cargo fmt --check --all
cargo test --workspace --locked
cd desktop
bun install --frozen-lockfile
bun run build
bun run tauri dev
```

The first Rust build can take several minutes. The last command opens the development app; it does not install a system-wide release. Test scans only on files you choose, verify cancellation and quarantine/restore with harmless test files, check light/dark themes and Wayland/X11, and confirm FreshClam status. Never submit a file to VirusTotal or urlscan unless you understand and explicitly accept its sharing settings.

Current sandbox results: `cargo fmt --check --all`, frontend build, and the focused platform integration suite (7 tests) pass. The full workspace run hits four helper tests that require filesystem/tool access unavailable in this sandbox. Skipping those allowed all 17 desktop unit tests and 103 core tests to pass, but CLI subprocess tests then remained active for over 60 seconds and the run was stopped. Run the full suite on CachyOS to distinguish sandbox limitations from host failures.

Thunar action unit tests pass, but the in-app integration manager is currently Flatpak-only; the native CachyOS development build will not show that manager yet. To validate the actual Thunar menu, build/install the Flatpak and enable its Thunar Send To actions in Settings → Behavior → File Manager Integration on a machine with Thunar installed. KDE tray clicks and Dolphin menus can be tested in the normal CachyOS session. A successful build is not a visual desktop test or a claim of complete protection.
