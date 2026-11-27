import { describe, expect, test } from "bun:test";
import { addSuggestedUrls, isUrlhausFeed, visibleCustomUrls } from "../src/suggestedUrls";

const urlhaus = "https://urlhaus-api.abuse.ch/v2/files/exports/key/urlhaus_clamav.ndb";
const custom = "https://example.invalid/custom.ndb";

describe("Suggested signature URLs", () => {
  test("default: only user URLs are visible", () => {
    const stored = [urlhaus, custom];
    expect(visibleCustomUrls(stored, false)).toEqual([custom]);
  });

  test("first click adds five providers and reveals everything", () => {
    const stored = [urlhaus, custom];
    const added = addSuggestedUrls(stored);
    expect(added).toHaveLength(7);
    expect(visibleCustomUrls(added, true)).toEqual(added);
  });

  test("second click hides rows but never removes data", () => {
    const added = addSuggestedUrls([urlhaus, custom]);
    expect(visibleCustomUrls(added, false)).toEqual([custom]);
    expect(added).toHaveLength(7);
    expect(added).toContain(urlhaus);
  });

  test("URLhaus feed is recognised", () => {
    expect(isUrlhausFeed(urlhaus)).toBe(true);
    expect(isUrlhausFeed(custom)).toBe(false);
  });
});
