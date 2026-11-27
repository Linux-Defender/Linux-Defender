import { describe, expect, test } from "bun:test";
import { toggleSuggestedUrls } from "../src/suggestedUrls";

describe("Suggested signature URLs", () => {
  test("default draft is empty", () => {
    expect(toggleSuggestedUrls([])).toHaveLength(5);
  });

  test("first click shows all five, second click removes all five", () => {
    const shown = toggleSuggestedUrls([]);
    expect(shown).toHaveLength(5);
    expect(toggleSuggestedUrls(shown)).toEqual([]);
  });

  test("toggle never removes user-added URLs", () => {
    const custom = "https://example.invalid/custom.ndb";
    const shown = toggleSuggestedUrls([custom]);
    expect(shown).toHaveLength(6);
    expect(toggleSuggestedUrls(shown)).toEqual([custom]);
  });
});
