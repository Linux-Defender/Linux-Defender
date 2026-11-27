# Flatpak / Flathub

`io.github.linuxdefender.linuxdefender.yml` is the Flatpak build recipe; the
`.local.yml` variant is for local development. Both use GNOME Platform/SDK 51,
the Rust stable and Node 24 extensions, and the rebranded
`io.github.linuxdefender.linuxdefender` app id. `cargo-sources.json` and
`bun-sources.json` are generated locked source manifests — do not hand-edit them.

`crates/linux-defender-core/assets/integrations/` is the source of the packaged file-manager actions and service menus (native formats use `assets/integrations-native/`).
Host ClamAV tools are reached through `flatpak-spawn --host`; no engine or
signature database is bundled in the sandbox. Database detection reads the
host's `DatabaseDirectory` read-only.

No Flatpak is published to Flathub or another remote yet. See
[installation](/Linux-Defender/docs/installation/) for current status and the
[development guide](/Linux-Defender/docs/contributing/development/) for local
build prerequisites.
