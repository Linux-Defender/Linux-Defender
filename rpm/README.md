# Fedora / RPM helper package

This folder builds **only the privileged helper**, not the desktop application.
`build-privileged-helper-rpm.sh` and `linux-defender-privileged-helper.spec`
produce a version-matched, root-owned helper plus its PolicyKit policy.

```bash
./rpm/build-privileged-helper-rpm.sh
```

Requirements: `rpm`/`rpmbuild`, `readelf` (binutils), `cargo`, `pkg-config`, and
GLib development files; a helper-only build needs neither Python nor the Bun GUI
toolchain. `LINUX_DEFENDER_ARTIFACT_DIR`, `CARGO_TARGET_DIR`, and
`CARGO_BUILD_TARGET` select prebuilt or nondefault artifacts; the build asserts
the ELF architecture.

A locally built RPM is unsigned and is not an eligible in-app installer asset.
Only a matching signed RPM with its detached signature can be installed through
the application. ClamAV remains host-installed and is never bundled. See
[installation](/Linux-Defender/docs/installation/) for current release status.
