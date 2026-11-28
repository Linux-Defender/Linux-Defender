import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";

const overview = readFileSync(new URL("../src/pages/Overview.tsx", import.meta.url), "utf8");

const EXPECTED_ORDER = [
  "Quick Scan",
  "System Security Check",
  "Update Database",
  "View Scan Logs",
  "Quarantine",
];

describe("Overview quick actions", () => {
  test("are ordered scan-first, then security check, then maintenance", () => {
    const section = overview.split('<div className="quick-actions">')[1]?.split("</div>")[0] ?? "";
    const found = EXPECTED_ORDER.map((label) => ({ label, at: section.indexOf(`{_("${label}")}`) }));
    expect(found.every((item) => item.at >= 0)).toBe(true);
    const positions = found.map((item) => item.at);
    expect([...positions].sort((a, b) => a - b)).toEqual(positions);
  });

  test("keep every action on the audit page reachable from the quick actions", () => {
    expect(overview).toContain('navigate("audit")');
    expect(overview).toContain('navigate("database")');
    expect(overview).toContain('navigate("logs")');
    expect(overview).toContain('navigate("quarantine")');
    expect(overview).toContain('navigate("scan", { quickScan: true })');
  });
});
