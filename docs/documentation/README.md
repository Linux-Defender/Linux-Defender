# Documentation

Source material for Linux Defender's published documentation lives in
[`../../website/src/content/docs/`](../../website/src/content/docs). This
folder holds **hand-written, in-repo reference and contributor documentation**
that is not part of the published website — things you need when developing,
reviewing, or migrating around the project.

## In this folder

| Folder | Contents |
|---|---|
| [`../clamui-fork/`](../clamui-fork/) | ClamUI fork history: what was ported from upstream, the rebrand state, and the upstream parity matrix |
| [`../revival/`](../revival/README.md) | Revival/rework index: link-checked upstream repository inventory, ClamTk/Lenspect/ClamUI parity reviews, rebrand audits, upstream changelog |

## Documentation guides

- **Troubleshooting:** [`website/src/content/docs/docs/troubleshooting.md`](../../website/src/content/docs/docs/troubleshooting.md)
- **Architecture:** [`website/src/content/docs/docs/contributing/architecture.md`](../../website/src/content/docs/docs/contributing/architecture.md)
- **Configuration:** [`website/src/content/docs/docs/reference/configuration.md`](../../website/src/content/docs/docs/reference/configuration.md)
- **Development:** [`website/src/content/docs/docs/contributing/development.md`](../../website/src/content/docs/docs/contributing/development.md)
- **Design tokens:** [`../../docs/DESIGN.md`](../../docs/DESIGN.md)

## Where to add what

- **User-facing docs** (app behavior, config, recovery): add/update files in
  `website/src/content/docs/docs/`. Use repository-page `/Linux-Defender/docs/.../` links.
- **Internal docs** (rebrand, migration, parity, contributor guides): add files
  here under `docs/clamui-fork/`, `docs/revival/`, or this `docs/documentation/` folder.
- **Translator notes, po/PO extraction details:** [`website/src/content/docs/docs/contributing/translating.md`](../../website/src/content/docs/docs/contributing/translating.md).
