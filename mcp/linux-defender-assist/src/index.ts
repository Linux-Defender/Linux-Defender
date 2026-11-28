import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readFile } from "node:fs/promises";
import * as z from "zod/v4";

const runFile = promisify(execFile);
const ROOT = resolve(fileURLToPath(new URL(".", import.meta.url)), "../../..");
const READ = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false } as const;
const LOCAL = { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false } as const;

async function command(file: string, args: string[] = []): Promise<{ code: number; out: string; err: string }> {
  try {
    const { stdout, stderr } = await runFile(file, args, { cwd: ROOT, maxBuffer: 4 * 1024 * 1024 });
    return { code: 0, out: stdout, err: stderr };
  } catch (error) {
    const failure = error as { code?: number; stdout?: string; stderr?: string; message?: string };
    return {
      code: failure.code ?? 1,
      out: failure.stdout ?? "",
      err: failure.stderr ?? failure.message ?? "command failed",
    };
  }
}

async function readRepoFile(rel: string): Promise<string> {
  try {
    return await readFile(resolve(ROOT, rel), "utf8");
  } catch {
    return "";
  }
}

function text(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

const server = new McpServer({ name: "linux-defender-assist", version: "0.6.0" });

server.registerTool(
  "ld_repo_status",
  {
    title: "Linux Defender repository status",
    description: "Read-only HEAD, sync, and working-tree state for the Linux Defender checkout.",
    inputSchema: z.object({}),
    annotations: READ,
  },
  async () => {
    const head = await command("git", ["rev-parse", "HEAD"]);
    const origin = await command("git", ["rev-parse", "origin/main"]);
    const status = await command("git", ["status", "--short"]);
    const result = {
      head: head.out.trim(),
      origin: origin.out.trim(),
      synced: head.out.trim() === origin.out.trim(),
      clean: status.out.trim().length === 0,
      changed: status.out.trim().split("\n").filter(Boolean).slice(0, 30),
    };
    return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
  },
);

server.registerTool(
  "ld_translation_candidates",
  {
    title: "Translation review candidates",
    description: "List long English strings still identical in a non-English catalog, from the generated review report.",
    inputSchema: z.object({
      locale: z.enum(["de", "es", "fr", "hu", "it", "nb", "pt_BR", "vi", "zh_CN"]),
    }),
    annotations: READ,
  },
  async ({ locale }) => {
    const report = await readRepoFile("po/TRANSLATION-REVIEW.md");
    const section = report.split(`## ${locale}\n`)[1]?.split("\n## ")[0] ?? "";
    const candidates = section.split("\n").filter((line) => line.startsWith("- `")).map((line) =>
      line.replace(/^- `/, "").replace(/`$/s, ""),
    );
    const result = { locale, candidates };
    return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
  },
);

server.registerTool(
  "ld_translation_suggest",
  {
    title: "Suggest a translation (never writes catalogs)",
    description: "Ask a locally running LM Studio model for a translation suggestion. Returns a proposal only; a human must apply it.",
    inputSchema: z.object({
      locale: z.enum(["de", "es", "fr", "hu", "it", "nb", "pt_BR", "vi", "zh_CN"]),
      msgid: z.string().min(1).max(2000),
    }),
    annotations: { ...READ, openWorldHint: false },
  },
  async ({ locale, msgid }) => {
    const names: Record<string, string> = {
      de: "German", es: "Spanish", fr: "French", hu: "Hungarian", it: "Italian",
      nb: "Norwegian Bokmål", pt_BR: "Brazilian Portuguese", vi: "Vietnamese", zh_CN: "Simplified Chinese",
    };
    try {
      // Fixed loopback endpoint: a caller must never be able to submit text to an arbitrary host.
      const response = await fetch("http://127.0.0.1:1234/v1/chat/completions", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          messages: [
            { role: "system", content: `Translate short desktop UI strings into ${names[locale]}. Preserve placeholders like {path} and {error}. Return only the translation.` },
            { role: "user", content: msgid },
          ],
          temperature: 0.2,
          max_tokens: 256,
        }),
        signal: AbortSignal.timeout(20_000),
      });
      if (!response.ok) throw new Error(`local model returned HTTP ${response.status}`);
      const body = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
      const suggestion = body.choices?.[0]?.message?.content?.trim() ?? "";
      const result = { locale, msgid, suggestion, applied: false, note: "Proposal only. Review and apply with scripts/merge-catalogs.py." };
      return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
    } catch (error) {
      const result = { locale, msgid, suggestion: null, applied: false, error: String(error) };
      return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
    }
  },
);

server.registerTool(
  "ld_desktop_capture",
  {
    title: "Capture the desktop app window",
    description: "Focus the Linux Defender window and capture a PNG using the repository capture helper.",
    inputSchema: z.object({
      output: z.string().regex(/^\/tmp\/opencode\/[A-Za-z0-9._-]+\.png$/, "must be a PNG directly under /tmp/opencode/").optional(),
    }),
    annotations: LOCAL,
  },
  async ({ output }) => {
    const path = output ?? "/tmp/opencode/mcp-linux-defender.png";
    const result = await command("bash", ["scripts/capture-app-window.sh", path]);
    return {
      content: [{ type: "text" as const, text: result.code === 0 ? `CAPTURED ${path}` : result.err }],
      structuredContent: { path, ok: result.code === 0, detail: result.err.trim() },
    };
  },
);

server.registerTool(
  "ld_tray_probe",
  {
    title: "Probe Sway/waybar tray readiness",
    description: "Read-only check for sway, waybar, grim, and a running Linux Defender process.",
    inputSchema: z.object({}),
    annotations: READ,
  },
  async () => {
    const checks: Record<string, boolean> = {};
    for (const tool of ["sway", "waybar", "grim"]) {
      checks[tool] = (await command("sh", ["-c", `command -v ${tool}`])).code === 0;
    }
    checks["linux-defender-running"] = (await command("pgrep", ["-x", "linux-defender"])).code === 0;
    checks["sni-implementation"] = (await readRepoFile("desktop/src-tauri/src/tray.rs")).includes("ksni");
    return {
      content: [{ type: "text" as const, text: text(checks) }],
      structuredContent: checks,
    };
  },
);

server.registerTool(
  "ld_helper_probe",
  {
    title: "Probe privileged helper trust state",
    description: "Read-only check of the canonical helper path, PolicyKit policy, and root-owned executable bit. Never invokes pkexec.",
    inputSchema: z.object({}),
    annotations: READ,
  },
  async () => {
    const helper = "/usr/bin/linux-defender-apply-preferences";
    const policy = "/usr/share/polkit-1/actions/io.github.linuxdefender.linuxdefender.policy";
    const stat = await command("stat", ["-c", "%u %a %F", helper]);
    const fields = stat.out.trim().split(/\s+/);
    const result = {
      helper,
      policy,
      helper_exists: stat.code === 0,
      root_owned: fields[0] === "0",
      executable: Boolean(fields[1] && parseInt(fields[1], 8) & 0o111),
      policy_exists: (await command("test", ["-f", policy])).code === 0,
      note: "Authorization itself requires an interactive pkexec session performed by a human.",
    };
    return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
  },
);

server.registerTool(
  "ld_online_preflight",
  {
    title: "Online service preflight (no submission)",
    description: "Check whether a VirusTotal or urlscan key exists in the OS keyring without revealing it, and show what a submission would disclose.",
    inputSchema: z.object({
      service: z.enum(["virustotal", "urlscan"]),
      target: z.string().min(1).max(2000).describe("File hash, URL, or path that would be submitted."),
    }),
    annotations: READ,
  },
  async ({ service, target }) => {
    const username = service === "virustotal" ? "virustotal_api_key" : "urlscan_api_key";
    const [canonical, legacy] = await Promise.all([
      command("secret-tool", ["search", "--all", "service", "linux-defender", "username", username]),
      command("secret-tool", ["search", "--all", "service", "clamui", "username", username]),
    ]);
    const lookup = { out: `${canonical.out}
${legacy.out}` };
    const result = {
      service,
      target,
      key_present: lookup.out.trim().length > 0,
      submission_performed: false,
      disclosure: service === "virustotal"
        ? "A hash lookup shares the hash; a file upload shares file contents."
        : "A URL submission shares the full URL including query string.",
      note: "Use the app UI for the explicit confirmation and real request.",
    };
    return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
  },
);

server.registerTool(
  "ld_support_parity",
  {
    title: "Cross-layer support parity",
    description: "Read-only report from scripts/check-support-parity.py: verifies that behavioral support remains symmetric across VirusTotal, urlscan, urlhaus, frontend validators, scheduler, quarantine, capabilities, and untrusted-input sanitization.",
    inputSchema: z.object({}),
    annotations: READ,
  },
  async () => {
    const check = await command("python3", ["scripts/check-support-parity.py"]);
    const result = {
      ok: check.code === 0,
      output: `${check.out}\n${check.err}`.trim(),
      note: "The same check runs in check-all.sh, pre-commit, and CI; a non-zero result means a layer was left behind by a partial fix.",
    };
    return { content: [{ type: "text" as const, text: text(result) }], structuredContent: result };
  },
);

server.registerTool(
  "ld_deep_audit",
  {
    title: "Deep audit (static, read-only)",
    description: "Run scripts/deep-audit.sh --quick: generated-artifact checks, all static gates, parity/signature/image guards, and the agent-fleet brief. Reports only; never edits, commits, or pushes.",
    inputSchema: z.object({}),
    annotations: READ,
  },
  async () => {
    const audit = await command("bash", ["scripts/deep-audit.sh", "--quick"]);
    const output = `${audit.out}\n${audit.err}`.trim();
    const report = "/tmp/opencode/linux-defender-deep-audit.md";
    return {
      content: [{ type: "text" as const, text: output.slice(0, 12000) }],
      structuredContent: { ok: audit.code === 0, output: output.slice(0, 12000), report },
    };
  },
);

async function main(): Promise<void> {
  await server.connect(new StdioServerTransport());
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
