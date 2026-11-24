import { Plugin } from "@opencode/plugin";

// Injected into every model context in this repository so every agent, model,
// and subagent obeys the same hard rules instead of relying on prose guidance.
const RULES = `LINUX DEFENDER MANDATORY RULES (enforced by hooks and CI):
1. Before saying "done", run bash scripts/check-all.sh and fix EVERY failure.
2. For any multi-layer or audit/parity/dead/stale/sync task, use the linux-defender-parity skill.
3. Cross-layer parity: a feature in one layer must be wired in every consuming layer; add it to scripts/cross-layer-contracts.json.
4. No dead links, dead files, stale docs/skills/site, or un-wired modules. Link new docs, import new modules, name new skills in AGENTS.md/CLAUDE.md/dev guide, add new site pages to the sidebar, reference new scripts/workflows.
5. Read the entire user request, enumerate every requirement, and satisfy all of them. Never declare done with a named item unaddressed.
6. Keep compatibility identifiers (clamui-* names, ~/.config/clamui, ~/.local/share/clamui, clamui.log*, cron markers, Nautilus fallbacks). Do not rebrand them away.
7. Exercise the real app (headless CLI status/history/EICAR scan, logs) and the production-preview site (Lighthouse), not only unit tests. Verify host signature database freshness with scripts/check-signatures.py and the product-default URLhaus feed with scripts/check-signature-feeds.py (Auth-Key redacted). Never bundle an engine or signature database in any package.
8. Pre-commit runs static checks; pre-push runs the full audit; CI runs both. Do not bypass hooks. Full check: bash scripts/audit-consistency.sh.`;

export default Plugin.define({
  id: "linux-defender-enforcement",
  async setup(ctx) {
    await ctx.session.hook("context", (event) => {
      event.system.push({ type: "text", text: RULES });
    });
  },
});
