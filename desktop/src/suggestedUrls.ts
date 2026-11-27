/** Provider feeds are added to the draft once, idempotently. Suggested only
 * reveals or hides their rows; it never changes data. Pure helpers make the
 * no-duplicate / no-repeated-toast rules regression-tested. */
export const SUGGESTED_SIGNATURE_URLS = [
  "https://www.rfxn.com/downloads/rfxn.hdb",
  "https://www.rfxn.com/downloads/rfxn.ndb",
  "https://sigs.interserver.net/interserver256.hdb",
  "https://sigs.interserver.net/interservertopline.db",
  "https://sigs.interserver.net/shell.ldb",
] as const;

export function isUrlhausFeed(url: string): boolean {
  return url.startsWith("https://urlhaus-api.abuse.ch/v2/files/exports/")
    && url.endsWith("/urlhaus_clamav.ndb");
}

export function isProviderUrl(url: string): boolean {
  return isUrlhausFeed(url)
    || (SUGGESTED_SIGNATURE_URLS as readonly string[]).includes(url);
}

/** Ensure every provider is present exactly once. Returns changed=false when
 * nothing was added, so the UI never shows a redundant Save & Apply toast. */
export function ensureProviderUrls(
  current: readonly string[],
  urlhausUrl: string,
): { values: string[]; changed: boolean } {
  const values: string[] = [];
  for (const url of [...current, urlhausUrl, ...SUGGESTED_SIGNATURE_URLS]) {
    if (!values.includes(url)) values.push(url);
  }
  const normalized = [...new Set(current)];
  return {
    values,
    changed: normalized.length !== values.length
      || normalized.some((url, index) => url !== values[index]),
  };
}

/** Nothing provider-related is visible by default; Suggested reveals all. */
export function visibleCustomUrls(values: readonly string[], showSuggested: boolean): string[] {
  return showSuggested ? [...values] : values.filter((url) => !isProviderUrl(url));
}
