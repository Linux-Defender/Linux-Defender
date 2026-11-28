import { describe, expect, test } from "bun:test";
import { readFileSync } from "node:fs";

const script = readFileSync(new URL("../public/boot-diagnostics.js", import.meta.url), "utf8");

describe("boot diagnostics", () => {
  test("is branding-correct and network-free", () => {
    expect(script).toContain("Linux Defender could not start");
    expect(script).toContain("linux-defender.log");
    expect(script).not.toMatch(/fetch\(|XMLHttpRequest|sendBeacon/);
  });
  test("only writes untrusted text via textContent", () => {
    expect(script).toContain("textContent");
    expect(script).not.toContain("innerHTML");
  });
  test("does not mistake a pre-body error for a successful mount", () => {
    expect(script).toContain("sawPlaceholder");
    expect(script).toContain("pendingFailure");
    expect(script).toContain("flush()");
    expect(script).toContain("debugLogPath()");
  });
});
