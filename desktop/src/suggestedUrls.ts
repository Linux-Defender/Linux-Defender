/** All provider feeds (URLhaus included) are added to the draft config by
 * default. Suggested only reveals or hides their rows; it never removes data. */
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

export function addSuggestedUrls(current: readonly string[]): string[] {
  const merged = [...current];
  for (const url of SUGGESTED_SIGNATURE_URLS) {
    if (!merged.includes(url)) merged.push(url);
  }
  return merged;
}

/** Nothing provider-related is visible by default; Suggested reveals all. */
export function visibleCustomUrls(values: readonly string[], showSuggested: boolean): string[] {
  return showSuggested ? [...values] : values.filter((url) => !isProviderUrl(url));
}
