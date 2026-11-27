import { describe, expect, test } from "bun:test";
import { createResultStore, trimmedForStorage, STORED_OUTPUT_LIMIT } from "../src/resultStore";

function fakeStorage(limit = 128) {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      if (value.length > limit) throw new Error("quota");
      data.set(key, value);
    },
    removeItem: (key: string) => { data.delete(key); },
  };
}

const isResult = (value: unknown): value is { stdout: string } =>
  typeof value === "object" && value !== null && typeof (value as { stdout?: unknown }).stdout === "string";

describe("result store", () => {
  test("memory stays complete when storage rejects the full result", () => {
    const storage = fakeStorage();
    const store = createResultStore(() => storage);
    const result = { stdout: "x".repeat(STORED_OUTPUT_LIMIT + 10) };
    store.remember("scan", result);
    expect(store.recall("scan", isResult)).toEqual(result);
  });

  test("trims raw output for the persisted copy", () => {
    const trimmed = trimmedForStorage({ stdout: "y".repeat(1000) }, 100) as { stdout: string };
    expect(trimmed.stdout.length).toBeLessThan(200);
    expect(trimmed.stdout).toContain("output truncated");
  });

  test("falls back to trimmed storage when memory is empty", () => {
    const storage = fakeStorage(4096);
    createResultStore(() => storage).remember("virustotal", { stdout: "ok" });
    expect(createResultStore(() => storage).recall("virustotal", isResult)).toEqual({ stdout: "ok" });
  });
});
