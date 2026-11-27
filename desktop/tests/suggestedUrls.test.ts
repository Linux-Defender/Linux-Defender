import { describe, expect, test } from "bun:test";
import { isUrlhausFeed, visibleCustomUrls } from "../src/suggestedUrls";

const urlhaus = "https://urlhaus-api.abuse.ch/v2/files/exports/key/urlhaus_clamav.ndb";
const custom = "https://example.invalid/custom.ndb";
const stored = [
  urlhaus,
  "https://www.rfxn.com/downloads/rfxn.hdb",
  "https://www.rfxn.com/downloads/rfxn.ndb",
  "https://sigs.interserver.net/interserver256.hdb",
  "https://sigs.interserver.net/interservertopline.db",
  "https://sigs.interserver.net/shell.ldb",
  custom,
];

describe("Suggested signature URL visibility", () => {
  test("provider rows are hidden by default, custom URLs remain", () => {
    expect(visibleCustomUrls(stored, false)).toEqual([custom]);
  });

  test("Suggested reveals every row without changing the stored list", () => {
    expect(visibleCustomUrls(stored, true)).toEqual(stored);
    expect(stored).toHaveLength(7);
  });

  test("URLhaus feed is recognised and kept", () => {
    expect(isUrlhausFeed(urlhaus)).toBe(true);
    expect(isUrlhausFeed(custom)).toBe(false);
    expect(stored).toContain(urlhaus);
  });
});
