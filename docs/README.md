# docs

Repo documentation and internal reference material.

## Direct contents
- [DESIGN.md](DESIGN.md) — visual identity (Guardian color tokens, typography, component rules)

The [complete documentation map](DOC-MAP.md) links every Markdown/MDX document
in the repository. It is generated and automatically verified, so a new doc
cannot be written and then forgotten.

## Folder index
- [`clamui-fork/`](clamui-fork/) — the ClamUI fork: what was ported from upstream, the rebrand state, and the upstream parity matrix
- **Package formats:** [DEB](../debian/README.md), [RPM helper](../rpm/README.md), [AppImage](../appimage/README.md), [Flatpak](../flathub/README.md), [Snap](../snap/README.md), [AUR](../aur/README.md) — every format has a README with build prerequisites, host-ClamAV boundary, and release status.
- [`documentation/`](documentation/) — general documentation index and in-repo reference
- [`revival/`](revival/) — revival/rework records. Start with its [index](revival/README.md): upstream repository inventory, ClamUI/ClamTk/Lenspect parity reviews, rebrand audits, and the requirement ledger.
- [`translations/`](translations/) — gettext catalog status and how to finish the audit-string translations
- [`mcp/`](../mcp/README.md) — local MCP server that assists human-only validation with read-only/proposal tools
