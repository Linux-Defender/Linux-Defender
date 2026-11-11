---
title: Release verification
description: Current Linux Defender release status and the verification rules for future packages.
---

## Linux Defender artifacts

Linux Defender 0.6.0 is a development snapshot. This repository has not published signed Linux Defender packages, an official release signing key, or release checksums. Do not install an artifact presented as a Linux Defender release until it is linked from the [Linux Defender releases page](https://github.com/Linux-Defender/Linux-Defender/releases) and its signature instructions are published here.

The ClamUI 0.6.0 signature key and release assets belong to the upstream ClamUI project. They do not verify Linux Defender builds or authorize Linux Defender packages. For upstream ClamUI releases, use its [official release page](https://github.com/linx-systems/clamui/releases) and instructions.

## Checking a source checkout

For a development build, confirm the branch and whether your checkout has local edits before building:

```bash
git status --short --branch
git rev-parse HEAD
```

Build from a commit in the Linux-Defender/Linux-Defender repository, keep the commit hash with your test notes, and review any local modifications. A locally built app is not a signed release artifact, even when its source came from GitHub.

## Future packages

Before Linux Defender publishes binaries, each release format needs a documented provenance and verification process. The release must provide trusted signing-key fingerprints, detached signatures or signed repository metadata, checksums, architecture-specific asset names, and a clear verification command. A checksum downloaded from the same untrusted location as a package does not authenticate it. Never bypass a failed or missing signature check.
