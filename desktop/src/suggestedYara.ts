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

/** Vetted example rules, shipped as .yar.example and never auto-loaded.
 * Keep in sync with assets/yara/linux-defender-examples.yar.example. */
export const YARA_EXAMPLE_RULES = "// Linux Defender example YARA rules (MIT). NOT enabled by default.\n// Verified against ClamAV 1.5.4's YARA subset: plain string rules only.\n// Copy into your YARA Rules folder as .yar after reviewing each rule.\nrule LinuxDefender_Example_EICAR_Test {\n    strings:\n        $eicar = \"EICAR-STANDARD-ANTIVIRUS-TEST-FILE\"\n    condition:\n        $eicar\n}\n\nrule LinuxDefender_Example_Inert_Template {\n    strings:\n        $template = \"REPLACE_WITH_A_REVIEWED_STRING\"\n    condition:\n        $template\n}\n";
