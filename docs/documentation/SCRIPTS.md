# Scripts index

Every tracked script in `scripts/` is listed here so none is forgotten. This
is internal contributor documentation; scripts are development aids, not
application runtime dependencies.

## Main entry points

- `scripts/check-all.sh` — single source of truth for static checks (pre-commit runs it).
- `scripts/audit-consistency.sh` — full audit: builds, tests, clippy, static checks, git/CI sync (pre-push runs it).
- `scripts/local-run.sh` — quick source build/run wrapper.
- `scripts/merge-catalogs.py` — regenerate POT and merge all active gettext catalogs.
- `scripts/generate-doc-map.py` — regenerate `docs/DOC-MAP.md`.
- `scripts/generate-translation-review.py` — regenerate `po/TRANSLATION-REVIEW.md`.

## Static checks

- `scripts/check-ai-enforcement-wiring.py` — AI adapters read the canonical rules.
- `scripts/check-aur-consistency.py` — named AUR-only wrapper over the unified packaging check.
- `scripts/check-badges.py` — every workflow has a README status badge.
- `scripts/check-build-wiring.py` — `tauri dev` → Vite → `dist`, vendored glib patch.
- `scripts/check-built-links.py` — built-site links, anchors, and HTML/CSS structure.
- `scripts/check-compiled-catalogs.ts` — compiled catalog identity check.
- `scripts/check-cross-layer.py` — IPC/CLI/locale/feature contracts from source.
- `scripts/check-support-parity.py` — declarative cross-service support invariants (VT/urlscan/urlhaus, frontend validators, scheduler, quarantine, capabilities, sanitization).
- `scripts/check-dead-files.py` — orphaned docs/modules/skills.
- `scripts/check-doc-indexes.py` — every internal doc linked from its folder index.
- `scripts/check-doc-links.py` — broken relative Markdown links.
- `scripts/check-external-links.py` — dead external documentation links.
- `scripts/check-file-modes.py` — shebang and Debian maintainer scripts are executable.
- `scripts/check-gate-wiring.py` — every checker is wired to a gate and every gate path exists.
- `scripts/check-host-tool-guidance.py` — app/site ClamAV commands.
- `scripts/check-integration-parity.py` — Flatpak vs native launcher assets.
- `scripts/check-ipc-operations.py` — every literal frontend IPC operation resolves to a core handler.
- `scripts/check-packaging-consistency.py` — all six formats.
- `scripts/check-packaging-freshness.py` — reviewed packaging reference drift.
- `scripts/check-potfiles.sh` — Rust/TS gettext source coverage.
- `scripts/check-repo-state.py` — one `main` branch and no local release tags.
- `scripts/check-repo-consistency.py` — versions, identity, workflow/script inventory.
- `scripts/check-scripts-index.py` — every tracked script is listed in this index.
- `scripts/check-signature-feeds.py` — URLhaus export health with key redacted.
- `scripts/check-signatures.py` — host database age + EICAR.
- `scripts/check-source-invariants.py` — explicit-apply path, retired event channel, CSP.
- `scripts/check-stale-phrases.py` — known stale claims.
- `scripts/check-sway-integration.py` — Sway wiring (build-time).
- `scripts/check-translations.sh` — gettext catalog validation gate.
- `scripts/check-upstream-freshness.py` — imported skill drift.
- `scripts/check-upstream-urls.py` — upstream inventory URLs.
- `scripts/check-workflows.py` — workflow YAML parses, named, triggerable.
- `scripts/check-watchers.py` — every scheduled workflow is indexed in `WATCHERS.md`.
- `scripts/extract-typescript-gettext.ts` — TS/TSX extraction.
- `scripts/update-pot.sh` — Rust/Tauri POT regeneration.

## Packaging and integrations

- `scripts/flatpak-release-source.awk`, `scripts/generate-flatpak-sources.sh`, `scripts/refresh-dependabot-sources.sh` — Flatpak locked sources.
- `scripts/install-nemo-actions.sh` (host-side installer from this checkout), `scripts/linux-defender-scan-nautilus.sh`, `scripts/linux-defender-virustotal-nautilus.sh` — file-manager helpers.

## Validation helpers

- `scripts/capture-app-window.sh` — real Tauri/WebKitGTK screenshot.
- `scripts/release-readiness.py` — read-only release checks and safe local tag preparation (never pushes).
- `scripts/validate-sway.sh` — interactive Sway checklist runner.
- `scripts/hooks/ai-enforcement-context.py`, `scripts/hooks/install-hooks.sh`, `scripts/hooks/pre-commit`, `scripts/hooks/pre-push` — git/AI hooks.
- `scripts/tests/test_external_links.py`, `scripts/tests/test_signature_check.py`, `scripts/tests/test_support_parity.py` — checker regression tests.
