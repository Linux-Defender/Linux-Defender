/** Provider rows stay in the configuration (URLhaus feed included) so signature
 * updates keep working. The Suggested control only hides or reveals those rows
 * in the draft UI. Pure helpers keep that rule regression-tested. */
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

export function isSuggestedUrl(url: string): boolean {
  return isUrlhausFeed(url)
    || (SUGGESTED_SIGNATURE_URLS as readonly string[]).includes(url);
}

/** Hidden by default; Suggested reveals all provider rows without changing
 * any stored configuration value. */
export function visibleCustomUrls(values: readonly string[], showSuggested: boolean): string[] {
  return showSuggested ? [...values] : values.filter((url) => !isSuggestedUrl(url));
}
