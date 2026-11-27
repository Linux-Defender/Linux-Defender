import { describe, expect, test } from "bun:test";
import { addSuggestedUrls, isUrlhausFeed, visibleCustomUrls } from "../src/suggestedUrls";

const urlhaus = "https://urlhaus-api.abuse.ch/v2/files/exports/key/urlhaus_clamav.ndb";
const custom = "https://example.invalid/custom.ndb";
const stored = addSuggestedUrls([urlhaus, custom]);

describe("Suggested row visibility", () => {
  test("all provider feeds are stored by default", () => {
    expect(stored).toHaveLength(7);
    expect(stored).toContain(urlhaus);
  });
  test("nothing provider-related is visible by default", () => {
    expect(visibleCustomUrls(stored, false)).toEqual([custom]);
  });
  test("Suggested reveals all rows without changing data", () => {
    expect(visibleCustomUrls(stored, true)).toEqual(stored);
    expect(stored).toHaveLength(7);
  });
  test("URLhaus feed is recognised", () => {
    expect(isUrlhausFeed(urlhaus)).toBe(true);
    expect(isUrlhausFeed(custom)).toBe(false);
  });
});
