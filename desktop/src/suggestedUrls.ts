/** Suggested signature URL toggle. Pure so it can be unit-tested without
 * importing the heavy preferences page (whose dependencies are mocked in
 * other tests). */
export const SUGGESTED_SIGNATURE_URLS = [
  "https://www.rfxn.com/downloads/rfxn.hdb",
  "https://www.rfxn.com/downloads/rfxn.ndb",
  "https://sigs.interserver.net/interserver256.hdb",
  "https://sigs.interserver.net/interservertopline.db",
  "https://sigs.interserver.net/shell.ldb",
] as const;

/** First click shows all five, the next removes them; user URLs survive. */
export function toggleSuggestedUrls(current: readonly string[]): string[] {
  if (SUGGESTED_SIGNATURE_URLS.every((url) => current.includes(url))) {
    return current.filter((url) => !SUGGESTED_SIGNATURE_URLS.includes(url as (typeof SUGGESTED_SIGNATURE_URLS)[number]));
  }
  const merged = [...current];
  for (const url of SUGGESTED_SIGNATURE_URLS) {
    if (!merged.includes(url)) merged.push(url);
  }
  return merged;
}
