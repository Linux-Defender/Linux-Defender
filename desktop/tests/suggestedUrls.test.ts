import { describe, expect, test } from "bun:test";
import { ensureProviderUrls, isUrlhausFeed, visibleCustomUrls } from "../src/suggestedUrls";

const urlhaus = "https://urlhaus-api.abuse.ch/v2/files/exports/key/urlhaus_clamav.ndb";

describe("Provider URL draft", () => {
  test("adds all providers once and de-duplicates", () => {
    const first = ensureProviderUrls([], urlhaus);
    expect(first.changed).toBe(true);
    expect(first.values).toHaveLength(6);
    const second = ensureProviderUrls([...first.values, urlhaus], urlhaus);
    expect(second.changed).toBe(false);
    expect(second.values).toEqual(first.values);
  });

  test("preserves user URLs and never duplicates them", () => {
    const custom = "https://example.invalid/custom.ndb";
    const result = ensureProviderUrls([custom, custom, urlhaus], urlhaus);
    expect(result.values.filter((url) => url === custom)).toHaveLength(1);
    expect(result.values.filter((url) => url === urlhaus)).toHaveLength(1);
  });

  test("nothing provider-related is visible by default; Suggested reveals", () => {
    const stored = ensureProviderUrls([], urlhaus).values;
    expect(visibleCustomUrls(stored, false)).toEqual([]);
    expect(visibleCustomUrls(stored, true)).toEqual(stored);
  });

  test("URLhaus feed is recognised", () => {
    expect(isUrlhausFeed(urlhaus)).toBe(true);
    expect(isUrlhausFeed("https://example.invalid/x.ndb")).toBe(false);
  });
});
