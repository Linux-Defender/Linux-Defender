/** Suggested YARA documentation sources. Suggestion-only: nothing is
 * downloaded, applied, or added to a scan. The user reviews every rule and
 * keeps the folder under their own control. */
export const SUGGESTED_YARA_SOURCES = [
  {
    label: "ClamAV signature formats",
    url: "https://docs.clamav.net/manual/Signatures.html",
  },
  {
    label: "ClamAV YARA support notes",
    url: "https://docs.clamav.net/manual/Signatures/YaraRules.html",
  },
  {
    label: "YARA documentation",
    url: "https://yara.readthedocs.io/en/stable/",
  },
] as const;

export function isSuggestedYaraUrl(url: string): boolean {
  return (SUGGESTED_YARA_SOURCES as readonly { url: string }[]).some(
    (source) => source.url === url,
  );
}
