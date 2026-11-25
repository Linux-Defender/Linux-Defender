# Snap

`snapcraft.yaml` builds the Linux Defender snap. The snap uses the system
WebKitGTK/GTK3 stack and calls host ClamAV tools through the snap boundary;
`snap/local/linux-defender-launch` rewrites desktop launch variables so the
host environment is not leaked into wrapped commands.

```bash
snapcraft
```

The snap keeps the rebranded app id `io.github.linuxdefender.linuxdefender` and
does not bundle ClamAV, FreshClam, or a signature database. Protected host
configuration still requires the version-matched privileged helper and Polkit;
the snap's file-manager integrations honor the same compatibility fallbacks.

A successful CI build is not a published-store release. See
[installation](/Linux-Defender/docs/installation/) for current release status.
