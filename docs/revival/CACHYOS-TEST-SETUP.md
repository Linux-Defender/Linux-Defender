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

The current headless test environment ran the Rust workspace suite with five host-specific tests skipped. On CachyOS, run the full command above without skips. A successful build is not a visual desktop test or a claim of complete protection.
