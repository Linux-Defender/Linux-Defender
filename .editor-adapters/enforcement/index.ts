import { Plugin } from "@opencode/plugin";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

// The rules are NOT duplicated here. AI-ENFORCEMENT.md is the single source of
// truth; this plugin reads it on every load so edits there reach every model.
const RULES_FILE = "AI-ENFORCEMENT.md";

function stripFrontmatter(text: string): string {
  return text.startsWith("---\n") ? text.replace(/^---\n[\s\S]*?\n---\n/, "") : text;
}

async function loadRules(ctx: any): Promise<string> {
  const root = ctx.location?.project?.canonical || ctx.location?.directory || process.cwd();
  try {
    const text = await readFile(join(root, RULES_FILE), "utf8");
    return `LINUX DEFENDER — MANDATORY RULES (source: ${RULES_FILE}):\n${stripFrontmatter(text)}`;
  } catch (error) {
    return `LINUX DEFENDER ENFORCEMENT ERROR: could not read ${RULES_FILE} from ${root}. Run bash scripts/check-all.sh before declaring anything done.\n${String(error)}`;
  }
}

export default Plugin.define({
  id: "linux-defender-enforcement",
  async setup(ctx) {
    const rules = await loadRules(ctx);
    await ctx.session.hook("context", (_event) => {
      event_system_push(_event, rules);
    });
  },
});

// Kept as a separate helper so the hook body stays tiny and the injected text
// comes from exactly one place (the file read above).
function event_system_push(event: any, text: string): void {
  event.system.push({ type: "text", text });
}
