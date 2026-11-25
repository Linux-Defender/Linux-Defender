# Linux Defender

Linux Defender configures host ClamAV tools and presents their scan outcomes.

## Language

**Save & Apply**:
The explicit application of edited ClamAV configuration and scheduled-scan preferences. It may finish with some changes saved and others not applied.
_Avoid_: atomic settings transaction

**Save proposal**:
The edited configuration and scheduled-scan values captured for one Save & Apply attempt, separate from currently loaded values.

**Durable group**:
A set of preference changes confirmed saved during a Save & Apply attempt, such as ClamAV configuration files or scheduled-scan preferences.

**Scan result**:
A scan outcome containing its status, detected threats, counts, warnings, and errors. Standalone observed counts and daemon pre-counts are distinct evidence, not interchangeable measurements.

**Parity**:
A ClamUI/ClamTk/Lenspect behavior is *ported* (implemented and tested in this Rust/Tauri/React runtime), *intentionally deferred* (documented in `docs/clamui-fork/STATUS.md` with a reason), or *open*. A merged upstream PR is not proof a behavior exists here; verify code and tests.

**Integration**:
A narrow, tested seam between Linux Defender and the host desktop or ClamAV — file-manager actions, tray/D-Bus, host `clamscan`/`clamdscan`/`freshclam`, the privileged helper, safe open/export/clipboard, VirusTotal/urlscan, or scheduled scans. Integrations never bundle an engine or add a second app runtime.

**Dead / stale**:
A ported module with no live caller (wire it or remove it), a broken doc link, an orphaned doc/skill, or an old ClamUI identifier/text in a live file (only migration/compat references are allowed). `scripts/check-all.sh` checks all of these on every commit and PR; `scripts/audit-consistency.sh` adds builds, tests, and sync.

**Canonical AI rules**:
`AI-ENFORCEMENT.md` at the repository root. It is a tool-neutral rules file with skill-style frontmatter; git hooks and CI enforce it for every assistant, while Claude Code, OpenCode, Codex, Aider, Cursor, Continue, Zed, and the thin `linux-defender-enforcement` pointer skill read it at runtime. Rules are never duplicated in an adapter. `scripts/check-ai-enforcement-wiring.py` enforces that contract.

**Cross-layer contract**:
A feature declared in `scripts/cross-layer-contracts.json` with the list of layers (core, native runtime, frontend, website docs, packaging) that must contain it. A feature added to only one layer fails `scripts/check-cross-layer.py`, which also derives Tauri commands, CLI subcommands, and locales from source. See `AI-ENFORCEMENT.md` for the mandatory rules injected into every AI model.
