/** Pure helpers for the Suggested control.
 *
 * Behavior (from the user's clarification and upstream ClamUI parity):
 *  - The URLhaus feed is always added to the draft config by default.
 *  - First Suggested click adds the five provider URLs to the draft config
 *    and reveals every provider row.
 *  - Second click only hides the rows; it never removes data.
 *  - Each visible row keeps its own Remove button.
 */
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

export function visibleCustomUrls(values: readonly string[], showSuggested: boolean): string[] {
  return showSuggested ? [...values] : values.filter((url) => !isProviderUrl(url));
}
