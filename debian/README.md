# Debian / Ubuntu packages

`build-deb.sh` builds the architecture-matched application package;
`build-privileged-helper-deb.sh` builds the version-matched helper package.
Both use the workspace version from `Cargo.toml` and produce
`linux-defender_<version>_<arch>.deb` and
`linux-defender-privileged-helper_<version>_<arch>.deb`.

```bash
./debian/build-deb.sh
./debian/build-privileged-helper-deb.sh
```

Requirements: `dpkg-deb`, `gettext`, `cargo`, and `bun` (or set
`LINUX_DEFENDER_ARTIFACT_DIR` to prebuilt binaries). Both packages are root-owned
by `dpkg-deb --root-owner-group`. The helper installs
`/usr/bin/linux-defender-apply-preferences` and the matching rebranded PolicyKit
policy. No package bundles ClamAV, its engine, or its signature database; use
the host's `clamscan`, `freshclam`, and optionally `clamd`/`clamdscan`.

See [installation](/Linux-Defender/docs/installation/) for release status and
the [development guide](/Linux-Defender/docs/contributing/development/) for CI
validation.
