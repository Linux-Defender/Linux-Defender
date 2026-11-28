import { describe, expect, test } from "bun:test";
import { isSuggestedYaraUrl, SUGGESTED_YARA_SOURCES } from "../src/suggestedYara";

describe("suggested YARA sources", () => {
  test("are documentation links only", () => {
    expect(SUGGESTED_YARA_SOURCES.length).toBeGreaterThan(0);
    for (const source of SUGGESTED_YARA_SOURCES) {
      expect(source.url.startsWith("https://")).toBe(true);
      expect(isSuggestedYaraUrl(source.url)).toBe(true);
    }
  });

  test("do not treat arbitrary feeds as suggested", () => {
    expect(isSuggestedYaraUrl("https://example.org/rules.yar")).toBe(false);
    expect(isSuggestedYaraUrl("")).toBe(false);
  });
});
