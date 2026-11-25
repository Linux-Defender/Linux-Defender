# AppImage

`build-appimage.sh` builds the x86_64 Linux Defender AppImage from the
Rust/Tauri workspace. Build on an Ubuntu 22.04-compatible baseline so the
bundled GTK3/WebKitGTK libraries keep that glibc floor.

```bash
./appimage/build-appimage.sh
```

Requirements: `cargo`, `bun`, `appimagetool`, and `pkg-config`. Output is
`Linux-Defender-<version>-x86_64.AppImage` with an optional `.zsync` sidecar for
signed update metadata. The AppImage uses host ClamAV; it must not bundle an
engine or signature database. Native dialogs and the SNI tray are provided by
the runtime/desktop, not by a Python helper.

No signed AppImage or public zsync feed is published yet. See
[installation](/Linux-Defender/docs/installation/) and the
[development guide](/Linux-Defender/docs/contributing/development/).
