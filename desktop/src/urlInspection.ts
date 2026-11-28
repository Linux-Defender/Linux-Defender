/** Pure helpers for combined website URL inspection. No network or side effects. */
export type UrlProvider = "urlscan" | "virustotal";
export type InspectionMode = UrlProvider | "both";

export type UrlscanSubmission = {
  uuid: string;
  url: string;
  visibility: "private" | "unlisted" | "public";
  result_url: string;
};
export type VirusTotalSubmission = {
  status: "clean" | "detected" | "pending" | "rate_limited" | "error";
  url: string;
  analysis_id?: string;
  detections: number;
  total_engines: number;
  analysis_url?: string;
  error_message?: string;
};

export type CombinedVerdict = "clean" | "detected" | "pending" | "partial" | "unavailable";

/** Services that can actually be used in the current mode. */
export function activeProviders(mode: InspectionMode): UrlProvider[] {
  return mode === "both" ? ["urlscan", "virustotal"] : [mode];
}

/**
 * Merge two independent reputation results conservatively: any detection
 * wins; otherwise a still-running analysis is not a clean verdict; if only
 * one service answered, the result is partial, never presented as complete.
 */
export function combinedVerdict(
  urlscan: UrlscanSubmission | null,
  virustotal: VirusTotalSubmission | null,
  providers: readonly UrlProvider[],
): CombinedVerdict {
  if (providers.length === 0) return "unavailable";
  let answered = 0;
  if (providers.includes("urlscan") && urlscan) answered += 1;
  if (providers.includes("virustotal") && virustotal) answered += 1;
  if (answered === 0) return "unavailable";

  if (virustotal && providers.includes("virustotal")) {
    if (virustotal.status === "detected") return "detected";
    if (virustotal.status === "pending") return "pending";
  }
  if (answered < providers.length) return "partial";
  return "clean";
}

export function combinedSummary(
  verdict: CombinedVerdict,
  detections: number,
  total: number,
): string {
  switch (verdict) {
    case "detected":
      return detections > 0
        ? `${detections} of ${total} VirusTotal URL engines reported suspicious or malicious; review both reports.`
        : "A service reported a suspicious result; review both reports.";
    case "pending":
      return "One analysis is still processing; this is not a clean verdict yet.";
    case "partial":
      return "Only one service answered; the URL was not checked by both.";
    case "unavailable":
      return "No URL inspection service was available.";
    default:
      return "Both services reported no detections for this URL.";
  }
}
