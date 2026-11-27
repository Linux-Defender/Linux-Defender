# Snap

`snapcraft.yaml` builds the Linux Defender snap. The snap runs host ClamAV tools directly under classic confinement and bundles
the GTK3/WebKitGTK 4.1 libraries staged from the core22 base;
`snap/local/linux-defender-launch` rewrites desktop launch variables so the
host environment is not leaked into wrapped commands.

```bash
snapcraft
```

The snap is named `linux-defender` and keeps `io.github.linuxdefender.linuxdefender`
as its desktop `common-id`/AppStream id; it does not bundle ClamAV, FreshClam, or a signature database. Protected host
configuration still requires the version-matched privileged helper and Polkit;
the snap's file-manager integrations honor the same compatibility fallbacks.

A successful CI build is not a published-store release. See
[installation](/Linux-Defender/docs/installation/) for current release status.
