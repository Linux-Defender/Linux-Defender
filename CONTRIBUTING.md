# Contributing to Linux Defender

Thanks for helping make Linux Defender reliable across Linux desktops. Report bugs and feature requests in [GitHub Issues](https://github.com/Linux-Defender/Linux-Defender/issues). Report vulnerabilities privately through [GitHub Security Advisories](https://github.com/Linux-Defender/Linux-Defender/security/advisories/new), not a public issue.

The repository's development guides are maintained in [`website/src/content/docs/docs/contributing/`](website/src/content/docs/docs/contributing/):

- [Development and packaging](website/src/content/docs/docs/contributing/development.md)
- [Rust/Tauri architecture](website/src/content/docs/docs/contributing/architecture.md)
- [Translation](website/src/content/docs/docs/contributing/translating.md)
- [Package signing](website/src/content/docs/docs/contributing/signing.md)
- [Security](website/src/content/docs/docs/contributing/security.md)
- [Code of conduct](CODE_OF_CONDUCT.md)

Linux Defender is a Rust core with a Tauri/React desktop. Keep ClamAV and FreshClam host-managed, preserve the privileged-helper security boundary, and keep new signature feeds opt-in until their provenance, license, update integrity, and failure handling have been reviewed. Do not add a second Python/GTK application runtime.

Before opening a pull request, run the checks relevant to your change. For Rust changes, use `cargo fmt --all -- --check`, `cargo clippy --workspace --all-targets --locked -- -D warnings`, and `cargo test --workspace --locked`. For desktop and website changes, install dependencies with `bun install --frozen-lockfile` in the relevant directory, then run its check/build scripts. Include the exact checks and results in your pull request.

The [issue and PR ledgers](docs/revival/) describe ongoing upstream parity work; review does not mean every report is implemented. Please keep those records current when porting behavior from ClamTk or another related scanner.
