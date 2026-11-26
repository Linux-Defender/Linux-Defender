---
title: Release verification
description: Current Linux Defender release status and the verification rules for future packages.
---

## Linux Defender artifacts

Linux Defender 0.6.0 is a development snapshot. The repository has an official release signing key, but has not published signed Linux Defender packages or release checksums. Do not install an artifact presented as a Linux Defender release until it is linked from the [Linux Defender releases page](https://github.com/Linux-Defender/Linux-Defender/releases) and its signature instructions are published here.

The Linux Defender release key is published in `signing-key.asc`. Its fingerprint is `28CA212A766A6D51273EBBD277B8EC8622C91282`. Verify that a package is linked from the [Linux Defender releases page](https://github.com/Linux-Defender/Linux-Defender/releases) and signed by this key before installation.

## Checking a source checkout

For a development build, confirm the branch and whether your checkout has local edits before building:

```bash
git status --short --branch
git rev-parse HEAD
```

Build from a commit in the Linux-Defender/Linux-Defender repository, keep the commit hash with your test notes, and review any local modifications. A locally built app is not a signed release artifact, even when its source came from GitHub.

## When the release workflow runs

`Release` (`.github/workflows/release.yml`) is the only workflow that signs artifacts. It starts when a tag matching `v*` is **pushed to GitHub**, or when a maintainer dispatches it manually. It builds signed Debian app/helper packages, the signed RPM helper, and a signed AppImage with the repository's GPG secrets, then creates a **draft** GitHub release whose notes come from `RELEASE_NOTES.md`. The draft is not published automatically: a human reviews the assets and signatures first.

This is deliberately left to a human decision. There are no published Linux Defender release packages yet, and the repository has **no tags on GitHub** — local legacy tags were removed so `git push --tags` cannot accidentally start a signed release. Do not create or push a `v*` tag until the version, changelog, release notes, CI state, and signing procedure have been reviewed. Read this page before dispatching `Release`, and never publish a draft that failed signature verification.

## Future packages

Before Linux Defender publishes binaries, each release format needs a documented provenance and verification process. The release must provide trusted signing-key fingerprints, detached signatures or signed repository metadata, checksums, architecture-specific asset names, and a clear verification command. A checksum downloaded from the same untrusted location as a package does not authenticate it. Never bypass a failed or missing signature check.
