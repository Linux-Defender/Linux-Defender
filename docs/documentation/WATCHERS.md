# Watchers index

Every scheduled workflow and what it watches. This is internal contributor
documentation; `scripts/check-watchers.py` verifies the index cannot drift.

| Workflow | Schedule | Watches |
| --- | --- | --- |
| `consistency.yml` | Weekly | Full repo/app/site audit: static checks, builds, clippy, tests, git/CI sync. |
| `codeql.yml` | Weekly | Code scanning for Rust/TypeScript changes. |
| `dependency-audit.yml` | Weekly | Rust and all Bun workspaces, including the MCP assist server. |
| `deploy-website.yml` | Weekly | Published site rebuild so the latest-release navigation stays current. |
| `doc-links.yml` | Weekly | Every external documentation link. |
| `proof-html.yml` | Weekly | Built-site HTML structure (DOCTYPE, duplicate IDs, alt text); installs Playwright for Mermaid and validates a throwaway copy with the `/Linux-Defender/` base path rewritten to root. |
| `packaging-sync.yml` | Weekly | All six package formats, version/app-id agreement, and the AUR reference in `packaging-lock.json`. |
| `signature-database.yml` | Weekly | Host ClamAV database age, EICAR detection, and the product-default URLhaus export. |
| `upstream-freshness.yml` | Weekly | Imported skill hashes in `skills-lock.json` and reviewed ClamUI/Lenspect/ClamTk/ClamAV Bytecode Compiler heads in `parity-lock.json`. |

Event/PR workflows (`test.yml`, `lint.yml`, `build-*.yml`, `release.yml`,
`i18n.yml`, `website.yml`, `dependency-review.yml`,
`dependabot-refresh.yml`, `auto-assign.yml`) run on their declared events. Every
workflow also declares `workflow_dispatch` so it can be triggered manually for
verification, and every workflow is listed in the README badges index.

A moved upstream head creates a review issue; nothing is auto-merged. The
host ClamAV engine and database are never bundled by any package format.
